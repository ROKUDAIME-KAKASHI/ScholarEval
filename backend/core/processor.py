import re

class TextProcessor:

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def split_sentences(self, text):
        return [s.strip() for s in text.split('.') if len(s.strip()) > 3]