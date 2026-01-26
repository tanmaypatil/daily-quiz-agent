"""
Tests for Analytics Service
"""
import pytest
from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Quiz, Question, Submission, Answer
from app.services.analytics import AnalyticsService


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret'
    GOOGLE_CLIENT_ID = 'test'
    GOOGLE_CLIENT_SECRET = 'test'


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_data(app):
    """Create sample user, quiz, and answers"""
    with app.app_context():
        # Create user
        user = User(
            google_id='test123',
            email='test@example.com',
            name='Test User'
        )
        db.session.add(user)

        # Create quiz
        quiz = Quiz(
            quiz_date=date.today(),
            passage='Test passage content'
        )
        db.session.add(quiz)
        db.session.flush()

        # Create questions
        categories = ['Constitutional Law', 'Legal Reasoning', 'Logical Reasoning']
        for i in range(1, 4):
            q = Question(
                quiz_id=quiz.id,
                question_number=i,
                question_text=f'Question {i}?',
                option_a='A',
                option_b='B',
                option_c='C',
                option_d='D',
                correct_answer='A',
                explanation='Because A',
                category=categories[i-1],
                difficulty='medium'
            )
            db.session.add(q)

        db.session.flush()

        # Create submission
        submission = Submission(
            user_id=user.id,
            quiz_id=quiz.id,
            completed=True,
            score=2
        )
        db.session.add(submission)
        db.session.flush()

        # Create answers
        questions = Question.query.all()
        for i, q in enumerate(questions):
            answer = Answer(
                submission_id=submission.id,
                question_id=q.id,
                selected_answer='A' if i < 2 else 'B',
                is_correct=i < 2,
                time_spent_seconds=30
            )
            db.session.add(answer)

        db.session.commit()

        return {'user': user, 'quiz': quiz}


def test_get_category_performance(app, sample_data):
    """Test category performance calculation"""
    with app.app_context():
        user = User.query.first()
        service = AnalyticsService(user.id)
        performance = service.get_category_performance()

        assert 'Constitutional Law' in performance
        assert 'Legal Reasoning' in performance
        assert performance['Constitutional Law']['accuracy'] == 100.0
        assert performance['Logical Reasoning']['accuracy'] == 0.0


def test_get_weak_areas(app, sample_data):
    """Test weak area identification"""
    with app.app_context():
        user = User.query.first()
        service = AnalyticsService(user.id)
        weak = service.get_weak_areas(threshold=60.0)

        # Logical Reasoning should be identified as weak (0% accuracy)
        weak_categories = [w['category'] for w in weak]
        assert 'Logical Reasoning' in weak_categories


def test_get_overall_stats(app, sample_data):
    """Test overall statistics"""
    with app.app_context():
        user = User.query.first()
        service = AnalyticsService(user.id)
        stats = service.get_overall_stats()

        assert stats['quizzes_taken'] == 1
