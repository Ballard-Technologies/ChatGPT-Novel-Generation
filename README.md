# AI Novel Generation

## Description

Research into exploring AI's efficacy in writing novels (using models like Grok/xAI, OpenAI, and others).

## Web Application

Everyone is welcome to test advanced AI's ability to write a novel! Please follow these steps to create your own AI-generated novel:

1. Get an API Key from your preferred provider (OpenAI, xAI/Grok, etc.).

2. Visit the deployed app.

3. Enter your API Key.

4. Fill out the details for the novel (genre, plot, style, length, etc.).

5. The application uses iterative, strategic prompting to generate novel-length text.

6. A PDF will automatically download when complete.

7. Feel free to leave feedback about the quality [via email](https://coleb.io/contact).

## Note

- The application **never** stores or uses your API Key outside of your own prompts. All of the code in this repository is public.
- Supports a selection of models for bulk prompts (including larger and more cost-effective options).

## Deployment

The app expects the following environment variables in production:

- `SECRET_KEY` - required when `ENV=production`; signs session cookies.
- `JAWSDB_MARIA_URL` or `DATABASE_URL` - MariaDB/MySQL connection string.
- `REDISCLOUD_URL` - Redis connection string used for the RQ job queue and progress channel.
- `RATELIMIT_STORAGE_URI` - optional; defaults to `memory://` when unset.

Two process types are defined in `Procfile`:

- `web: gunicorn app:app` - serves HTTP requests.
- `worker: rq worker --url $REDISCLOUD_URL default` - runs background novel-generation jobs.

## Contribution

Contribution is closed at the moment. Sorry for the inconvenience.

## **[Contact](https://github.com/ColeBallard/coleballard.github.io/blob/main/README.md)**
