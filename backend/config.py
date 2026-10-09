import os
import socket
from pathlib import Path
from dotenv import load_dotenv

# Force IPv4 socket resolution to prevent 25-second Windows IPv6 handshake timeouts
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    ipv4_results = [r for r in results if r[0] == socket.AF_INET]
    return ipv4_results if ipv4_results else results
socket.getaddrinfo = _ipv4_getaddrinfo

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# LLM & Embedding Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Preferred Model
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Retrieval & Grounding Settings
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.62"))
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "5"))
BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.4"))
DENSE_WEIGHT = float(os.getenv("DENSE_WEIGHT", "0.6"))

# Zero-Hallucination Safe Fallback Message
FALLBACK_RESPONSE = (
    "I could not find this information in the official campus document. "
    "To ensure zero hallucinations, I only provide answers explicitly verified in the provided dataset."
)
