"""
job_scraper.py — Scrape a job posting URL and extract structured JSON via Gemini.

Usage:
    python job_scraper.py --url "https://example.com/job-posting"
"""

import argparse
import json
import os

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL, JOB_DATA_DIR, create_dirs


# ── Setup ──────────────────────────────────────────────────────────────────────

def _configure_gemini():
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY is not set. Add it to your .env file.")
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)


# ── Core Functions ─────────────────────────────────────────────────────────────

def scrape_job_posting(url: str) -> str | None:
    """Fetch a job posting page and return cleaned plain text (max 8000 chars)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        cleaned = text[:8000]
        print(f"✅ Job posting scraped — {len(cleaned)} characters.")
        print("--- Preview ---")
        print(cleaned[:500])
        return cleaned
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return None


def extract_job_json(raw_text: str, model) -> dict:
    """Use Gemini to extract structured job data from raw posting text."""
    prompt = f"""Extract the following from this job posting and return ONLY valid JSON.
No explanation, no markdown, just the JSON object.

Fields to extract:
- job_title (string)
- company (string)
- required_skills (list of strings)
- preferred_skills (list of strings)
- experience_years (string)
- responsibilities (list of strings)
- education (string)

Job posting:
{raw_text[:4000]}
"""
    response = model.generate_content(prompt)
    text = response.text.strip()
    # Strip any accidental markdown fences
    text = text.replace("```json", "").replace("```", "").strip()
    job_data = json.loads(text)
    print("✅ Job JSON extracted!")
    print(json.dumps(job_data, indent=2))
    return job_data


def save_job_json(job_data: dict, filename: str = "job_requirements.json") -> str:
    """Save extracted job JSON to the job_data directory."""
    os.makedirs(JOB_DATA_DIR, exist_ok=True)
    path = os.path.join(JOB_DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(job_data, f, indent=2)
    print(f"   Job data saved to: {path}")
    return path


def load_job_json(filename: str = "job_requirements.json") -> dict:
    """Load previously saved job JSON."""
    path = os.path.join(JOB_DATA_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


# ── CLI Entry Point ────────────────────────────────────────────────────────────

def main():
    create_dirs()
    parser = argparse.ArgumentParser(description="Scrape a job posting and extract structured data.")
    parser.add_argument("--url", required=True, help="Job posting URL to scrape.")
    args = parser.parse_args()

    model = _configure_gemini()
    raw_text = scrape_job_posting(args.url)

    if not raw_text:
        print("❌ Could not scrape the URL. Try pasting the job description manually.")
        return

    job_data = extract_job_json(raw_text, model)
    save_job_json(job_data)


if __name__ == "__main__":
    main()