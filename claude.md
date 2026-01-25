# CLAT Quiz Agent - Project Context

## What We're Building
An automated daily quiz system for CLAT (Common Law Admission Test) exam preparation. Every morning at 7:30 AM IST, the system generates an adaptive quiz based on performance analytics, posts it to a website, and sends a WhatsApp notification.
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

**Notifications**: Twilio WhatsApp API
- Sends quiz link every morning

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
5. Send WhatsApp link via Twilio

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

## Environment Setup

Key configs needed:
- `ANTHROPIC_API_KEY` - for Claude API
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` - for WhatsApp
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - for OAuth
- Database path: `/var/db/quiz.db`
- Quiz HTML served from: `/var/www/quiz/`

## Remember

This is an **adaptive quiz system**, not a general-purpose AI agent. The intelligence is in:
1. Tracking granular performance data
2. Analyzing trends and weak areas  
3. Building smart prompts for Claude
4. Consistent daily delivery

Keep it simple, focused, and effective.