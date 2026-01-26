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
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    NOTIFICATION_PHONE = os.environ.get('NOTIFICATION_PHONE')
    TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

    # App settings
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    QUIZ_TIME_LIMIT_SECONDS = 360  # 6 minutes
