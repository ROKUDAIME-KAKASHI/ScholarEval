from sentence_transformers import SentenceTransformer
import faiss
from .config import EMBEDDING_MODEL, TOP_K

class RAGEngine:

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.data = []
        self.index = None

    def build_index(self, structured_data):

        self.data = structured_data

        questions = [d["question"] for d in structured_data]

        embeddings = self.model.encode(questions, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        # precompute point embeddings
        for item in self.data:
            texts = [p["text"] for p in item["points"]]
            pe = self.model.encode(texts, convert_to_numpy=True)
            faiss.normalize_L2(pe)
            item["point_embeddings"] = pe

    def retrieve(self, query):

        q_emb = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)

        D, I = self.index.search(q_emb, TOP_K)

        return [(D[0][i], self.data[I[0][i]]) for i in range(len(I[0]))]