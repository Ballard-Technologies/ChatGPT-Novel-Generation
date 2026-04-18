import os
import re
import time
import requests
from datetime import datetime
from threading import Thread, Lock

import utilities.prompt_templates as pt
from features.progress_store import JobCancelled
from utilities.text_utilities import TextUtilities as tu

class StoryCreator:
    def __init__(self, progress, api_key, testing=False, prompt_overrides=None):
        self.progress = progress
        self.api_key = api_key
        self.testing = testing
        self.prompt_overrides = prompt_overrides or {}

        self.TESTING_CHAP_DELIM = "[CHAPTER_DELIM]"
        self._meta_text = ''
        self._meta_lock = Lock()

    def _append_meta(self, text):
        with self._meta_lock:
            self._meta_text += text

    def process_chapter(self, index, chap, prompt_vars, chatgpt_model, completed_chapters_list):
        try:
            self._append_meta(f'Rough Chapter:\n{chap}\n\n')
            detailed_chap = self.write_text(prompt_vars, chatgpt_model, 'create_chapter', chap=chap)

            self._append_meta(f'Detailed Chapter:\n{detailed_chap}\n\n')

            self.progress.inc_current()

            chapter_text = ''
            last_chapter_text = ''
            chapter_index = 0

            while '^^^' not in chapter_text:
                write_chapter_type = 'write_chapter' if chapter_index != 0 else 'write_first_chapter'
                if last_chapter_text != '':
                    first_half, last_chapter_text = tu.splitParagraphs(last_chapter_text)
                last_chapter_text = self.write_text(
                    prompt_vars, chatgpt_model, write_chapter_type,
                    det_chap=detailed_chap, prev_sec=last_chapter_text
                )
                chapter_text += last_chapter_text

                self._append_meta(f'Chapter Text {chapter_index}:\n{chapter_text}\n\n')

                self.progress.inc_current()

                chapter_index += 1

            chapter_text = tu.getChapterTextUntilMarker(chapter_text)
            completed_chapters_list[index] = chapter_text
        except JobCancelled:
            return

    def process_summary(self, title, summary, chatgpt_model):
        self.progress.start(total=100)

        prompt_vars = {
            'title': title,
            'user_summary': summary
        }

        if self.testing:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            example_novel_path = os.path.join('testing_data', f'example_novel_{timestamp}.txt')
            example_novel_metadata_path = os.path.join('testing_data', f'example_novel_metadata_{timestamp}.txt')
            if os.path.exists(example_novel_path):
                with open(example_novel_path, 'r') as f:
                    example_novel = f.read()

                chapter_list = example_novel.split(self.TESTING_CHAP_DELIM)
                chapter_list = [chap for chap in chapter_list if chap.strip()]

                self.progress.complete(chapters=chapter_list)
                return

        # Continue with generation if example novel is not found or not in testing mode
        create_summary_type = 'create_summary' if summary != '' else 'create_summary_from_scratch'

        prompt_vars['summary'] = self.write_text(prompt_vars, 'gpt-5.4', create_summary_type)
        self.progress.inc_current()

        prompt_vars['author'] = self.write_text(prompt_vars, 'gpt-5.4', 'create_author')
        self.progress.inc_current()

        prompt_vars['characters'] = self.write_text(prompt_vars, 'gpt-5.4', 'create_characters')
        self.progress.inc_current()

        prompt_vars['themes_and_conflicts'] = self.write_text(prompt_vars, 'gpt-5.4', 'create_themes_and_conflicts')
        self.progress.inc_current()

        retry_count = 0
        max_retries = 5
        chapter_list = []

        while retry_count < max_retries:
            chapters = self.write_text(prompt_vars, 'gpt-5.4', 'create_chapters')

            self._append_meta(f'Chapters:\n{chapters}\n\n')

            pattern = r'(?=Chapter \d+)'
            chapter_list = re.split(pattern, chapters)

            chapter_list = [chapter for chapter in chapter_list if 'chapter' in chapter.lower()]

            for i, c in enumerate(chapter_list):
                self._append_meta(f'Post Pattern Split Chapter {i}:\n{c}\n\n')

            chapter_list = [chap for chap in chapter_list if chap.strip()]

            if any("Chapter" in chap for chap in chapter_list):
                break
            else:
                if retry_count + 1 == max_retries:
                    self.progress.fail('Unable to create chapters.')
                    raise SystemExit
                else:
                    retry_count += 1
                    time.sleep(1)

        self.progress.set_total(self.progress.get_current() + (len(chapter_list) * 4) + 1)
        self.progress.inc_current()

        completed_chapters_list = [''] * len(chapter_list)
        threads = []

        for index, chap in enumerate(chapter_list):
            t = Thread(
                target=self.process_chapter,
                args=(index, chap, prompt_vars, chatgpt_model, completed_chapters_list)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.progress.check_cancel()

        self.progress.complete(chapters=completed_chapters_list)

        if self.testing:
            with open(example_novel_path, 'w') as f:
                f.write(self.TESTING_CHAP_DELIM.join(completed_chapters_list))
            with open(example_novel_metadata_path, 'w') as f:
                f.write(self._meta_text)

    def write_text(self, prompt_vars, chatgpt_model, prompt_type, chap=None, det_chap=None, prev_sec=None):
        self.progress.check_cancel()

        temp_prompt_vars = prompt_vars.copy()
        if chap:
            temp_prompt_vars['chapter'] = chap
        if det_chap:
            temp_prompt_vars['detailed_chapter'] = det_chap
        if prev_sec:
            temp_prompt_vars['previous_section'] = prev_sec

        template = pt.resolve_template('summary_template_v0020', self.prompt_overrides)
        instruction = template[prompt_type].format(**temp_prompt_vars)

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': 'Bearer ' + self.api_key,  # Added space after 'Bearer'
            'Content-Type': 'application/json'
        }
        data = {
            'model': chatgpt_model,
            'messages': [{'role': 'user', 'content': instruction}],
        }
        # The base GPT-5 reasoning family (gpt-5, gpt-5-mini, gpt-5-nano) rejects
        # the temperature parameter; GPT-5.x point releases and GPT-4.1 accept it.
        if chatgpt_model != 'gpt-5' and not chatgpt_model.startswith('gpt-5-'):
            data['temperature'] = 1.0

        try:
            response = requests.post(url, headers=headers, json=data).json()
            if 'choices' in response:
                return response['choices'][0]['message']['content'].replace('#', '').replace('*', '')
            else:
                raise Exception(f'Invalid response from ChatGPT. Response: {response}')
        except Exception as e:
            self.progress.fail(e)
            raise SystemExit(e)