import fitz
import re
from .processor import TextProcessor

class PDFManager:

    def __init__(self):
        self.processor = TextProcessor()

    def extract_text(self, path):
        doc = fitz.open(path)
        return "\n".join([page.get_text() for page in doc])

    # -----------------------------
    # 🔥 NEW: NORMALIZATION STEP
    # -----------------------------
    def _normalize(self, text: str) -> str:
        tokens = ["Q-", "Q.", "Q:", "Q ", "Question:", "Ans-", "Ans:", "A.", "Answer:"]
        for t in tokens:
            text = text.replace(t, f"\n{t}")

        # Handle numbered questions like "1. "
        text = re.sub(r'(\s|^)(\d+)\.\s', r'\n\2. ', text)

        return text

    # -----------------------------
    # 🔥 UPDATED PARSER
    # -----------------------------
    def extract_structured_data(self, text):

        text = self._normalize(text)

        lines = text.split("\n")

        data = []
        current_q = None

        question_patterns = [
            r"^Q[\s\-\:\.]*(.*)",
            r"^[0-9]+\.\s*(.*)",
            r"^Question[\s\:\-]*(.*)",
        ]

        answer_patterns = [
            r"^Ans[\s\-\:\.]*(.*)",
            r"^A[\s\-\:\.]*(.*)",
            r"^Answer[\s\:\-]*(.*)",
        ]

        def match(patterns, line):
            for p in patterns:
                m = re.match(p, line, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
            return None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            q_match = match(question_patterns, line)

            if q_match:
                current_q = {"question": q_match, "points": []}
                data.append(current_q)
                continue

            a_match = match(answer_patterns, line)

            if a_match and current_q:
                parts = re.split(r"[;,]", a_match)

                for p in parts:
                    p = p.strip()
                    if p:
                        current_q["points"].append({
                            "text": p,
                            "marks": 1
                        })
                continue

            # fallback: take first meaningful line as answer
            if current_q and not current_q["points"] and len(line) > 3:
                current_q["points"].append({
                    "text": line,
                    "marks": 1
                })

        return [d for d in data if d["points"]]

    def process_pdf(self, path):
        raw = self.extract_text(path)

        if not raw.strip():
            raise ValueError("Unreadable PDF")

        # 🔥 NORMALIZE BEFORE CLEAN
        text = self._normalize(raw)
        text = self.processor.clean_text(text)

        structured = self.extract_structured_data(text)

        if not structured:
            raise ValueError("No questions found")

        return structured