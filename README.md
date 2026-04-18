# ChatGPT Novel Generation

## Description

Research into exploring ChatGPT's efficacy in writing novels.

## Web Application

Everyone is welcome to test ChatGPT's ability to write a novel! Please follow these steps to create your own ChatGPT-generated novel:

1. [Create an OpenAI account and get an API Key.](https://www.maisieai.com/help/how-to-get-an-openai-api-key-for-chatgpt)

2. Go to [https://chatgpt-novel-generation-e0691bd56612.herokuapp.com/](https://chatgpt-novel-generation-e0691bd56612.herokuapp.com/).

3. Press the API Key button, then paste your OpenAI API Key in the designated input field.

4. Fill out the details for the novel you would like to be generated.

5. The application will use iteration and strategic prompting to create a novel-length text.

6. A pdf will automatically be downloaded whenever the loading bar gets to 100%.

7. Feel free to leave feedback about the quality of the produced text [via email](https://coleb.io/contact).

## Note

- The application **never** stores or uses your API Key outside of your own prompts. All of the code in this repository is public.
- The application supports a selection of OpenAI models for bulk prompts, including larger options (gpt-5.4, gpt-5, gpt-4.1) and smaller, cheaper options (gpt-5.4-mini, gpt-5.4-nano, gpt-5-mini, gpt-4.1-mini). Most prompts total out between 25-200 cents depending on the base model used.

## Deployment

The app expects the following environment variables in production:

- `SECRET_KEY` - required when `ENV=production`; signs session cookies.
- `JAWSDB_MARIA_URL` or `DATABASE_URL` - MariaDB/MySQL connection string.
- `REDISCLOUD_URL` - Redis connection string used for the RQ job queue and
  progress channel. Heroku's Redis Cloud add-on sets this automatically.
- `RATELIMIT_STORAGE_URI` - optional; defaults to `memory://` when unset.
  Set to a Redis URL in production so the rate limiter stays consistent
  across web dynos.

Two process types are defined in `Procfile`:

- `web: gunicorn app:app` - serves HTTP requests.
- `worker: rq worker --url $REDISCLOUD_URL default` - runs background
  novel-generation jobs.

### Local development without Redis

If `REDISCLOUD_URL` is not set, the queue factory falls back to a
synchronous in-process runner and jobs execute on the web request's
thread. Cancellation and progress still work; no separate worker
process is required.

## Contribution

Contribution is closed at the moment. Sorry for the inconvenience.

## **[Contact](https://github.com/ColeBallard/coleballard.github.io/blob/main/README.md)**
