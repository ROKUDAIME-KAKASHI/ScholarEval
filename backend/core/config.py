import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TOP_K = 5
SIMILARITY_THRESHOLD = 0.55
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Flask configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# File upload configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", 50 * 1024 * 1024))  # 50MB default
ALLOWED_EXTENSIONS = {"pdf"}