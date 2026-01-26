from datetime import datetime
from app.extensions import db


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    quiz_date = db.Column(db.Date, unique=True, nullable=False)
    passage = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    generation_prompt = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, archived
    notification_sent = db.Column(db.Boolean, default=False)

    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy='dynamic',
                                order_by='Question.question_number')
    submissions = db.relationship('Submission', backref='quiz', lazy='dynamic')

    def __repr__(self):
        return f'<Quiz {self.quiz_date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'quiz_date': self.quiz_date.isoformat(),
            'passage': self.passage,
            'questions': [q.to_dict() for q in self.questions]
        }
