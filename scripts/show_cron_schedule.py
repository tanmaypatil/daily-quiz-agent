#!/usr/bin/env python
"""
Helper script to show the cron schedule for the configured quiz generation time.
Run this after changing QUIZ_GENERATION_TIME_IST in .env to get the crontab entry.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

if __name__ == '__main__':
    ist_time = Config.QUIZ_GENERATION_TIME_IST
    cron_schedule = Config.get_cron_schedule()

    print(f"\nQuiz Generation Time Configuration")
    print(f"=" * 40)
    print(f"IST Time: {ist_time}")
    print(f"Cron Schedule (UTC): {cron_schedule}")
    print(f"\nCrontab entry for Lightsail:")
    print(f"{cron_schedule} cd /var/www/quiz && venv/bin/python scripts/generate_quiz.py")
    print()
