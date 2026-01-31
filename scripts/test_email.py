#!/usr/bin/env python
"""Test email notification"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.services.notification import NotificationService

app = create_app()
with app.app_context():
    try:
        notifier = NotificationService()
        to_email = app.config.get('NOTIFICATION_EMAIL')
        print(f"Sending test email to: {to_email}")
        success = notifier.send_quiz_notification(to_email, 'https://quiz.germanwakad.click/quiz/test')
        print('Email sent!' if success else 'Failed to send email')
    except Exception as e:
        print(f"Error: {e}")
