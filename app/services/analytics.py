"""
Analytics Service
Calculates performance metrics for adaptive quiz generation
"""
from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import User, Quiz, Question, Submission, Answer
from app.models.question import CATEGORIES


class AnalyticsService:
    """Calculate user performance analytics for adaptive quiz generation"""

    def __init__(self, user_id: int, days: int = 7):
        self.user_id = user_id
        self.days = days
        self.start_date = date.today() - timedelta(days=days)

    def get_performance_summary(self) -> dict:
        """Get complete performance summary for prompt building"""
        return {
            'category_performance': self.get_category_performance(),
            'difficulty_performance': self.get_difficulty_performance(),
            'weak_areas': self.get_weak_areas(),
            'time_struggles': self.get_time_struggles(),
            'recent_trends': self.get_recent_trends(),
            'overall_stats': self.get_overall_stats()
        }

    def get_category_performance(self) -> dict:
        """Calculate accuracy per category over the time period"""
        # Join through submission to get user's answers
        results = db.session.query(
            Question.category,
            func.count(Answer.id).label('total'),
            func.sum(func.cast(Answer.is_correct, db.Integer)).label('correct')
        ).join(
            Answer, Answer.question_id == Question.id
        ).join(
            Submission, Submission.id == Answer.submission_id
        ).join(
            Quiz, Quiz.id == Question.quiz_id
        ).filter(
            Submission.user_id == self.user_id,
            Submission.completed == True,
            Quiz.quiz_date >= self.start_date
        ).group_by(Question.category).all()

        performance = {}
        for category, total, correct in results:
            correct = correct or 0
            accuracy = (correct / total * 100) if total > 0 else 0
            performance[category] = {
                'total': total,
                'correct': correct,
                'accuracy': round(accuracy, 1)
            }

        # Add categories with no attempts
        for cat in CATEGORIES:
            if cat not in performance:
                performance[cat] = {'total': 0, 'correct': 0, 'accuracy': 0}

        return performance

    def get_difficulty_performance(self) -> dict:
        """Calculate accuracy per difficulty level"""
        results = db.session.query(
            Question.difficulty,
            func.count(Answer.id).label('total'),
            func.sum(func.cast(Answer.is_correct, db.Integer)).label('correct')
        ).join(
            Answer, Answer.question_id == Question.id
        ).join(
            Submission, Submission.id == Answer.submission_id
        ).join(
            Quiz, Quiz.id == Question.quiz_id
        ).filter(
            Submission.user_id == self.user_id,
            Submission.completed == True,
            Quiz.quiz_date >= self.start_date
        ).group_by(Question.difficulty).all()

        performance = {}
        for difficulty, total, correct in results:
            correct = correct or 0
            accuracy = (correct / total * 100) if total > 0 else 0
            performance[difficulty] = {
                'total': total,
                'correct': correct,
                'accuracy': round(accuracy, 1)
            }

        return performance

    def get_weak_areas(self, threshold: float = 60.0) -> list:
        """Get categories where accuracy is below threshold"""
        category_perf = self.get_category_performance()

        weak = []
        for category, stats in category_perf.items():
            if stats['total'] > 0 and stats['accuracy'] < threshold:
                weak.append({
                    'category': category,
                    'accuracy': stats['accuracy'],
                    'attempts': stats['total']
                })

        # Sort by accuracy (worst first)
        weak.sort(key=lambda x: x['accuracy'])
        return weak

    def get_time_struggles(self) -> list:
        """Find categories where user is slow AND has low accuracy"""
        # Average time per question by category
        results = db.session.query(
            Question.category,
            func.avg(Answer.time_spent_seconds).label('avg_time'),
            func.avg(func.cast(Answer.is_correct, db.Float)).label('accuracy')
        ).join(
            Answer, Answer.question_id == Question.id
        ).join(
            Submission, Submission.id == Answer.submission_id
        ).join(
            Quiz, Quiz.id == Question.quiz_id
        ).filter(
            Submission.user_id == self.user_id,
            Submission.completed == True,
            Quiz.quiz_date >= self.start_date,
            Answer.time_spent_seconds.isnot(None)
        ).group_by(Question.category).all()

        # Find categories with above-average time and below-average accuracy
        if not results:
            return []

        avg_time_overall = sum(r[1] or 0 for r in results) / len(results) if results else 36
        avg_accuracy_overall = sum(r[2] or 0 for r in results) / len(results) if results else 0.5

        struggles = []
        for category, avg_time, accuracy in results:
            avg_time = avg_time or 0
            accuracy = accuracy or 0
            if avg_time > avg_time_overall and accuracy < avg_accuracy_overall:
                struggles.append({
                    'category': category,
                    'avg_time_seconds': round(avg_time, 1),
                    'accuracy': round(accuracy * 100, 1)
                })

        return struggles

    def get_recent_trends(self) -> dict:
        """Compare recent performance to earlier period"""
        midpoint = date.today() - timedelta(days=self.days // 2)

        def get_period_accuracy(start, end):
            result = db.session.query(
                func.count(Answer.id).label('total'),
                func.sum(func.cast(Answer.is_correct, db.Integer)).label('correct')
            ).join(
                Submission, Submission.id == Answer.submission_id
            ).join(
                Quiz, Quiz.id == Submission.quiz_id
            ).filter(
                Submission.user_id == self.user_id,
                Submission.completed == True,
                Quiz.quiz_date >= start,
                Quiz.quiz_date < end
            ).first()

            total, correct = result
            if total and total > 0:
                return round((correct or 0) / total * 100, 1)
            return None

        earlier = get_period_accuracy(self.start_date, midpoint)
        recent = get_period_accuracy(midpoint, date.today() + timedelta(days=1))

        trend = 'stable'
        if earlier is not None and recent is not None:
            diff = recent - earlier
            if diff > 5:
                trend = 'improving'
            elif diff < -5:
                trend = 'declining'

        return {
            'earlier_accuracy': earlier,
            'recent_accuracy': recent,
            'trend': trend
        }

    def get_overall_stats(self) -> dict:
        """Get overall statistics"""
        result = db.session.query(
            func.count(Submission.id).label('quizzes_taken'),
            func.avg(Submission.score).label('avg_score'),
            func.avg(Submission.total_time_seconds).label('avg_time')
        ).filter(
            Submission.user_id == self.user_id,
            Submission.completed == True,
            Submission.submitted_at >= self.start_date
        ).first()

        quizzes, avg_score, avg_time = result
        return {
            'quizzes_taken': quizzes or 0,
            'average_score': round(avg_score, 1) if avg_score else 0,
            'average_time_seconds': round(avg_time, 0) if avg_time else 0
        }
