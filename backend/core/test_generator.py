
"""
Test Generator Module
Handles generation and management of mock tests for different subjects.
"""
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generates and manages mock tests for different subjects."""

    def __init__(self):
        self.subjects = {}  # Maps subject names to their questions
        self.active_tests = {}  # Maps test IDs to test data

    def categorize_questions_by_subject(self, questions: List[str]) -> Dict[str, List[str]]:
        """
        Categorize questions into subjects based on keywords and patterns.

        Args:
            questions: List of question strings

        Returns:
            Dictionary mapping subject names to lists of questions
        """
        subject_keywords = {
            'Mathematics': ['calculate', 'solve', 'equation', 'mathematics', 'algebra', 
                          'geometry', 'calculus', 'statistics', 'probability', 'number',
                          'function', 'graph', 'angle', 'triangle', 'circle', 'area', 
                          'volume', 'derivative', 'integral'],
            'Science': ['science', 'physics', 'chemistry', 'biology', 'atom', 'molecule',
                       'cell', 'organism', 'force', 'energy', 'reaction', 'element',
                       'experiment', 'hypothesis', 'theory', 'law', 'motion', 'gravity'],
            'Social Science': ['history', 'geography', 'economics', 'political', 'social',
                             'government', 'democracy', 'society', 'culture', 'religion',
                             'war', 'revolution', 'civilization', 'population', 'trade'],
            'English': ['literature', 'poetry', 'novel', 'drama', 'grammar', 'vocabulary',
                       'comprehension', 'essay', 'writing', 'author', 'poet', 'story'],
            'Computer Science': ['computer', 'programming', 'algorithm', 'data structure',
                               'software', 'hardware', 'network', 'database', 'code',
                               'language', 'system', 'artificial intelligence']
        }

        categorized = {subject: [] for subject in subject_keywords}
        categorized['General'] = []  # For questions that don't fit specific subjects

        for question in questions:
            question_lower = question.lower()
            matched = False

            # Check each subject's keywords
            for subject, keywords in subject_keywords.items():
                if any(keyword in question_lower for keyword in keywords):
                    categorized[subject].append(question)
                    matched = True
                    break

            # If no match, add to General
            if not matched:
                categorized['General'].append(question)

        # Remove empty subjects
        self.subjects = {k: v for k, v in categorized.items() if v}

        logger.info(f"Categorized {len(questions)} questions into {len(self.subjects)} subjects")
        for subject, qs in self.subjects.items():
            logger.info(f"  - {subject}: {len(qs)} questions")

        return self.subjects

    def generate_test(self, 
                     subject: str, 
                     num_questions: int = 10,
                     difficulty: Optional[str] = None) -> Dict:
        """
        Generate a mock test for a specific subject.

        Args:
            subject: Name of the subject
            num_questions: Number of questions to include (default: 10)
            difficulty: Optional difficulty level ('easy', 'medium', 'hard')

        Returns:
            Dictionary containing test information and questions
        """
        if subject not in self.subjects:
            raise ValueError(f"Subject '{subject}' not found. Available subjects: {list(self.subjects.keys())}")

        available_questions = self.subjects[subject]

        if num_questions > len(available_questions):
            logger.warning(f"Requested {num_questions} questions but only {len(available_questions)} available")
            num_questions = len(available_questions)

        # Select random questions
        selected_questions = random.sample(available_questions, num_questions)

        # Generate test ID
        test_id = f"{subject.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create test data
        test_data = {
            'test_id': test_id,
            'subject': subject,
            'difficulty': difficulty or 'mixed',
            'created_at': datetime.now().isoformat(),
            'questions': [
                {
                    'id': i,
                    'question': q,
                    'max_marks': 5,  # Default marks per question
                    'student_answer': None,
                    'evaluation': None
                }
                for i, q in enumerate(selected_questions)
            ],
            'total_marks': num_questions * 5,
            'status': 'pending'
        }

        # Store test
        self.active_tests[test_id] = test_data

        logger.info(f"Generated test {test_id} for {subject} with {num_questions} questions")
        return test_data

    def get_available_subjects(self) -> List[str]:
        """Get list of available subjects with questions."""
        return list(self.subjects.keys())

    def get_subject_stats(self) -> Dict[str, int]:
        """Get statistics about questions per subject."""
        return {subject: len(questions) for subject, questions in self.subjects.items()}

    def get_test(self, test_id: str) -> Optional[Dict]:
        """Retrieve a test by its ID."""
        return self.active_tests.get(test_id)

    def submit_answer(self, 
                     test_id: str, 
                     question_id: int, 
                     answer: str) -> Dict:
        """
        Submit an answer for a specific question in a test.

        Args:
            test_id: ID of the test
            question_id: ID of the question within the test
            answer: Student's answer

        Returns:
            Updated test data
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        if question_id < 0 or question_id >= len(test['questions']):
            raise ValueError(f"Invalid question ID: {question_id}")

        # Store the answer
        test['questions'][question_id]['student_answer'] = answer
        test['status'] = 'in_progress'

        return test

    def submit_all_answers(self, 
                          test_id: str, 
                          answers: List[Dict]) -> Dict:
        """
        Submit all answers for a test at once.

        Args:
            test_id: ID of the test
            answers: List of dictionaries with 'question_id' and 'answer'

        Returns:
            Updated test data with evaluations
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        # Process each answer
        for answer_data in answers:
            q_id = answer_data['question_id']
            answer = answer_data['answer']

            if q_id < 0 or q_id >= len(test['questions']):
                logger.warning(f"Skipping invalid question ID: {q_id}")
                continue

            test['questions'][q_id]['student_answer'] = answer

        test['status'] = 'submitted'

        return test

    def calculate_test_score(self, test_id: str) -> Dict:
        """
        Calculate the total score for a completed test.

        Args:
            test_id: ID of the test

        Returns:
            Dictionary with score breakdown and feedback
        """
        test = self.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        if test['status'] != 'submitted':
            raise ValueError(f"Test {test_id} has not been submitted yet")

        total_score = 0
        total_max = 0
        question_results = []

        for q in test['questions']:
            if q['evaluation']:
                total_score += q['evaluation'].get('score', 0)
                total_max += q['evaluation'].get('max_marks', q['max_marks'])

                question_results.append({
                    'question_id': q['id'],
                    'question': q['question'],
                    'score': q['evaluation'].get('score', 0),
                    'max_marks': q['evaluation'].get('max_marks', q['max_marks']),
                    'feedback': q['evaluation'].get('feedback', '')
                })

        percentage = (total_score / total_max * 100) if total_max > 0 else 0

        # Generate overall feedback
        if percentage >= 80:
            overall_feedback = "Excellent performance! You have a strong understanding of the subject."
        elif percentage >= 60:
            overall_feedback = "Good performance! Continue practicing to improve further."
        elif percentage >= 40:
            overall_feedback = "Satisfactory performance. Review the topics where you scored lower."
        else:
            overall_feedback = "Needs improvement. We recommend reviewing the study material and retaking the test."

        return {
            'test_id': test_id,
            'subject': test['subject'],
            'total_score': total_score,
            'total_max_marks': total_max,
            'percentage': round(percentage, 2),
            'overall_feedback': overall_feedback,
            'question_results': question_results,
            'completed_at': datetime.now().isoformat()
        }
