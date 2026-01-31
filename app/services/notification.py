"""
Notification Service
Send email notifications via Gmail SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


class NotificationService:
    """Send email notifications via Gmail SMTP"""

    def __init__(self):
        self.smtp_email = current_app.config['SMTP_EMAIL']
        self.smtp_password = current_app.config['SMTP_PASSWORD']

        if not self.smtp_email or not self.smtp_password:
            raise ValueError("Gmail SMTP credentials not configured")

    def send_quiz_notification(self, to_email: str, quiz_url: str) -> bool:
        """Send daily quiz notification via email"""
        subject = "Daily CLAT Quiz Ready"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Good morning!</h2>
            <p>Your daily CLAT quiz is ready.</p>
            <p><a href="{quiz_url}" style="display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">Take Today's Quiz</a></p>
            <p style="color: #666;">10 questions, 6 minutes. Let's keep the streak going!</p>
        </body>
        </html>
        """

        text_body = f"""Good morning!

Your daily CLAT quiz is ready.

Take today's quiz: {quiz_url}

10 questions, 6 minutes. Let's keep the streak going!
"""

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_email
            msg['To'] = to_email

            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)

            current_app.logger.info(f"Email notification sent to {to_email}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to send email notification: {e}")
            return False

    def send_results_notification(self, to_email: str, score: int, total: int) -> bool:
        """Send quiz completion notification"""
        percentage = round(score / total * 100)

        if percentage >= 80:
            message = "Excellent work!"
        elif percentage >= 60:
            message = "Good job!"
        else:
            message = "Keep practicing!"

        subject = f"Quiz Complete: {score}/{total} ({percentage}%)"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Quiz completed!</h2>
            <p style="font-size: 24px; font-weight: bold;">Score: {score}/{total} ({percentage}%)</p>
            <p style="font-size: 18px;">{message}</p>
            <p style="color: #666;">Check your detailed results in the app.</p>
        </body>
        </html>
        """

        text_body = f"""Quiz completed!

Score: {score}/{total} ({percentage}%)
{message}

Check your detailed results in the app.
"""

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_email
            msg['To'] = to_email

            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)

            return True

        except Exception as e:
            current_app.logger.error(f"Failed to send results notification: {e}")
            return False
