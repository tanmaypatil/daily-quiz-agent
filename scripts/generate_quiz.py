#!/usr/bin/env python
"""
Daily Quiz Generation Script
Run via cron at 7:30 AM IST daily

Crontab entry (IST = UTC+5:30, so 7:30 IST = 2:00 UTC):
0 2 * * * cd /path/to/daily-quiz-agent && /path/to/venv/bin/python scripts/generate_quiz.py
"""
import os
import sys
import logging
from datetime import date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/quiz-generator.log') if os.path.exists('/var/log') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Generate today's quiz and send notification"""
    logger.info("Starting daily quiz generation")

    from app import create_app
    from app.extensions import db
    from app.models import User, Quiz
    from app.services.quiz_generator import QuizGeneratorService
    from app.services.notification import NotificationService

    app = create_app()

    with app.app_context():
        try:
            # Check if quiz already exists for today
            today = date.today()
            existing = Quiz.query.filter_by(quiz_date=today).first()

            if existing:
                logger.info(f"Quiz already exists for {today}")
                quiz = existing
            else:
                # Get user for adaptive quiz generation
                # Use the first authorized user, or the most recently active user
                authorized_emails = app.config.get('AUTHORIZED_EMAILS', [])
                user = None
                if authorized_emails:
                    # Try first authorized email
                    user = User.query.filter_by(email=authorized_emails[0]).first()
                if not user:
                    # Fall back to most recently active user
                    user = User.query.order_by(User.last_login.desc()).first()

                # Generate quiz
                generator = QuizGeneratorService()
                quiz = generator.generate_daily_quiz(user_id=user.id if user else None)
                logger.info(f"Generated quiz for {today}: {quiz.id}")

            # Send notification if not already sent
            if not quiz.notification_sent:
                notification_email = app.config.get('NOTIFICATION_EMAIL')
                base_url = app.config.get('BASE_URL')

                if notification_email and base_url:
                    try:
                        notifier = NotificationService()
                        quiz_url = f"{base_url}/quiz/{today.isoformat()}"
                        success = notifier.send_quiz_notification(notification_email, quiz_url)

                        if success:
                            quiz.notification_sent = True
                            db.session.commit()
                            logger.info("Email notification sent successfully")
                        else:
                            logger.error("Failed to send email notification")
                    except Exception as e:
                        logger.error(f"Notification error: {e}")
                else:
                    logger.warning("Notification email or base URL not configured")

            logger.info("Daily quiz generation completed successfully")

        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise


if __name__ == '__main__':
    main()
