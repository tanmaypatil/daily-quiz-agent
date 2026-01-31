#!/usr/bin/env python
"""List recent quizzes"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.models import Quiz

app = create_app()
with app.app_context():
    quizzes = Quiz.query.order_by(Quiz.quiz_date.desc()).limit(10).all()

    if not quizzes:
        print("No quizzes found")
    else:
        print(f"{'Date':<12} {'ID':<6} {'Questions':<10} {'Notified':<10}")
        print("-" * 40)
        for q in quizzes:
            question_count = len(q.questions) if q.questions else 0
            print(f"{q.quiz_date}   {q.id:<6} {question_count:<10} {q.notification_sent}")
