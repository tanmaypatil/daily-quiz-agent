"""
Quiz display routes
"""
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Quiz, Submission

quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/')
def index():
    """Redirect to today's quiz or login page"""
    if not current_user.is_authenticated:
        return render_template('login.html')

    # Get today's quiz
    today = date.today()
    quiz = Quiz.query.filter_by(quiz_date=today).first()

    if quiz:
        return redirect(url_for('quiz.take_quiz', quiz_date=today.isoformat()))

    # Check for most recent quiz if no quiz today
    quiz = Quiz.query.order_by(Quiz.quiz_date.desc()).first()
    if quiz:
        return redirect(url_for('quiz.take_quiz', quiz_date=quiz.quiz_date.isoformat()))

    return render_template('no_quiz.html')


@quiz_bp.route('/quiz/<quiz_date>')
@login_required
def take_quiz(quiz_date):
    """Display quiz for a specific date"""
    try:
        quiz_date_obj = date.fromisoformat(quiz_date)
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('quiz.index'))

    quiz = Quiz.query.filter_by(quiz_date=quiz_date_obj).first()
    if not quiz:
        flash('Quiz not found for this date.', 'error')
        return redirect(url_for('quiz.index'))

    # Check if user already completed this quiz
    existing_submission = Submission.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id,
        completed=True
    ).first()

    if existing_submission:
        return redirect(url_for('quiz.results', submission_id=existing_submission.id))

    # Check for in-progress submission
    in_progress = Submission.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id,
        completed=False
    ).first()

    time_limit = current_app.config['QUIZ_TIME_LIMIT_SECONDS']

    return render_template(
        'quiz.html',
        quiz=quiz,
        submission=in_progress,
        time_limit=time_limit
    )


@quiz_bp.route('/results/<int:submission_id>')
@login_required
def results(submission_id):
    """Display quiz results with explanations"""
    submission = Submission.query.get_or_404(submission_id)

    # Verify this submission belongs to current user
    if submission.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('quiz.index'))

    quiz = submission.quiz
    answers = {a.question_id: a for a in submission.answers}

    # Calculate category breakdown
    category_stats = {}
    for question in quiz.questions:
        cat = question.category
        if cat not in category_stats:
            category_stats[cat] = {'correct': 0, 'total': 0}
        category_stats[cat]['total'] += 1

        answer = answers.get(question.id)
        if answer and answer.is_correct:
            category_stats[cat]['correct'] += 1

    return render_template(
        'results.html',
        quiz=quiz,
        submission=submission,
        answers=answers,
        category_stats=category_stats
    )


@quiz_bp.route('/history')
@login_required
def history():
    """Show quiz history"""
    submissions = Submission.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).order_by(Submission.submitted_at.desc()).all()

    return render_template('history.html', submissions=submissions)
