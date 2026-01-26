# CLAT Quiz App - Deployment Guide

## Overview

This guide covers deploying the CLAT Quiz app to AWS Lightsail.

**Architecture:**
```
User Browser
     ↓
quiz.germanwakad.click (Route 53 DNS)
     ↓
Lightsail Instance (Static IP)
     ↓
Nginx (port 80/443) → reverse proxy
     ↓
Gunicorn (port 5001) → WSGI server
     ↓
Flask App → serves quiz pages
     ↓
SQLite Database (/var/db/quiz.db)
```

**Daily Quiz Generation (Cron):**
```
7:30 AM IST → Cron triggers generate_quiz.py
     ↓
Fetch user analytics from SQLite
     ↓
Call Claude API with adaptive prompt
     ↓
Save quiz to database
     ↓
Send WhatsApp notification via Twilio
```

---

## Prerequisites

Before starting, ensure you have:

1. **Lightsail instance** running (Ubuntu 20.04+ recommended)
2. **Static IP** attached to the instance
3. **Route 53 A record** for `quiz.germanwakad.click` pointing to static IP
4. **SSH access** to the instance
5. **GitHub repository** with the code pushed

**Required credentials (have these ready):**
- Google OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Anthropic: `ANTHROPIC_API_KEY`
- Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `NOTIFICATION_PHONE`

---

## Part 1: Initial Server Setup (One-Time)

### Step 1.1: SSH into Lightsail

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_STATIC_IP
```

### Step 1.2: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx git
```

### Step 1.3: Create Directories

```bash
sudo mkdir -p /var/www/quiz
sudo mkdir -p /var/db
sudo chown -R ubuntu:ubuntu /var/www/quiz
sudo chown -R ubuntu:ubuntu /var/db
```

### Step 1.4: Clone Repository

```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/daily-quiz-agent.git quiz
cd /var/www/quiz
```

### Step 1.5: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 1.6: Create and Configure .env File (CRITICAL)

> **STOP! Do not skip this step.** The app will not work without proper credentials.

**Step 1.6a: Copy the template**
```bash
cp .env.example .env
```

**Step 1.6b: Generate a secret key**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output - you'll use it below.

**Step 1.6c: Edit the .env file**
```bash
nano .env
```

**Step 1.6d: Update ALL these values with your real credentials:**

```env
# Flask - paste the secret key you generated above
SECRET_KEY=paste-your-generated-secret-key-here
FLASK_ENV=production

# Database - use this exact path
DATABASE_PATH=/var/db/quiz.db

# Google OAuth (from Google Cloud Console → APIs & Services → Credentials)
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-actual-secret

# Authorized users - your daughter's actual email
AUTHORIZED_EMAILS=actual-email@gmail.com

# Claude API (from console.anthropic.com → API Keys)
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key

# Twilio WhatsApp (from twilio.com → Console → Account Info)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
NOTIFICATION_PHONE=+919876543210

# Production URL - use exactly this
BASE_URL=https://quiz.germanwakad.click

# Quiz generation time (IST, 24-hour format)
QUIZ_GENERATION_TIME_IST=07:30
```

**Step 1.6e: Save and exit nano**
- Press `Ctrl+X`, then `Y`, then `Enter`

**Step 1.6f: Verify your .env file**
```bash
# Check all required values are set (not placeholder values)
grep -E "^(SECRET_KEY|GOOGLE_CLIENT_ID|ANTHROPIC_API_KEY|AUTHORIZED_EMAILS)" .env
```
Make sure none of them still say "your-" or "paste-".

### Step 1.7: Initialize Database

```bash
source venv/bin/activate
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.extensions import db; db.create_all(); print('Database initialized')"
```

---

## Part 2: Systemd Service Setup

### Step 2.1: Install Service File

```bash
sudo cp /var/www/quiz/deploy/quiz.service /etc/systemd/system/quiz.service
sudo systemctl daemon-reload
sudo systemctl enable quiz
sudo systemctl start quiz
```

### Step 2.2: Verify Service is Running

```bash
sudo systemctl status quiz
```

Should show `active (running)`. If not, check logs:
```bash
sudo journalctl -u quiz -f
```

---

## Part 3: Nginx Setup

### Step 3.1: Install Nginx Config

```bash
sudo cp /var/www/quiz/deploy/nginx.conf /etc/nginx/sites-available/quiz
sudo ln -sf /etc/nginx/sites-available/quiz /etc/nginx/sites-enabled/quiz
```

### Step 3.2: Test and Reload Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3.3: Test HTTP Access

Open browser: `http://quiz.germanwakad.click`

You should see the login page (without HTTPS for now).

---

## Part 4: SSL/HTTPS Setup

### Step 4.1: Install Certbot

```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 4.2: Get SSL Certificate

```bash
sudo certbot --nginx -d quiz.germanwakad.click
```

Follow the prompts. Certbot will:
- Obtain certificate from Let's Encrypt
- Automatically configure nginx for HTTPS
- Set up auto-renewal

### Step 4.3: Verify HTTPS

Open browser: `https://quiz.germanwakad.click`

---

## Part 5: Cron Job Setup

### Step 5.1: Edit Crontab

```bash
crontab -e
```

### Step 5.2: Add Quiz Generation Job

Add this line (7:30 AM IST = 2:00 AM UTC):
```cron
0 2 * * * cd /var/www/quiz && /var/www/quiz/venv/bin/python scripts/generate_quiz.py >> /var/log/quiz-cron.log 2>&1
```

### Step 5.3: Verify Cron is Set

```bash
crontab -l
```

### Step 5.4: Test Quiz Generation Manually

```bash
cd /var/www/quiz
source venv/bin/activate
python scripts/generate_quiz.py
```

---

## Part 6: Google OAuth Production Setup

### Step 6.1: Update Google Cloud Console

Go to Google Cloud Console → APIs & Services → Credentials

**Add Authorized redirect URI:**
```
https://quiz.germanwakad.click/auth/callback
```

**Add Authorized JavaScript origin:**
```
https://quiz.germanwakad.click
```

---

## Part 7: GitHub Actions Setup (Continuous Deployment)

### Step 7.1: Add GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:
| Secret Name | Value |
|-------------|-------|
| `LIGHTSAIL_HOST` | Your Lightsail static IP |
| `LIGHTSAIL_USER` | `ubuntu` |
| `LIGHTSAIL_SSH_KEY` | Contents of your private SSH key |

### Step 7.2: Test Deployment

Push a commit to `main` branch. GitHub Actions will:
1. SSH into Lightsail
2. Pull latest code
3. Install dependencies
4. Restart the quiz service

Check: GitHub repo → Actions tab

---

## Part 8: Verification Checklist

After deployment, verify everything works:

- [ ] `https://quiz.germanwakad.click` loads login page
- [ ] Google OAuth login works
- [ ] Quiz displays correctly after login
- [ ] Quiz submission works, results show
- [ ] Manual quiz generation works: `python scripts/generate_quiz.py`
- [ ] GitHub Actions deployment succeeds on push
- [ ] (Next day) Cron generates quiz at 7:30 AM IST
- [ ] (Next day) WhatsApp notification received

---

## Troubleshooting

### App not loading
```bash
sudo systemctl status quiz
sudo journalctl -u quiz -n 50
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Database issues
```bash
ls -la /var/db/quiz.db
# Check permissions - should be owned by ubuntu
```

### OAuth errors
- Verify redirect URI in Google Console matches exactly
- Check BASE_URL in .env is `https://quiz.germanwakad.click`

### Cron not running
```bash
# Check cron logs
grep CRON /var/log/syslog | tail -20

# Check quiz-specific logs
cat /var/log/quiz-cron.log
```

---

## Useful Commands

```bash
# Restart app
sudo systemctl restart quiz

# View app logs
sudo journalctl -u quiz -f

# Restart nginx
sudo systemctl reload nginx

# Check cron schedule
crontab -l

# Generate quiz manually
cd /var/www/quiz && source venv/bin/activate && python scripts/generate_quiz.py

# Check database
cd /var/www/quiz && source venv/bin/activate
python -c "from app import create_app; from app.models import Quiz; app = create_app(); app.app_context().push(); print(Quiz.query.count(), 'quizzes')"
```

---

## Changing Quiz Generation Time

1. Edit `.env`:
   ```
   QUIZ_GENERATION_TIME_IST=07:15
   ```

2. Get new cron schedule:
   ```bash
   python scripts/show_cron_schedule.py
   ```

3. Update crontab with new schedule:
   ```bash
   crontab -e
   ```
