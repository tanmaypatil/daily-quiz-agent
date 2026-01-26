from datetime import datetime
from app.extensions import db


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    total_time_seconds = db.Column(db.Integer)
    score = db.Column(db.Integer)  # Number of correct answers
    completed = db.Column(db.Boolean, default=False)

    # Relationships
    answers = db.relationship('Answer', backref='submission', lazy='dynamic')

    def __repr__(self):
        return f'<Submission {self.user_id}-{self.quiz_id}>'

    def calculate_score(self):
        """Calculate and update the score based on answers"""
        correct_count = self.answers.filter_by(is_correct=True).count()
        self.score = correct_count
        return correct_count

    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'total_time_seconds': self.total_time_seconds,
            'score': self.score,
            'completed': self.completed
        }
