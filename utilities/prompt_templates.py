outline_template_v0010 = [
    "Below is a segment from the outline of my story titled '{title}'. Based on this segment: {prompt}. Could you expand upon this by creating a numbered list (1-10) that outlines a series of events for this part of the story? Please ensure each event is detailed and contributes to the development of the plot or characters. Also, consider the logical progression of events and how they connect to the overall narrative. This list should help in further fleshing out the story's structure and guide the subsequent drafting process.",
    "Here is a section from the outline of my story titled {title}. Based on this outline: {prompt}. Please write this part of the story in a detailed narrative prose format, focusing on descriptive storytelling. Include descriptions of settings, characters' thoughts and dialogue, and actions, and ensure the story flows smoothly from one scene to the next. Avoid presenting the story as a script or an outline. Fill in the gaps as necessary to create a cohesive and engaging narrative.",
    "Below is a segment from the rough draft of my story titled '{title}'. {prompt}. Could you revise this to make the narrative more cohesive? Focus on improving the flow of events, enhancing character development, and ensuring that the transitions between scenes are smooth. Additionally, please look for any inconsistencies in the plot or character actions and address them. My goal is to have a seamless narrative that clearly conveys the story's progression and deepens the reader's engagement with the characters and their journey."
]

summary_template_v0001 = [
    "Here is a summary of the story '{title}':\n{summary}\nCan you flesh out this summary, filling in the gaps where necessary but staying true to every aspect of the original summary?",
    "Here is a summary of the story '{title}':\n{summary}\nCan you split this summary into 24 parts that logically flow together, filling in the gaps where necessary but staying true to every aspect of the original summary?",
    "Here is a summary of the story '{title}': \n{summary}\nHere are the 24 parts of the story: {parts}\nCan you write this specific part of the story in a detailed narrative prose format, focusing on 3rd person descriptive storytelling, also filling in the gaps where necessary but staying true to every aspect of the original summary?: {part}",
    "Can you make these two sections more cohesize?: \n{section1}\n{section2}"
]

summary_template_v0002 = [
    "Here is a summary of the story '{title}':\n{summary}\n I need you to expand it into a more detailed narrative. Please incorporate vivid descriptions of characters, settings, and key events. Introduce dialogue where appropriate to bring characters to life, and develop subplots that enrich the main storyline. Ensure each aspect of the summary is explored with depth, creating immersive scenes that engage the reader fully.",
    "Here is a summary of the story '{title}':\n{summary}\nDivide the story into 24 cohesive chapters, based on the summary provided. For each chapter, outline the primary focus, key events, character developments, and how it contributes to the overall arc of the story. Ensure each chapter opens and concludes in a manner that propels the story forward, maintaining narrative tension and thematic coherence throughout.",
    "Here is a summary of the story '{title}': \n{summary}\nHere are the 24 parts of the story: {parts}\nDevelop a detailed chapter based on the chapter summary below using third-person narrative. Incorporate sensory descriptions to paint vivid scenes, deepen character insights with internal monologues, and craft meaningful dialogue that reveals character dynamics and advances the plot. Ensure the chapter's events are seamlessly integrated with the story's overall themes and contribute significantly to character development and plot progression: {part}",
    "Enhance the cohesion between the following two sections: \n{section1}\n{section2}\nPlease intertwine these sections by adding transitional phrases, ensuring character motivations and story developments are consistent across both. Introduce reflections or events that logically connect the sections, smoothing any abrupt narrative jumps and aligning the tone and pacing."
]

summary_template_v0010 = {
    "create_summary": "Title: {title}\nSummary: {user_summary}\nPlease expand this into a more detailed narrative. Begin by focusing on the characters and their unique situations—ensure the central conflict is clear and rooted in emotional or moral stakes for the characters. Explore the decisions the characters make, showing how each choice affects the progression of the story, and reflect on how these decisions drive the plot. Include vivid descriptions of the characters, settings, and key events, but avoid predictable plot turns. Embrace realism by introducing natural consequences and surprise elements. Develop subplots that arise naturally from the characters' actions and add richness to the overall storyline, making sure to fully immerse the reader in each scene.",

    "create_summary_from_scratch": "Please create a detailed narrative based on this title: {title}\nStart by developing central characters and the situations they find themselves in, ensuring their core conflicts naturally drive the plot. Focus on what’s at stake for these characters emotionally or morally, making their dilemmas essential to their identity or world. Introduce subplots that enrich the main storyline by exploring character choices and responses, where each decision leads to the next stage of the narrative. Reflect the complexity of life in the plot structure—embracing unpredictability and avoiding a too-neat progression. Please incorporate vivid descriptions of characters, settings, and key events, creating immersive scenes that engage the reader fully.",

    "create_characters": "Title: {title}\nSummary: {summary}\nPlease create the characters for this story, focusing on the following aspects:\n1. Observation and realism: Use observations of real-life behavior to inform how the characters speak, act, and interact with others. Focus on creating characters that feel authentic and have natural traits.\n2. Character flaws: Make the characters imperfect with compelling quirks, contradictions, or flaws. Show how these imperfections influence their decisions and drive the story forward.\n3. Interiority: Develop each character’s inner life by exploring their motivations, fears, and desires. Let their internal struggles shape their external actions.\n4. Character growth: The characters should not be static. Show how they evolve or reveal new dimensions of themselves as the story progresses.\n5. Actions and dialogue: Reveal characters through their actions and dialogue, rather than exposition. Let their choices and words define who they are and how they relate to others.\n6. Psychological depth: Ensure that each character has a psychological complexity, showing thoughts and emotions that make them believable and engaging.",

    "create_themes_and_conflicts": "Title: {title}\nSummary: {summary}\nCharacters: {characters}\nPlease establish the themes and conflicts of this story, focusing on how the characters' internal and external conflicts evolve. Consider the moral dilemmas and emotional tensions they face, allowing themes to emerge naturally from their struggles. Introduce complications or reversals that create unpredictability while exploring any universal truths or human experiences that might arise from the narrative.",

    "create_chapters": "Title: {title}\nSummary: {summary}\nCharacters: {characters}\nThemes and Conflicts: {themes_and_conflicts}\nPlease divide the story into 24 cohesive chapters, based on the summary provided. For each chapter, outline the primary focus, key events, and character developments, ensuring the plot grows organically from the characters’ desires, decisions, and conflicts. Reflect on how their choices under pressure drive the narrative forward. Each chapter should feature moments of tension, evolving conflicts, and delayed resolutions, while still maintaining a sense of momentum. Use subplots and layering to deepen the main narrative and enrich character interactions. Ensure that chapters open with a sense of purpose and conclude with unresolved questions or emotional tension to keep the reader engaged across the story arc. Weave in subtle foreshadowing, recurring symbols, and details to build anticipation, leading to a satisfying, layered conclusion.",

    "create_chapter": "Title: {title}\nSummary: {summary}\nCharacters: {characters}\nThemes and Conflicts: {themes_and_conflicts}\nChapter: {chapter}\nPlease expand upon the provided chapter by fleshing out the significant events, character interactions, and key moments. Focus on adding depth to scenes through sensory descriptions (sight, sound, touch, smell, taste) and meaningful details that highlight the setting and characters' emotions. Include suggestions for how characters' actions and gestures reveal their inner thoughts and motivations, and describe how the dialogue could incorporate subtext to suggest underlying tensions or relationships. Ensure the pacing builds appropriately, with slow, reflective moments for key emotional or thematic developments, and faster pacing for moments of action or tension. Provide ideas for how the chapter can progress towards a strong, impactful ending that leaves some tension unresolved or builds anticipation for what comes next. Additionally, suggest ways to naturally reveal character development and explore broader themes through the plot events and character decisions.",

    "write_first_chapter": "Title: {title}\nSummary: {summary}\nCharacters: {characters}\nChapter: {detailed_chapter}\nPlease start writing this chapter. In your writing, please:\n- Craft sentences carefully, paying close attention to language that reflects the characters, settings, and themes.\n- Use sentence structures that create the desired impact, focusing on clarity, tension, or atmosphere as appropriate.\n- Employ free indirect style where suitable to blend third-person narration with characters' internal thoughts, providing deeper emotional insight.\n- Include telling details to bring scenes and characters to life, focusing on small but significant aspects.\n- Reveal characters through their actions and dialogue, allowing their personalities to emerge naturally.\n- Develop main characters as complex and evolving (round characters), while utilizing simpler (flat) characters where appropriate.\n- Create narrative tension by introducing conflicts or moral dilemmas, balancing plot progression with character development.\n- Control the pacing of the story, knowing when to slow down for detail or speed up to build tension.\n- Be concise and cut unnecessary words to keep the narrative tight and focused.\n- Allow themes to emerge organically from the plot and characters, exploring fundamental human experiences or questions.",

    "write_chapter": "Title: {title}\nSummary: {summary}\nCharacters: {characters}\nChapter: {detailed_chapter}\nPlease continue writing this story until the natural end of the chapter. In your writing, please:\n- Craft sentences carefully, paying close attention to language that reflects the characters, settings, and themes.\n- Use sentence structures that create the desired impact, focusing on clarity, tension, or atmosphere as appropriate.\n- Employ free indirect style where suitable to blend third-person narration with characters' internal thoughts, providing deeper emotional insight.\n- Include telling details to bring scenes and characters to life, focusing on small but significant aspects.\n- Reveal characters through their actions and dialogue, allowing their personalities to emerge naturally.\n- Develop main characters as complex and evolving (round characters), while utilizing simpler (flat) characters where appropriate.\n- Create narrative tension by introducing conflicts or moral dilemmas, balancing plot progression with character development.\n- Control the pacing of the story, knowing when to slow down for detail or speed up to build tension.\n- Be concise and cut unnecessary words to keep the narrative tight and focused.\n- Allow themes to emerge organically from the plot and characters, exploring fundamental human experiences or questions.\nWhen the end of the chapter is reached, please write the special characters ^^^.\nPrevious section: {previous_section}"
}

summary_template_v0020 = {
    "create_summary": "Title: {title}\nSummary: {user_summary}\nPlease expand this into a more detailed narrative. Begin by focusing on the characters and their unique situations—ensure the central conflict is clear and rooted in emotional or moral stakes for the characters. Explore the decisions the characters make, showing how each choice affects the progression of the story, and reflect on how these decisions drive the plot. Include vivid descriptions of the characters, settings, and key events, but avoid predictable plot turns. Embrace realism by introducing natural consequences and surprise elements. Develop subplots that arise naturally from the characters' actions and add richness to the overall storyline, making sure to fully immerse the reader in each scene.",

    "create_summary_from_scratch": "Please create a detailed narrative based on this title: {title}\nStart by developing central characters and the situations they find themselves in, ensuring their core conflicts naturally drive the plot. Focus on what’s at stake for these characters emotionally or morally, making their dilemmas essential to their identity or world. Introduce subplots that enrich the main storyline by exploring character choices and responses, where each decision leads to the next stage of the narrative. Reflect the complexity of life in the plot structure—embracing unpredictability and avoiding a too-neat progression. Please incorporate vivid descriptions of characters, settings, and key events, creating immersive scenes that engage the reader fully.",

    "create_author": "Title: {title}\nSummary: {summary}\nPlease develop the author's profile for this story, focusing on the following aspects:\n1. Author's Personality: Describe the author's personality traits, passions, and worldview. Explain how these characteristics influence their writing style and narrative choices.\n2. Motivation for Writing the Novel: Discuss why the author is writing this novel. What personal experiences, beliefs, or messages are they aiming to convey? How do their motivations shape the themes and direction of the story?\n3. Writing Style and Subtleties: Elaborate on the author's unique style, including their use of language, subtleties, word choices, and narrative patterns. Consider how their background and perspective influence these elements. Ensure that the author's personality and motivations are deeply connected to the story's content, and that these elements are reflected in the way the story unfolds.",

    "create_characters": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nPlease create the characters for this story, focusing on the following aspects:\n1. Observation and realism: Use observations of real-life behavior to inform how the characters speak, act, and interact with others. Focus on creating characters that feel authentic and have natural traits.\n2. Character flaws: Make the characters imperfect with compelling quirks, contradictions, or flaws. Show how these imperfections influence their decisions and drive the story forward.\n3. Interiority: Develop each character’s inner life by exploring their motivations, fears, and desires. Let their internal struggles shape their external actions.\n4. Character growth: The characters should not be static. Show how they evolve or reveal new dimensions of themselves as the story progresses.\n5. Actions and dialogue: Reveal characters through their actions and dialogue, rather than exposition. Let their choices and words define who they are and how they relate to others.\n6. Psychological depth: Ensure that each character has a psychological complexity, showing thoughts and emotions that make them believable and engaging.",

    "create_themes_and_conflicts": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nCharacters: {characters}\nPlease establish the themes and conflicts of this story, focusing on how the characters' internal and external conflicts evolve. Consider the moral dilemmas and emotional tensions they face, allowing themes to emerge naturally from their struggles. Introduce complications or reversals that create unpredictability while exploring any universal truths or human experiences that might arise from the narrative.",

    "create_chapters": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nCharacters: {characters}\nThemes and Conflicts: {themes_and_conflicts}\nPlease divide the story into 24 cohesive chapters, based on the summary provided. For each chapter, outline the primary focus, key events, and character developments, ensuring the plot grows organically from the characters’ desires, decisions, and conflicts. Reflect on how their choices under pressure drive the narrative forward. Each chapter should feature moments of tension, evolving conflicts, and delayed resolutions, while still maintaining a sense of momentum. Use subplots and layering to deepen the main narrative and enrich character interactions. Ensure that chapters open with a sense of purpose and conclude with unresolved questions or emotional tension to keep the reader engaged across the story arc. Weave in subtle foreshadowing, recurring symbols, and details to build anticipation, leading to a satisfying, layered conclusion.",

    "create_chapter": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nCharacters: {characters}\nThemes and Conflicts: {themes_and_conflicts}\nChapter: {chapter}\nPlease expand upon the provided chapter by fleshing out the significant events, character interactions, and key moments. Focus on adding depth to scenes through sensory descriptions (sight, sound, touch, smell, taste) and meaningful details that highlight the setting and characters' emotions. Include suggestions for how characters' actions and gestures reveal their inner thoughts and motivations, and describe how the dialogue could incorporate subtext to suggest underlying tensions or relationships. Ensure the pacing builds appropriately, with slow, reflective moments for key emotional or thematic developments, and faster pacing for moments of action or tension. Provide ideas for how the chapter can progress towards a strong, impactful ending that leaves some tension unresolved or builds anticipation for what comes next. Additionally, suggest ways to naturally reveal character development and explore broader themes through the plot events and character decisions.",

    "write_first_chapter": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nCharacters: {characters}\nChapter: {detailed_chapter}\nPlease start writing this chapter. In your writing, please:\n- Craft sentences carefully, paying close attention to language that reflects the characters, settings, and themes.\n- Use sentence structures that create the desired impact, focusing on clarity, tension, or atmosphere as appropriate.\n- Employ free indirect style where suitable to blend third-person narration with characters' internal thoughts, providing deeper emotional insight.\n- Include telling details to bring scenes and characters to life, focusing on small but significant aspects.\n- Reveal characters through their actions and dialogue, allowing their personalities to emerge naturally.\n- Develop main characters as complex and evolving (round characters), while utilizing simpler (flat) characters where appropriate.\n- Create narrative tension by introducing conflicts or moral dilemmas, balancing plot progression with character development.\n- Control the pacing of the story, knowing when to slow down for detail or speed up to build tension.\n- Be concise and cut unnecessary words to keep the narrative tight and focused.\n- Allow themes to emerge organically from the plot and characters, exploring fundamental human experiences or questions.",

    "write_chapter": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nCharacters: {characters}\nChapter: {detailed_chapter}\nPlease continue writing this story until the natural end of the chapter. In your writing, please:\n- Craft sentences carefully, paying close attention to language that reflects the characters, settings, and themes.\n- Use sentence structures that create the desired impact, focusing on clarity, tension, or atmosphere as appropriate.\n- Employ free indirect style where suitable to blend third-person narration with characters' internal thoughts, providing deeper emotional insight.\n- Include telling details to bring scenes and characters to life, focusing on small but significant aspects.\n- Reveal characters through their actions and dialogue, allowing their personalities to emerge naturally.\n- Develop main characters as complex and evolving (round characters), while utilizing simpler (flat) characters where appropriate.\n- Create narrative tension by introducing conflicts or moral dilemmas, balancing plot progression with character development.\n- Control the pacing of the story, knowing when to slow down for detail or speed up to build tension.\n- Be concise and cut unnecessary words to keep the narrative tight and focused.\n- Allow themes to emerge organically from the plot and characters, exploring fundamental human experiences or questions.\nWhen the end of the chapter is reached, please write the special characters ^^^.\nPrevious section: {previous_section}"
}

summary_template_v0030 = {
    "create_summary": "Title: {title}\nSummary: {user_summary}\nPlease expand this into a more detailed narrative. Begin by focusing on the characters and their unique situations—ensure the central conflict is clear and rooted in emotional or moral stakes for the characters. Explore the decisions the characters make, showing how each choice affects the progression of the story, and reflect on how these decisions drive the plot. Include vivid descriptions of the characters, settings, and key events, but avoid predictable plot turns. Embrace realism by introducing natural consequences and surprise elements. Develop subplots that arise naturally from the characters' actions and add richness to the overall storyline, making sure to fully immerse the reader in each scene.",

    "create_summary_from_scratch": "Please create a detailed narrative based on this title: {title}\nStart by developing central characters and the situations they find themselves in, ensuring their core conflicts naturally drive the plot. Focus on what’s at stake for these characters emotionally or morally, making their dilemmas essential to their identity or world. Introduce subplots that enrich the main storyline by exploring character choices and responses, where each decision leads to the next stage of the narrative. Reflect the complexity of life in the plot structure—embracing unpredictability and avoiding a too-neat progression. Please incorporate vivid descriptions of characters, settings, and key events, creating immersive scenes that engage the reader fully.",

    "create_author": "Title: {title}\nSummary: {summary}\nPlease develop the author's profile for this story, focusing on the following aspects:\n1. Author's Personality: Describe the author's personality traits, passions, and worldview. Explain how these characteristics influence their writing style and narrative choices.\n2. Motivation for Writing the Novel: Discuss why the author is writing this novel. What personal experiences, beliefs, or messages are they aiming to convey? How do their motivations shape the themes and direction of the story?\n3. Writing Style and Subtleties: Elaborate on the author's unique style, including their use of language, subtleties, word choices, and narrative patterns. Consider how their background and perspective influence these elements. Ensure that the author's personality and motivations are deeply connected to the story's content, and that these elements are reflected in the way the story unfolds.",

    "create_characters": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nPlease create the characters for this story, focusing on the following aspects:\n1. Observation and realism: Use observations of real-life behavior to inform how the characters speak, act, and interact with others. Focus on creating characters that feel authentic and have natural traits.\n2. Character flaws: Make the characters imperfect with compelling quirks, contradictions, or flaws. Show how these imperfections influence their decisions and drive the story forward.\n3. Interiority: Develop each character’s inner life by exploring their motivations, fears, and desires. Let their internal struggles shape their external actions.\n4. Character growth: The characters should not be static. Show how they evolve or reveal new dimensions of themselves as the story progresses.\n5. Actions and dialogue: Reveal characters through their actions and dialogue, rather than exposition. Let their choices and words define who they are and how they relate to others.\n6. Psychological depth: Ensure that each character has a psychological complexity, showing thoughts and emotions that make them believable and engaging.",

    "create_themes_and_conflicts": "Title: {title}\nSummary: {summary}\nAuthor: {author}\nCharacters: {characters}\nPlease establish the themes and conflicts of this story, focusing on how the characters' internal and external conflicts evolve. Consider the moral dilemmas and emotional tensions they face, allowing themes to emerge naturally from their struggles. Introduce complications or reversals that create unpredictability while exploring any universal truths or human experiences that might arise from the narrative.",

    "create_novel_framework": "Title: {title}\nSummary: {user_summary}\nAuthor: {author}\nCharacters: {characters}\nThemes and Conflicts: {themes_and_conflicts}\n\nUsing the full scope of provided information, please construct a comprehensive framework for this novel. This framework should act as a foundational map for constructing each chapter of the novel, ensuring coherence and depth in the storytelling, with all elements working in harmony to create a compelling and immersive narrative.",

    "create_chapters": "Novel Framework: {novel_framework}\nPlease divide the story into 24 cohesive chapters, based on the summary provided. For each chapter, outline the primary focus, key events, and character developments, ensuring the plot grows organically from the characters’ desires, decisions, and conflicts. Reflect on how their choices under pressure drive the narrative forward. Each chapter should feature moments of tension, evolving conflicts, and delayed resolutions, while still maintaining a sense of momentum. Use subplots and layering to deepen the main narrative and enrich character interactions. Ensure that chapters open with a sense of purpose and conclude with unresolved questions or emotional tension to keep the reader engaged across the story arc. Weave in subtle foreshadowing, recurring symbols, and details to build anticipation, leading to a satisfying, layered conclusion.",

    "create_chapter": "Novel Framework: {novel_framework}\nChapter: {chapter}\nPlease expand upon the provided chapter by fleshing out the significant events, character interactions, and key moments. Focus on adding depth to scenes through sensory descriptions (sight, sound, touch, smell, taste) and meaningful details that highlight the setting and characters' emotions. Include suggestions for how characters' actions and gestures reveal their inner thoughts and motivations, and describe how the dialogue could incorporate subtext to suggest underlying tensions or relationships. Ensure the pacing builds appropriately, with slow, reflective moments for key emotional or thematic developments, and faster pacing for moments of action or tension. Provide ideas for how the chapter can progress towards a strong, impactful ending that leaves some tension unresolved or builds anticipation for what comes next. Additionally, suggest ways to naturally reveal character development and explore broader themes through the plot events and character decisions.",

    "write_first_chapter": "Novel Framework: {novel_framework}\nChapter Description: {detailed_chapter}\nPlease start writing this chapter. In your writing, please:\n- Craft sentences carefully, paying close attention to language that reflects the characters, settings, and themes.\n- Use sentence structures that create the desired impact, focusing on clarity, tension, or atmosphere as appropriate.\n- Employ free indirect style where suitable to blend third-person narration with characters' internal thoughts, providing deeper emotional insight.\n- Include telling details to bring scenes and characters to life, focusing on small but significant aspects.\n- Reveal characters through their actions and dialogue, allowing their personalities to emerge naturally.\n- Develop main characters as complex and evolving (round characters), while utilizing simpler (flat) characters where appropriate.\n- Create narrative tension by introducing conflicts or moral dilemmas, balancing plot progression with character development.\n- Control the pacing of the story, knowing when to slow down for detail or speed up to build tension.\n- Be concise and cut unnecessary words to keep the narrative tight and focused.\n- Allow themes to emerge organically from the plot and characters, exploring fundamental human experiences or questions.\nChapter {chapter_num}: ",

    "write_chapter": "Novel Framework: {novel_framework}\nChapter Description: {detailed_chapter}\nPlease continue writing this story until the natural end of the chapter. In your writing, please:\n- Craft sentences carefully, paying close attention to language that reflects the characters, settings, and themes.\n- Use sentence structures that create the desired impact, focusing on clarity, tension, or atmosphere as appropriate.\n- Employ free indirect style where suitable to blend third-person narration with characters' internal thoughts, providing deeper emotional insight.\n- Include telling details to bring scenes and characters to life, focusing on small but significant aspects.\n- Reveal characters through their actions and dialogue, allowing their personalities to emerge naturally.\n- Develop main characters as complex and evolving (round characters), while utilizing simpler (flat) characters where appropriate.\n- Create narrative tension by introducing conflicts or moral dilemmas, balancing plot progression with character development.\n- Control the pacing of the story, knowing when to slow down for detail or speed up to build tension.\n- Be concise and cut unnecessary words to keep the narrative tight and focused.\n- Allow themes to emerge organically from the plot and characters, exploring fundamental human experiences or questions.\nWhen the end of the chapter is reached, please write the special characters ^^^.\nPrevious section: {previous_section}"
}


# ---------------------------------------------------------------------------
# Public registry used by the settings UI and the /api/prompt-settings endpoint
#
# ``PROMPT_TEMPLATE_REGISTRY`` describes every editable template grouped by
# the generation version that uses it. ``keys`` is the ordered list of slots
# inside that template (either list indices as strings, or dict keys).
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE_REGISTRY = [
    {
        'version': 'v0',
        'label': 'v0 \u2013 Sequential single-pass pipeline',
        'templates': [
            {
                'name': 'outline_template_v0010',
                'label': 'Outline pipeline',
                'kind': 'list',
                'keys': ['0', '1', '2'],
                'key_labels': {
                    '0': 'Expand outline segment',
                    '1': 'Write narrative from outline',
                    '2': 'Revise rough draft',
                },
            },
            {
                'name': 'summary_template_v0002',
                'label': 'Summary pipeline',
                'kind': 'list',
                'keys': ['0', '1', '2', '3'],
                'key_labels': {
                    '0': 'Expand summary',
                    '1': 'Divide into 24 chapters',
                    '2': 'Develop chapter part',
                    '3': 'Enhance section cohesion',
                },
            },
        ],
    },
    {
        'version': 'v1',
        'label': 'v1 \u2013 Author/character/theme context',
        'templates': [
            {
                'name': 'summary_template_v0020',
                'label': 'Summary pipeline',
                'kind': 'dict',
                'keys': [
                    'create_summary',
                    'create_summary_from_scratch',
                    'create_author',
                    'create_characters',
                    'create_themes_and_conflicts',
                    'create_chapters',
                    'create_chapter',
                    'write_first_chapter',
                    'write_chapter',
                ],
            },
        ],
    },
    {
        'version': 'v2',
        'label': 'v2 \u2013 Novel framework planning (recommended)',
        'templates': [
            {
                'name': 'summary_template_v0030',
                'label': 'Summary pipeline',
                'kind': 'dict',
                'keys': [
                    'create_summary',
                    'create_summary_from_scratch',
                    'create_author',
                    'create_characters',
                    'create_themes_and_conflicts',
                    'create_novel_framework',
                    'create_chapters',
                    'create_chapter',
                    'write_first_chapter',
                    'write_chapter',
                ],
            },
        ],
    },
]


_TEMPLATES_BY_NAME = {
    'outline_template_v0010': outline_template_v0010,
    'summary_template_v0001': summary_template_v0001,
    'summary_template_v0002': summary_template_v0002,
    'summary_template_v0010': summary_template_v0010,
    'summary_template_v0020': summary_template_v0020,
    'summary_template_v0030': summary_template_v0030,
}


def get_default_template(name):
    """Return the module-level default template object for ``name``."""
    return _TEMPLATES_BY_NAME[name]


def get_default_prompts():
    """Return a deep copy of the defaults for every registered template.

    The returned structure mirrors what users store as their overrides: a
    dict keyed by template name whose values are either a list of strings
    (for list templates) or a dict of name -> string (for dict templates).
    List templates are serialised as dicts keyed by stringified indices so
    the JSON roundtrip is lossless.
    """
    result = {}
    for group in PROMPT_TEMPLATE_REGISTRY:
        for tpl in group['templates']:
            default = _TEMPLATES_BY_NAME[tpl['name']]
            if tpl['kind'] == 'list':
                result[tpl['name']] = {
                    k: default[int(k)] for k in tpl['keys']
                }
            else:
                result[tpl['name']] = {k: default[k] for k in tpl['keys']}
    return result


def resolve_template(name, overrides):
    """Return the template for ``name`` honouring any overrides.

    ``overrides`` is the dict persisted on ``User.prompt_settings_json``.
    Missing keys silently fall back to the module defaults so partial
    overrides are valid. The returned object has the same shape (list or
    dict) as the module-level default for ``name``.
    """
    default = _TEMPLATES_BY_NAME[name]
    if not overrides:
        return default
    override = overrides.get(name)
    if not isinstance(override, dict):
        return default

    if isinstance(default, list):
        merged = list(default)
        for k, v in override.items():
            if not isinstance(v, str):
                continue
            try:
                idx = int(k)
            except (TypeError, ValueError):
                continue
            if 0 <= idx < len(merged):
                merged[idx] = v
        return merged

    merged = dict(default)
    for k, v in override.items():
        if k in merged and isinstance(v, str):
            merged[k] = v
    return merged