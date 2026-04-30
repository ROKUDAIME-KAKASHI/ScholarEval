import re
from .processor import TextProcessor
from .utils import cosine_similarity
from .config import SIMILARITY_THRESHOLD

class ScoringEngine:

    def __init__(self, model):
        self.processor = TextProcessor()
        self.model = model

    def extract_number(self, text):
        nums = re.findall(r"\d+\.?\d*", text)
        return float(nums[0]) if nums else None

    def extract_unit(self, text):
        units = ["m/s","kg","m","cm","km","N","J","W","°C"]
        for u in units:
            if u in text:
                return u
        return None

    def numeric_match(self, student, correct, tol=0.05):
        s = self.extract_number(student)
        c = self.extract_number(correct)
        if s is None or c is None:
            return False
        return abs(s - c)/max(c,1) <= tol

    def unit_match(self, student, correct):
        su = self.extract_unit(student)
        cu = self.extract_unit(correct)
        if not cu:
            return True
        return su == cu

    def score(self, answer, rubric_points, point_embeddings):

        sentences = self.processor.split_sentences(answer) or [answer]

        sent_emb = self.model.encode(sentences, convert_to_numpy=True)

        total = 0
        max_marks = 0
        hit, missed = [], []

        for i, p in enumerate(rubric_points):

            text = p["text"]
            marks = p.get("marks",1)
            emb = point_embeddings[i]

            max_marks += marks

            best = 0

            for s, se in zip(sentences, sent_emb):

                sim = cosine_similarity(se, emb)

                if self.numeric_match(s, text):
                    sim += 0.2

                if not self.unit_match(s, text):
                    sim -= 0.2

                best = max(best, sim)

            if best >= SIMILARITY_THRESHOLD:
                total += marks
                hit.append(text)
            else:
                missed.append(text)

        confidence = total/max_marks if max_marks else 0

        return {
            "score": total,
            "max_marks": max_marks,
            "points_hit": hit,
            "points_missed": missed,
            "confidence": round(confidence,2)
        }