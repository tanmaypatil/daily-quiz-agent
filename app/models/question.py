from app.extensions import db


# CLAT categories
CATEGORIES = [
    'Constitutional Law',
    'Legal Reasoning',
    'Logical Reasoning',
    'English Comprehension',
    'Current Affairs & Legal GK',
    'Quantitative Techniques'
]

DIFFICULTIES = ['easy', 'medium', 'hard']


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)  # 1-10
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # A, B, C, or D
    explanation = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)  # easy, medium, hard

    # Relationships
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    def __repr__(self):
        return f'<Question {self.quiz_id}-{self.question_number}>'

    def to_dict(self, include_answer=False):
        data = {
            'id': self.id,
            'number': self.question_number,
            'text': self.question_text,
            'options': {
                'A': self.option_a,
                'B': self.option_b,
                'C': self.option_c,
                'D': self.option_d
            },
            'category': self.category,
            'difficulty': self.difficulty
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
            data['explanation'] = self.explanation
        return data
