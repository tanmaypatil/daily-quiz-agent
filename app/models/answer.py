from app.extensions import db


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_answer = db.Column(db.String(1))  # A, B, C, D, or None if not answered
    is_correct = db.Column(db.Boolean, default=False)
    time_spent_seconds = db.Column(db.Integer)

    def __repr__(self):
        return f'<Answer {self.submission_id}-{self.question_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'selected_answer': self.selected_answer,
            'is_correct': self.is_correct,
            'time_spent_seconds': self.time_spent_seconds
        }
