# CLAT Quiz Agent - Project Context

## What We're Building
An automated daily quiz system for CLAT (Common Law Admission Test) exam preparation. Every morning at 7:30 AM IST, the system generates an adaptive quiz based on performance analytics, posts it to a website, and sends an email notification.
It will be a single paragraph with 10 questions and time limit of 6 minutes.

## Key Decisions Made

### Why This Approach?
- **Single user** (daughter preparing for CLAT) - no need for complex scaling .
- **Adaptive learning** - quiz difficulty and topics adjust based on her weak areas
- **Daily habit formation** - consistent 7:30 AM routine
- **Data-driven improvement** - track performance trends over time

### Technology Choices

**Hosting**: AWS Lightsail (quiz.germanwakad.click subdomain)
- We already run germanwakad.click on Lightsail with Flask
- Keep everything in one place for simplicity

**Stack**: Python + Flask
- Consistency with existing germanwakad.click app
- We know it, deployment is already set up

**Database**: SQLite
- Single user, low concurrency
- File-based, no separate database server needed
- Lives on Lightsail instance
- Can migrate to PostgreSQL later if needed

**Deployment**: GitHub Actions
- Automated CI/CD via SSH to Lightsail
- Git push → auto deploy

**Authentication**: Google OAuth
- Only daughter has access. 
- Simple, secure

**Notifications**: Gmail SMTP
- Sends quiz link every morning via email
- Free, reliable, no sandbox limitations

### Architecture Philosophy

**Simple Workflow, Not Agentic**
- We don't need a full AI agent making decisions
- Fixed workflow: analyze → generate → post → notify
- Intelligence comes from **adaptive prompts** to Claude, not tool-using agents

**Single Claude API Call**
- Analytics → Build smart prompt → Claude generates quiz
- No multi-step reasoning needed
- Cost-effective, predictable

## How Adaptation Works

### The Intelligence Layer
Quiz adapts based on:
- **Weak areas** (< 60% accuracy) get more questions
- **Time struggles** (slow + low accuracy) get targeted practice  
- **Recent trends** (improving/declining areas)
- **Difficulty calibration** based on category performance

### What We Track
Every quiz stores:
- Score, time spent overall
- Per-question: answer, correctness, time spent
- Category breakdown (Constitutional Law, Legal Reasoning, etc.)
- Difficulty breakdown (easy/medium/hard)

Analytics calculate:
- 7-day rolling averages by category
- Weak areas needing focus
- Topics where she's improving
- Time management issues

### Adaptive Prompt
We build a detailed prompt for Claude with:
- Her performance data
- Which topics to focus on (6 questions from weak areas)
- Difficulty calibration per topic
- CLAT exam format requirements

Claude returns 10 questions as JSON. We render as HTML.

## Daily Workflow

**7:30 AM (Cron on Lightsail)**
1. Fetch analytics from SQLite
2. Build adaptive prompt
3. Call Claude API
4. Generate HTML quiz page
5. Send email notification via Gmail SMTP

**User Takes Quiz**
1. Clicks link, loads quiz page
2. Answers 10 questions
3. Submits via Flask API
4. Gets immediate results with explanations
5. Data stored in SQLite

**Analytics Update**
- New performance data added
- Rolling averages recalculated
- Next day's quiz will adapt

## What Makes This Work

**Not Over-Engineered**
- No microservices, no Kubernetes, no separate API layer
- Everything on one Lightsail instance
- SQLite file in `/var/db/quiz.db`
- Static HTML + Flask API

**Focused on Value**
- The value is **adaptive quizzes** based on her weaknesses
- Not in fancy tech or agentic capabilities
- Simple, reliable, effective

**Room to Grow**
- Start with basic analytics
- Can add: spaced repetition, mock exam correlation, weekly reports
- Can migrate to PostgreSQL if needed
- Can add more users later if needed

## Key Constraints

- **Single user** - daughter only (via Google OAuth)
- **Low traffic** - one quiz per day
- **Simple deployment** - GitHub push → Lightsail
- **Keep it consistent** - match germanwakad.click stack
- **Fully automated** - no manual intervention needed

## Future Possibilities

Later we might add:
- Spaced repetition (re-ask missed questions)
- Mock exam score correlation
- Weekly performance emails
- Analytics dashboard
- More sophisticated adaptation logic

But start simple and prove value first.

## Current Deployment

**Live URL**: https://quiz.germanwakad.click

**Architecture**:
```
User Browser → Nginx (443) → Gunicorn (127.0.0.1:5002) → Flask App
```

**Server Details**:
- AWS Lightsail (512MB RAM + 1GB swap)
- Ubuntu 22.04
- Port 5002 (port 5001 used by gmail-chat app)
- SSL via Let's Encrypt (certbot)

**Key Paths**:
- App: `/var/www/quiz/`
- Database: `/var/db/quiz.db`
- Logs: `/var/log/quiz-generator.log`
- Service: `/etc/systemd/system/quiz.service`
- Nginx: `/etc/nginx/sites-available/quiz`

**Cron Job** (7:30 AM IST = 2:00 AM UTC):
```
0 2 * * * cd /var/www/quiz && /var/www/quiz/venv/bin/python scripts/generate_quiz.py >> /var/log/quiz-cron.log 2>&1
```

## Environment Setup

**Required `.env` variables**:
```env
# Flask
SECRET_KEY=<random-secret>
FLASK_ENV=production

# Database
DATABASE_PATH=/var/db/quiz.db

# Google OAuth
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>

# Authorized users (comma-separated emails)
AUTHORIZED_EMAILS=daughter@gmail.com

# Claude API
ANTHROPIC_API_KEY=sk-ant-<your-key>

# Gmail SMTP for notifications
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Gmail App Password (not regular password)
NOTIFICATION_EMAIL=daughter@gmail.com

# App URL
BASE_URL=https://quiz.germanwakad.click

# Quiz generation time (IST)
QUIZ_GENERATION_TIME_IST=07:30
```

**Gmail App Password Setup**:
1. Go to Google Account → Security → 2-Step Verification (enable if not already)
2. Go to App passwords (at bottom of 2-Step Verification page)
3. Generate a new app password for "Mail"
4. Use this 16-character password as SMTP_PASSWORD (not your regular Gmail password)

## Useful Commands

```bash
# Restart app
sudo systemctl restart quiz

# View logs
sudo journalctl -u quiz -f

# Generate quiz manually
cd /var/www/quiz && source venv/bin/activate && python scripts/generate_quiz.py

# Test email notification
python -c "from app import create_app; from app.services.notification import NotificationService; app = create_app(); app.app_context().push(); NotificationService().send_quiz_notification('test@gmail.com', 'https://quiz.germanwakad.click/quiz/2024-01-01')"

# Check cron schedule
python scripts/show_cron_schedule.py
```

## Remember

This is an **adaptive quiz system**, not a general-purpose AI agent. The intelligence is in:
1. Tracking granular performance data
2. Analyzing trends and weak areas  
3. Building smart prompts for Claude
4. Consistent daily delivery

Keep it simple, focused, and effective.