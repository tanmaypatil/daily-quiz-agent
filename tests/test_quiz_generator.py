"""
Tests for Quiz Generator Service
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import date
from app import create_app
from app.extensions import db
from app.models import Quiz, Question


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret'
    GOOGLE_CLIENT_ID = 'test'
    GOOGLE_CLIENT_SECRET = 'test'
    ANTHROPIC_API_KEY = 'test-key'


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def mock_claude_response():
    """Sample Claude API response"""
    return {
        "passage": "Test passage about constitutional law...",
        "questions": [
            {
                "number": 1,
                "text": "What is the supreme law of the land?",
                "options": {
                    "A": "Constitution",
                    "B": "Parliament",
                    "C": "Supreme Court",
                    "D": "President"
                },
                "correct": "A",
                "explanation": "The Constitution is the supreme law.",
                "category": "Constitutional Law",
                "difficulty": "easy"
            }
        ]
    }


def test_build_prompt_without_analytics(app):
    """Test prompt building without analytics data"""
    with app.app_context():
        from app.services.quiz_generator import QuizGeneratorService

        with patch('app.services.quiz_generator.anthropic'):
            service = QuizGeneratorService()
            prompt = service._build_prompt(None)

            assert 'CLAT' in prompt
            assert 'Constitutional Law' in prompt
            assert '10 questions' in prompt


def test_build_prompt_with_analytics(app):
    """Test prompt building with analytics data"""
    with app.app_context():
        from app.services.quiz_generator import QuizGeneratorService

        analytics = {
            'category_performance': {
                'Constitutional Law': {'total': 5, 'correct': 2, 'accuracy': 40.0},
                'Legal Reasoning': {'total': 5, 'correct': 5, 'accuracy': 100.0}
            },
            'weak_areas': [
                {'category': 'Constitutional Law', 'accuracy': 40.0, 'attempts': 5}
            ],
            'time_struggles': [],
            'recent_trends': {'trend': 'stable'}
        }

        with patch('app.services.quiz_generator.anthropic'):
            service = QuizGeneratorService()
            prompt = service._build_prompt(analytics)

            assert 'Constitutional Law' in prompt
            assert 'weak areas' in prompt.lower() or 'Weak areas' in prompt


def test_save_quiz(app, mock_claude_response):
    """Test saving quiz to database"""
    with app.app_context():
        from app.services.quiz_generator import QuizGeneratorService

        with patch('app.services.quiz_generator.anthropic'):
            service = QuizGeneratorService()
            quiz = service._save_quiz(date.today(), mock_claude_response, "test prompt")

            assert quiz.id is not None
            assert quiz.passage == mock_claude_response['passage']

            questions = list(quiz.questions)
            assert len(questions) == 1
            assert questions[0].correct_answer == 'A'
