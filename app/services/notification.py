"""
Notification Service
Send WhatsApp notifications via Twilio
"""
from flask import current_app
from twilio.rest import Client


class NotificationService:
    """Send WhatsApp notifications via Twilio"""

    def __init__(self):
        account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        auth_token = current_app.config['TWILIO_AUTH_TOKEN']

        if not account_sid or not auth_token:
            raise ValueError("Twilio credentials not configured")

        self.client = Client(account_sid, auth_token)
        self.from_number = current_app.config['TWILIO_WHATSAPP_FROM']

    def send_quiz_notification(self, to_number: str, quiz_url: str) -> bool:
        """Send daily quiz notification via WhatsApp"""
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'

        message_body = f"""Good morning! Your daily CLAT quiz is ready.

Take today's quiz: {quiz_url}

10 questions, 6 minutes. Let's keep the streak going!"""

        try:
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )
            current_app.logger.info(f"WhatsApp notification sent: {message.sid}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp notification: {e}")
            return False

    def send_results_notification(self, to_number: str, score: int, total: int) -> bool:
        """Send quiz completion notification"""
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'

        percentage = round(score / total * 100)

        if percentage >= 80:
            emoji = "Excellent work!"
        elif percentage >= 60:
            emoji = "Good job!"
        else:
            emoji = "Keep practicing!"

        message_body = f"""Quiz completed!

Score: {score}/{total} ({percentage}%)
{emoji}

Check your detailed results in the app."""

        try:
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to send results notification: {e}")
            return False
