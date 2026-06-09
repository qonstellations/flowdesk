# FlowDesk Local Setup Guide

This guide gets FlowDesk running on a fresh machine with:

- Streamlit frontend
- FastAPI Telegram webhook backend
- ngrok public URL for Telegram and Google OAuth callbacks
- Google OAuth for student login and Telegram linking
- Gemini, OpenAI, or Ollama for LLM calls

## 1. Install Prerequisites

Install these first:

- Git: https://git-scm.com/downloads
- uv: https://docs.astral.sh/uv/getting-started/installation/
- Python 3.13, managed automatically by `uv`
- ngrok: https://ngrok.com/download
- Optional for local LLMs: Ollama: https://ollama.com/download

Clone the repo:

```bash
git clone https://github.com/qonstellations/flowdesk.git
cd flowdesk
```

Install Python dependencies:

```bash
uv sync
```

## 2. Create Required Accounts and Keys

### Telegram Bot Token
ALREADY GIVEN TO ALL TEAM USERS

### ngrok Public URL

Create an account at:

```text
https://ngrok.com
```

Authenticate ngrok locally:

```bash
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

Start a tunnel to the FastAPI backend port:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL, for example:

```text
https://abc123.ngrok-free.app
```

Use this as:

```env
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok-free.app
GOOGLE_REDIRECT_URI=https://abc123.ngrok-free.app/auth/google/callback
```

Keep ngrok running while testing Telegram.

### Google OAuth Client

Create a Google Cloud project:

```text
https://console.cloud.google.com
```

Then:

1. Go to `APIs & Services` -> `OAuth consent screen`.
2. Configure the consent screen.
3. Go to `APIs & Services` -> `Credentials`.
4. Create `OAuth client ID`.
5. Choose `Web application`.
6. Add these Authorized redirect URIs:

```text
http://localhost:8501/oauth2callback
https://abc123.ngrok-free.app/auth/google/callback
```

Replace `https://abc123.ngrok-free.app` with your actual ngrok HTTPS URL.

Leave Authorized JavaScript origins empty. FlowDesk uses server-side OAuth redirects.

Copy the Google OAuth client values:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://abc123.ngrok-free.app/auth/google/callback
```

### LLM Provider

Pick one.

#### Option A: Gemini

Create a key at:

```text
https://aistudio.google.com/app/apikey
```

Use:

```env
LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.0-flash
```

#### Option B: OpenAI

Create a key at:

```text
https://platform.openai.com/api-keys
```

Use:

```env
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
LLM_MODEL=gpt-4.1-mini
```

#### Option C: Ollama

Install Ollama, then pull a model:

```bash
ollama pull llama3.2:3b
```

Keep Ollama running, then use:

```env
LLM_PROVIDER=ollama
LLM_API_KEY=
LLM_MODEL=llama3.2:3b
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT_SECONDS=180
```

Local models must return valid JSON for structured calls. If ticket creation fails with JSON parsing errors, use Gemini/OpenAI or a stronger local instruct model.

## 3. Create `.env`

Copy the example:

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your-telegram-token
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok-free.app

LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.0-flash
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT_SECONDS=120

ADMIN_KEY=choose-a-password-for-admin-login

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://abc123.ngrok-free.app/auth/google/callback

ALLOWED_EMAIL_DOMAINS=
DATABASE_PATH=data/flowdesk.db
```

`ALLOWED_EMAIL_DOMAINS=` can stay empty. That allows any verified Google account.

## 4. Create Streamlit Secrets

Copy the example:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "replace-with-a-long-random-cookie-secret"
client_id = "your-client-id.apps.googleusercontent.com"
client_secret = "your-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Generate a cookie secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste that value into `cookie_secret`.

## 5. Start the App

Use three terminals.

### Terminal 1: ngrok

```bash
ngrok http 8000
```

If the ngrok URL changes, update:

- `.env` -> `TELEGRAM_WEBHOOK_URL`
- `.env` -> `GOOGLE_REDIRECT_URI`
- Google OAuth client authorized redirect URI

### Terminal 2: FastAPI Backend

```bash
uv run uvicorn backend.webhook:app --host 0.0.0.0 --port 8000 --reload
```

On startup, the backend registers the Telegram webhook automatically if `TELEGRAM_WEBHOOK_URL` is set.

Backend health check:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

### Terminal 3: Streamlit Frontend

```bash
uv run streamlit run app/main.py
```

Open:

```text
http://localhost:8501
```

## 6. First-Time App Setup

1. Open the frontend.
2. Enter Admin Dashboard.
3. Use the `ADMIN_KEY` from `.env`.
4. Create at least one active department.

Example department:

```text
Name: General Admin
Responsibilities: Handles all general campus complaints and routes unclear issues.
Contact: Admin office
Email ID: admin@example.com
Active: checked
```

The bot cannot route tickets until at least one active department exists.

## 7. Student Flow

### Link Telegram to Google

In Telegram, message your bot:

```text
/start
/link
```

Open the Google sign-in link from Telegram. After sign-in, the Telegram account is linked to that Google account.

### Create a Ticket

In Telegram:

```text
/ticket Wi-Fi is not working in the library second floor
```

If the issue is vague, the bot asks follow-up questions. Reply normally in Telegram.

### Check Ticket Status

In Telegram:

```text
/status
```

Or open the Streamlit frontend, enter Student Portal, and log in with Google.

## 8. Common Problems

### Telegram says webhook failed

Check:

- ngrok is still running.
- `.env` has the current ngrok HTTPS URL.
- Backend was restarted after changing `.env`.
- `TELEGRAM_WEBHOOK_URL` does not include `/webhook`; the app adds that automatically.

Correct:

```env
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok-free.app
```

Wrong:

```env
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok-free.app/webhook
```

### Google says redirect URI mismatch

The URI in Google Cloud must exactly match the app.

For Telegram `/link`:

```text
https://abc123.ngrok-free.app/auth/google/callback
```

For Streamlit login:

```text
http://localhost:8501/oauth2callback
```

### Admin says `ADMIN_KEY is not configured`

Check `.env`:

```env
ADMIN_KEY=some-value
```

Restart Streamlit after changing `.env`.

### Ollama times out

Use a smaller model or increase timeout:

```env
OLLAMA_TIMEOUT_SECONDS=180
```

Recommended local speed:

- Minimum: 8-10 tokens/second
- Comfortable: 15-25 tokens/second
- Smooth: 30+ tokens/second

For easiest setup, use Gemini first and switch to Ollama later.

### LLM returned invalid JSON

Local models sometimes ignore JSON instructions. Try:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
```

or use a stronger local instruct model.

## 9. Reset Local Data

To reset the local database:

```bash
rm -f data/flowdesk.db
```

Then restart the backend or frontend. The DB schema is recreated automatically.

