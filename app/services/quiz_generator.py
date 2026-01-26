"""
Quiz Generator Service
Uses Claude API to generate adaptive quizzes based on performance analytics
"""
import json
import anthropic
from datetime import date
from flask import current_app

from app.extensions import db
from app.models import Quiz, Question, User
from app.models.question import CATEGORIES
from app.services.analytics import AnalyticsService


class QuizGeneratorService:
    """Generate adaptive CLAT quizzes using Claude API"""

    def __init__(self):
        api_key = current_app.config['ANTHROPIC_API_KEY']
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_daily_quiz(self, user_id: int = None) -> Quiz:
        """Generate quiz for today based on user's performance"""
        today = date.today()

        # Check if quiz already exists for today
        existing = Quiz.query.filter_by(quiz_date=today).first()
        if existing:
            return existing

        # Get analytics if user provided
        analytics = None
        if user_id:
            user = User.query.get(user_id)
            if user:
                analytics_service = AnalyticsService(user_id)
                analytics = analytics_service.get_performance_summary()

        # Build and execute prompt
        prompt = self._build_prompt(analytics)
        quiz_data = self._call_claude(prompt)

        # Create quiz and questions
        quiz = self._save_quiz(today, quiz_data, prompt)

        return quiz

    def _build_prompt(self, analytics: dict = None) -> str:
        """Build adaptive prompt based on performance analytics"""

        # Base prompt
        prompt = """You are a CLAT (Common Law Admission Test) exam preparation expert. Generate a quiz with a single reading comprehension passage followed by 10 multiple-choice questions.

## CLAT Exam Context
CLAT tests:
- Constitutional Law
- Legal Reasoning
- Logical Reasoning
- English Comprehension
- Current Affairs & Legal GK
- Quantitative Techniques

## Quiz Requirements
1. Create ONE cohesive passage (300-500 words) that can support questions from multiple categories
2. The passage should be about a legal topic, case, or current affairs related to law or a quuantitative scenario relevant to CLAT
3. Friday and Sunday quizzes should focus on quantitative techniques and logical reasoning
4. Generate exactly 10 questions based on the passage
4. Each question should have 4 options (A, B, C, D)
5. Provide detailed explanations for each answer

## Question Distribution
"""

        if analytics and analytics.get('weak_areas'):
            weak_areas = analytics['weak_areas']
            weak_categories = [w['category'] for w in weak_areas[:3]]

            prompt += f"""
Based on the student's performance data:
- Weak areas (needs more practice): {', '.join(weak_categories)}
- Focus 6 questions on weak areas
- Include 4 questions from other categories for balanced practice

Student Performance Summary:
"""
            for category, stats in analytics.get('category_performance', {}).items():
                if stats['total'] > 0:
                    prompt += f"- {category}: {stats['accuracy']}% accuracy ({stats['total']} questions)\n"

            if analytics.get('time_struggles'):
                prompt += "\nTime management issues in: "
                prompt += ', '.join([t['category'] for t in analytics['time_struggles']])
                prompt += "\nInclude some straightforward questions in these areas to build confidence.\n"

            if analytics.get('recent_trends', {}).get('trend') == 'declining':
                prompt += "\nRecent performance is declining - include more medium difficulty questions.\n"
            elif analytics.get('recent_trends', {}).get('trend') == 'improving':
                prompt += "\nStudent is improving - can include some challenging questions.\n"

        else:
            # No analytics - balanced distribution
            prompt += """
- Distribute questions evenly across categories
- Mix of easy (3), medium (5), and hard (2) difficulty
- This is the first quiz or no performance data available
"""

        prompt += """
## Difficulty Guidelines
- Easy: Direct comprehension, simple recall
- Medium: Requires inference, application of concepts
- Hard: Complex reasoning, multiple steps, nuanced understanding

## Output Format
Return ONLY valid JSON in this exact format:
```json
{
  "passage": "The comprehension passage text here...",
  "questions": [
    {
      "number": 1,
      "text": "Question text here?",
      "options": {
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      },
      "correct": "B",
      "explanation": "Detailed explanation of why B is correct...",
      "category": "Legal Reasoning",
      "difficulty": "medium"
    }
  ]
}
```

Generate the quiz now. Remember:
- Passage must be engaging and legally relevant
- Questions should test understanding, not just memory
- Explanations should be educational
- Categories must be from: Constitutional Law, Legal Reasoning, Logical Reasoning, English Comprehension, Current Affairs & Legal GK, Quantitative Techniques
- Difficulty must be: easy, medium, or hard
"""

        return prompt

    def _call_claude(self, prompt: str) -> dict:
        """Call Claude API and parse response"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text content
        content = response.content[0].text

        # Parse JSON from response (handle markdown code blocks)
        if '```json' in content:
            json_start = content.find('```json') + 7
            json_end = content.find('```', json_start)
            content = content[json_start:json_end]
        elif '```' in content:
            json_start = content.find('```') + 3
            json_end = content.find('```', json_start)
            content = content[json_start:json_end]

        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse Claude response: {e}")
            current_app.logger.error(f"Response content: {content[:500]}")
            raise ValueError("Failed to parse quiz data from Claude response")

    def _save_quiz(self, quiz_date: date, quiz_data: dict, prompt: str) -> Quiz:
        """Save quiz and questions to database"""
        quiz = Quiz(
            quiz_date=quiz_date,
            passage=quiz_data['passage'],
            generation_prompt=prompt
        )
        db.session.add(quiz)
        db.session.flush()  # Get quiz.id

        for q in quiz_data['questions']:
            question = Question(
                quiz_id=quiz.id,
                question_number=q['number'],
                question_text=q['text'],
                option_a=q['options']['A'],
                option_b=q['options']['B'],
                option_c=q['options']['C'],
                option_d=q['options']['D'],
                correct_answer=q['correct'],
                explanation=q['explanation'],
                category=q['category'],
                difficulty=q['difficulty']
            )
            db.session.add(question)

        db.session.commit()
        return quiz
