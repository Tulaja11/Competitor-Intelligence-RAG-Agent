import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHROMA_PATH = "chroma_db"
SQLITE_PATH = "data/rivalradar.db"
MAX_RESULTS_PER_SEARCH = 5