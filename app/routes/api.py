"""
API routes for quiz submission
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Quiz, Question, Submission, Answer

api_bp = Blueprint('api', __name__)


@api_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start a quiz, create submission record"""
    quiz = Quiz.query.get_or_404(quiz_id)

    # Check if already completed
    existing = Submission.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed=True
    ).first()

    if existing:
        return jsonify({'error': 'Quiz already completed', 'submission_id': existing.id}), 400

    # Check for in-progress submission
    in_progress = Submission.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed=False
    ).first()

    if in_progress:
        # Return existing in-progress submission
        elapsed = (datetime.utcnow() - in_progress.started_at).total_seconds()
        time_limit = current_app.config['QUIZ_TIME_LIMIT_SECONDS']
        remaining = max(0, time_limit - elapsed)

        return jsonify({
            'submission_id': in_progress.id,
            'started_at': in_progress.started_at.isoformat(),
            'remaining_seconds': int(remaining)
        })

    # Create new submission
    submission = Submission(
        user_id=current_user.id,
        quiz_id=quiz_id,
        started_at=datetime.utcnow()
    )
    db.session.add(submission)
    db.session.commit()

    time_limit = current_app.config['QUIZ_TIME_LIMIT_SECONDS']

    return jsonify({
        'submission_id': submission.id,
        'started_at': submission.started_at.isoformat(),
        'remaining_seconds': time_limit
    })


@api_bp.route('/quiz/<int:quiz_id>/answer', methods=['POST'])
@login_required
def save_answer(quiz_id):
    """Save an individual answer"""
    data = request.get_json()

    submission_id = data.get('submission_id')
    question_id = data.get('question_id')
    selected_answer = data.get('selected_answer')
    time_spent = data.get('time_spent_seconds', 0)

    if not all([submission_id, question_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Verify submission belongs to user and is not completed
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    if submission.completed:
        return jsonify({'error': 'Quiz already submitted'}), 400

    # Get question and verify it belongs to this quiz
    question = Question.query.get_or_404(question_id)
    if question.quiz_id != quiz_id:
        return jsonify({'error': 'Question does not belong to this quiz'}), 400

    # Check if answer already exists
    answer = Answer.query.filter_by(
        submission_id=submission_id,
        question_id=question_id
    ).first()

    is_correct = selected_answer == question.correct_answer if selected_answer else False

    if answer:
        # Update existing answer
        answer.selected_answer = selected_answer
        answer.is_correct = is_correct
        answer.time_spent_seconds = time_spent
    else:
        # Create new answer
        answer = Answer(
            submission_id=submission_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            time_spent_seconds=time_spent
        )
        db.session.add(answer)

    db.session.commit()

    return jsonify({'success': True, 'answer_id': answer.id})


@api_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    """Complete quiz submission"""
    data = request.get_json()
    submission_id = data.get('submission_id')

    if not submission_id:
        return jsonify({'error': 'Missing submission_id'}), 400

    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    if submission.completed:
        return jsonify({'error': 'Quiz already submitted'}), 400

    # Calculate total time
    now = datetime.utcnow()
    total_seconds = int((now - submission.started_at).total_seconds())

    # Update submission
    submission.submitted_at = now
    submission.total_time_seconds = total_seconds
    submission.completed = True
    submission.calculate_score()

    db.session.commit()

    return jsonify({
        'success': True,
        'score': submission.score,
        'total_questions': 10,
        'time_seconds': submission.total_time_seconds,
        'redirect_url': f'/results/{submission.id}'
    })


@api_bp.route('/quiz/<int:quiz_id>/data')
@login_required
def get_quiz_data(quiz_id):
    """Get quiz data as JSON"""
    quiz = Quiz.query.get_or_404(quiz_id)

    return jsonify({
        'id': quiz.id,
        'date': quiz.quiz_date.isoformat(),
        'passage': quiz.passage,
        'questions': [q.to_dict(include_answer=False) for q in quiz.questions]
    })
