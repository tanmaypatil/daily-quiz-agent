/**
 * Quiz Timer and Answer Tracking
 */

class QuizManager {
    constructor(quizId, timeLimit) {
        this.quizId = quizId;
        this.timeLimit = timeLimit;
        this.submissionId = null;
        this.startTime = null;
        this.remainingSeconds = timeLimit;
        this.questionStartTimes = {};
        this.currentQuestion = null;
        this.timerInterval = null;
        this.answers = {};

        this.init();
    }

    async init() {
        // Start the quiz
        await this.startQuiz();

        // Set up event listeners
        this.setupEventListeners();

        // Start timer
        this.startTimer();

        // Track initial question
        this.trackQuestionFocus(1);
    }

    async startQuiz() {
        try {
            const response = await fetch(`/api/quiz/${this.quizId}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (response.ok) {
                this.submissionId = data.submission_id;
                this.remainingSeconds = data.remaining_seconds;
                document.getElementById('submission-id').value = this.submissionId;
                this.startTime = new Date();
            } else {
                if (data.submission_id) {
                    // Already completed
                    window.location.href = `/results/${data.submission_id}`;
                }
                console.error('Failed to start quiz:', data.error);
            }
        } catch (error) {
            console.error('Error starting quiz:', error);
        }
    }

    setupEventListeners() {
        // Track answer selections
        document.querySelectorAll('.option input[type="radio"]').forEach(input => {
            input.addEventListener('change', (e) => this.handleAnswerSelect(e));
        });

        // Track question visibility (for time tracking)
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const questionNum = entry.target.dataset.questionNumber;
                    this.trackQuestionFocus(parseInt(questionNum));
                }
            });
        }, { threshold: 0.5 });

        document.querySelectorAll('.question-card').forEach(card => {
            observer.observe(card);
        });

        // Form submission
        document.getElementById('quiz-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitQuiz();
        });
    }

    trackQuestionFocus(questionNumber) {
        const now = Date.now();

        // Record time spent on previous question
        if (this.currentQuestion && this.currentQuestion !== questionNumber) {
            const prevStart = this.questionStartTimes[this.currentQuestion];
            if (prevStart) {
                const timeSpent = Math.floor((now - prevStart) / 1000);
                this.updateQuestionTime(this.currentQuestion, timeSpent);
            }
        }

        // Start tracking new question
        this.currentQuestion = questionNumber;
        if (!this.questionStartTimes[questionNumber]) {
            this.questionStartTimes[questionNumber] = now;
        }
    }

    updateQuestionTime(questionNumber, additionalTime) {
        const questionCard = document.querySelector(
            `.question-card[data-question-number="${questionNumber}"]`
        );
        if (!questionCard) return;

        const questionId = questionCard.dataset.questionId;
        if (!this.answers[questionId]) {
            this.answers[questionId] = { timeSpent: 0 };
        }
        this.answers[questionId].timeSpent += additionalTime;
    }

    async handleAnswerSelect(event) {
        const input = event.target;
        const questionCard = input.closest('.question-card');
        const questionId = questionCard.dataset.questionId;
        const selectedAnswer = input.value;

        // Calculate time spent on this question
        const questionNum = parseInt(questionCard.dataset.questionNumber);
        const startTime = this.questionStartTimes[questionNum];
        const timeSpent = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;

        // Store answer locally
        if (!this.answers[questionId]) {
            this.answers[questionId] = { timeSpent: 0 };
        }
        this.answers[questionId].selected = selectedAnswer;
        this.answers[questionId].timeSpent += timeSpent;

        // Reset start time for this question
        this.questionStartTimes[questionNum] = Date.now();

        // Save to server
        try {
            await fetch(`/api/quiz/${this.quizId}/answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    submission_id: this.submissionId,
                    question_id: parseInt(questionId),
                    selected_answer: selectedAnswer,
                    time_spent_seconds: this.answers[questionId].timeSpent
                })
            });
        } catch (error) {
            console.error('Error saving answer:', error);
        }

        // Update answered count
        this.updateAnsweredCount();
    }

    updateAnsweredCount() {
        const answered = document.querySelectorAll('.option input[type="radio"]:checked').length;
        document.getElementById('answered-count').textContent = answered;
    }

    startTimer() {
        this.updateTimerDisplay();

        this.timerInterval = setInterval(() => {
            this.remainingSeconds--;

            if (this.remainingSeconds <= 0) {
                clearInterval(this.timerInterval);
                this.submitQuiz(true);
                return;
            }

            this.updateTimerDisplay();
        }, 1000);
    }

    updateTimerDisplay() {
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        const timerValue = document.getElementById('timer-value');
        const timer = document.getElementById('timer');

        timerValue.textContent = display;

        // Update timer styling based on remaining time
        timer.classList.remove('warning', 'danger');
        if (this.remainingSeconds <= 60) {
            timer.classList.add('danger');
        } else if (this.remainingSeconds <= 120) {
            timer.classList.add('warning');
        }
    }

    async submitQuiz(autoSubmit = false) {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }

        // Save any pending question time
        if (this.currentQuestion) {
            const startTime = this.questionStartTimes[this.currentQuestion];
            if (startTime) {
                const timeSpent = Math.floor((Date.now() - startTime) / 1000);
                this.updateQuestionTime(this.currentQuestion, timeSpent);
            }
        }

        // Disable submit button
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = autoSubmit ? 'Time\'s up! Submitting...' : 'Submitting...';

        try {
            const response = await fetch(`/api/quiz/${this.quizId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    submission_id: this.submissionId
                })
            });

            const data = await response.json();

            if (response.ok && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                console.error('Submit failed:', data.error);
                alert('Failed to submit quiz. Please try again.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Quiz';
            }
        } catch (error) {
            console.error('Error submitting quiz:', error);
            alert('Failed to submit quiz. Please try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Quiz';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof QUIZ_ID !== 'undefined' && typeof TIME_LIMIT !== 'undefined') {
        window.quizManager = new QuizManager(QUIZ_ID, TIME_LIMIT);
    }
});
