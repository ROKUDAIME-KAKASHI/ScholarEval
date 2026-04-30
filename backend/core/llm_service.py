import google.generativeai as genai
import time, random
from .config import GEMINI_API_KEY

class LLMService:

    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def evaluate(self, question: str, answer: str, context: str, max_marks: int) -> dict:
        """
        Evaluate a student's answer against a question.
        
        Args:
            question: The exam question
            answer: The student's answer
            context: Retrieved context/reference material
            max_marks: Maximum marks for this question
            
        Returns:
            Dictionary with score, feedback, points_hit, points_missed, and max_marks
        """
        if not answer or not answer.strip():
            return {
                "score": 0,
                "feedback": "No answer provided.",
                "points_hit": [],
                "points_missed": [],
                "max_marks": max_marks
            }

        # Simple keyword-based scoring if LLM unavailable
        if not self.model:
            return self._keyword_based_evaluation(question, answer, context, max_marks)

        try:
            prompt = f"""You are a strict CBSE examiner. Evaluate this answer.

Question: {question}
Answer: {answer}
{f'Reference Material: {context}' if context else ''}

Provide evaluation in this exact format:
SCORE: [0-{max_marks}]
FEEDBACK: [2-3 sentences]
CORRECT_POINTS: [comma-separated key points covered]
MISSING_POINTS: [comma-separated key points missed]
"""
            
            result = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0}
            )
            
            if not result or not result.text:
                return self._keyword_based_evaluation(question, answer, context, max_marks)
            
            # Parse response
            text = result.text.strip()
            lines = text.split('\n')
            
            score = max_marks // 2  # Default: half marks
            feedback = "Answer evaluated."
            points_hit = []
            points_missed = []
            
            for line in lines:
                if line.startswith("SCORE:"):
                    try:
                        score = min(max_marks, max(0, int(line.split(":")[-1].strip())))
                    except:
                        pass
                elif line.startswith("FEEDBACK:"):
                    feedback = line.split(":", 1)[-1].strip()
                elif line.startswith("CORRECT_POINTS:"):
                    points_hit = [p.strip() for p in line.split(":", 1)[-1].split(",") if p.strip()]
                elif line.startswith("MISSING_POINTS:"):
                    points_missed = [p.strip() for p in line.split(":", 1)[-1].split(",") if p.strip()]
            
            return {
                "score": score,
                "feedback": feedback,
                "points_hit": points_hit,
                "points_missed": points_missed,
                "max_marks": max_marks
            }
        except Exception as e:
            return self._keyword_based_evaluation(question, answer, context, max_marks)

    def _keyword_based_evaluation(self, question: str, answer: str, context: str, max_marks: int) -> dict:
        """Fallback keyword-based evaluation."""
        question_lower = question.lower()
        answer_lower = answer.lower()
        context_lower = context.lower() if context else ""
        
        # Extract keywords from context
        keywords = []
        if context:
            words = context_lower.split()
            keywords = [w.strip('.,!?;:') for w in words if len(w) > 4]
            keywords = list(set(keywords))[:10]
        
        # Count matching keywords
        matches = sum(1 for kw in keywords if kw in answer_lower)
        match_ratio = matches / len(keywords) if keywords else 0
        
        # Calculate score
        score = int(max_marks * match_ratio)
        
        # Bonus for longer answers
        if len(answer) > 100:
            score = min(max_marks, score + 1)
        
        score = max(0, min(score, max_marks))
        
        return {
            "score": score,
            "feedback": f"Answer evaluated. {score}/{max_marks} points awarded.",
            "points_hit": keywords[:min(3, len(keywords))],
            "points_missed": keywords[3:],
            "max_marks": max_marks
        }

    def generate_feedback(self, question, answer, hit, missed):

        if not self.model:
            return "Evaluation completed."

        prompt = f"""
You are a CBSE examiner.

Question: {question}
Answer: {answer}

Correct: {hit}
Missing: {missed}

Give 3-4 line feedback.
"""

        for i in range(3):
            try:
                r = self.model.generate_content(
                    prompt,
                    generation_config={"temperature":0}
                )
                if not r.text:
                    return "Blocked by safety filter"
                return r.text.strip()

            except Exception as e:
                if "429" in str(e):
                    time.sleep(1.5*(2**i)+random.random())
                else:
                    return "Feedback unavailable"

        return "System busy"