# AI Gmail Agent 🤖 📧 (Python)

An AI-powered CLI that drafts emails using **Claude AI**, fetches files from **Google Drive**, and sends them via **Gmail** — all from your terminal.

---

## Features

- 🤖 **AI email drafting** — Give Claude key points, it writes the full email
- 📁 **Google Drive attachment** — Search by file name, downloads automatically
- 📬 **Save as Gmail Draft** — Review in Gmail before sending
- 🚀 **Send immediately** — Send directly from the CLI
- 🎨 **Rich interactive CLI** — Colourful, step-by-step prompts

---

## Prerequisites

- **Python 3.8+** — check with `python --version`
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com/)
- **Google Cloud project** with Gmail API + Drive API enabled

---

## Setup

### 1. Install dependencies

```bash
cd gmail-ai-agent-python
pip install -r requirements.txt
```

### 2. Set up your `.env`

```bash
cp .env.example .env
```

### 3. Set up Google OAuth credentials (one-time)

#### A — Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **New Project**, give it a name (e.g. `gmail-ai-agent`)

#### B — Enable APIs

Go to **APIs & Services → Library** and enable:
- ✅ **Gmail API**
- ✅ **Google Drive API**

#### C — Create OAuth 2.0 credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. If prompted, set up the OAuth consent screen first:
   - User type: **External**
   - App name: `Gmail AI Agent`
   - Add your email as a **test user**
4. Application type: **Web application**
5. Authorized redirect URI: `http://localhost:3000/oauth2callback`
6. Copy **Client ID** and **Client Secret** into `.env`:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

### 4. Authenticate with Google (one-time)

```bash
python auth.py
```

A browser opens — log in and approve. A `token.json` is saved locally.

---

## Usage

```bash
python main.py
```

The CLI walks you through:

1. **Recipients** — one or more email addresses
2. **Email details** — subject, key points, tone, your name
3. **Attachment** — optionally search Google Drive by file name
4. **AI drafts the email** — Claude writes subject + body
5. **Preview** the draft in the terminal
6. **Choose**: Save as Draft / Send immediately / Re-draft / Cancel

---

## File structure

```
gmail-ai-agent-python/
├── main.py          # Interactive CLI (entry point)
├── auth.py          # Google OAuth flow
├── drive.py         # Google Drive file search & download
├── drafter.py       # Claude AI email drafting
├── gmail.py         # Gmail send / draft creation
├── requirements.txt
├── .env             # Your secrets (never commit)
├── .env.example     # Template
└── token.json       # Auto-created after auth (never commit)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Authentication failed` | Run `python auth.py` first |
| File not found in Drive | Check the spelling — search is a substring match |
| `insufficient permission` | Delete `token.json` and run `python auth.py` again |
| Gmail / Drive API errors | Make sure both APIs are enabled in Google Cloud Console |

---

## Security

- `token.json` and `.env` are in `.gitignore` — never commit them
- OAuth tokens auto-refresh when expired
- Only requests minimum required scopes (compose + send + Drive read-only)
