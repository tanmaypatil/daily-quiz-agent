import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'quiz.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Authorized users - comma-separated list of emails
    # Example: "user1@gmail.com,user2@gmail.com"
    # If empty, anyone with Google account can access
    _authorized_emails_str = os.environ.get('AUTHORIZED_EMAILS', '')
    AUTHORIZED_EMAILS = [e.strip() for e in _authorized_emails_str.split(',') if e.strip()]

    # External APIs
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

    # Gmail SMTP for notifications
    SMTP_EMAIL = os.environ.get('SMTP_EMAIL')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL')

    # App settings
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    QUIZ_TIME_LIMIT_SECONDS = 360  # 6 minutes

    # Quiz generation time (IST, 24-hour format like "07:30" or "07:15")
    # Note: Update crontab on Lightsail when changing this
    # Cron runs in UTC, so IST 07:30 = UTC 02:00, IST 07:15 = UTC 01:45
    QUIZ_GENERATION_TIME_IST = os.environ.get('QUIZ_GENERATION_TIME_IST', '07:30')

    @staticmethod
    def get_cron_schedule():
        """Convert IST time to UTC cron schedule string"""
        time_ist = Config.QUIZ_GENERATION_TIME_IST
        try:
            hour, minute = map(int, time_ist.split(':'))
            # IST is UTC+5:30
            utc_hour = hour - 5
            utc_minute = minute - 30
            if utc_minute < 0:
                utc_minute += 60
                utc_hour -= 1
            if utc_hour < 0:
                utc_hour += 24
            return f"{utc_minute} {utc_hour} * * *"
        except:
            return "0 2 * * *"  # Default: 7:30 AM IST
