# CLAT Daily Quiz Agent

Automated daily quiz system for CLAT exam preparation. Generates adaptive quizzes based on performance analytics using Claude AI.

## Features

- Daily adaptive quizzes with 10 questions and 6-minute time limit
- Single comprehension passage format (matches CLAT exam)
- Performance tracking and weak area identification
- WhatsApp notifications via Twilio
- Google OAuth authentication with configurable authorized users

## Setup

### 1. Clone and Install

```bash
git clone <repo-url>
cd daily-quiz-agent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth credentials
- `AUTHORIZED_EMAILS` - Comma-separated list of authorized user emails (leave empty to allow anyone)
- `ANTHROPIC_API_KEY` - Claude API key
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` - Twilio credentials (optional)
- `NOTIFICATION_PHONE` - WhatsApp number to notify (optional)

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the OAuth2 API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:5000/auth/callback` (for development)
6. Copy Client ID and Client Secret to `.env`

### 4. Run Development Server

```bash
python run.py
```

Visit `http://localhost:5000`

## Project Structure

```
daily-quiz-agent/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Flask routes
│   ├── services/        # Business logic
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS/JS assets
├── scripts/
│   └── generate_quiz.py # Daily cron script
├── tests/               # Test files
└── wsgi.py              # Production entry point
```

## Daily Quiz Generation

The `scripts/generate_quiz.py` script runs daily to:
1. Analyze user's 7-day performance
2. Build adaptive prompt focusing on weak areas
3. Call Claude API to generate quiz
4. Store quiz in SQLite database
5. Send WhatsApp notification

Cron setup (7:30 AM IST = 2:00 UTC):
```cron
0 2 * * * cd /var/www/quiz && venv/bin/python scripts/generate_quiz.py
```

## Testing

```bash
pytest tests/
```

## Deployment

GitHub Actions automatically deploys to Lightsail on push to main.

Required GitHub Secrets:
- `LIGHTSAIL_HOST`
- `LIGHTSAIL_USER`
- `LIGHTSAIL_SSH_KEY`
