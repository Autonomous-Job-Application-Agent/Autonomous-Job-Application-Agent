"""
config.py — Central configuration for the Job Application Agent.
All paths and settings are defined here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Project Folder Structure ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESUMES_DIR    = os.path.join(BASE_DIR, "data", "resumes")
OUTPUTS_DIR    = os.path.join(BASE_DIR, "data", "outputs")
JOB_DATA_DIR   = os.path.join(BASE_DIR, "data", "job_data")
DB_DIR         = os.path.join(BASE_DIR, "data", "db")
FAISS_DIR      = os.path.join(BASE_DIR, "data", "resume_faiss")

DB_PATH        = os.path.join(DB_DIR, "applications.db")

# ── Model Settings ────────────────────────────────────────────────────────────
GEMINI_MODEL   = "gemini-2.5-flash"
EMBED_MODEL    = "all-MiniLM-L6-v2"
LLM_TEMP       = 0.2

def create_dirs():
    """Create all project directories if they don't exist."""
    for d in [RESUMES_DIR, OUTPUTS_DIR, JOB_DATA_DIR, DB_DIR, FAISS_DIR]:
        os.makedirs(d, exist_ok=True)
    print("✅ Project directories ready.")


if __name__ == "__main__":
    create_dirs()
    print(f"Project root: {BASE_DIR}")
    if not GEMINI_API_KEY:
        print("⚠️  GEMINI_API_KEY not found — add it to your .env file!")
    else:
        print("✅ GEMINI_API_KEY loaded.")