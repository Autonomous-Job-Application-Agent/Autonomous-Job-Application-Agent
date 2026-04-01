"""
main.py — Full pipeline: scrape → extract → analyse → export PDF → log to DB.

Usage:
    python main.py --resume path/to/resume.pdf --url "https://example.com/job"

Optional flags:
    --skip-scrape   Skip scraping (uses existing job_requirements.json)
    --skip-parse    Skip resume parsing (uses existing FAISS store)
"""

import argparse
import os
import time

from config import OUTPUTS_DIR, create_dirs
from resume_parser import parse_resume_pdf, build_vector_store, load_vector_store, search_resume
from job_scraper import scrape_job_posting, extract_job_json, save_job_json, load_job_json, _configure_gemini
from analyzer import get_llm, run_gap_analysis, generate_tailored_bullets, generate_cover_letter
from pdf_exporter import export_resume_pdf
from database import log_application


def run_pipeline(resume_path: str, job_url: str, skip_scrape: bool, skip_parse: bool):
    create_dirs()
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    print("\n" + "═" * 60)
    print("  🤖  AUTONOMOUS JOB APPLICATION AGENT")
    print("═" * 60)

    # ── Step 1: Parse Resume ───────────────────────────────────────────────────
    if skip_parse:
        print("\n[1/5] Loading existing vector store…")
        vectorstore = load_vector_store()
        resume_text = search_resume(vectorstore, "skills experience education projects", k=10)
    else:
        print(f"\n[1/5] 📄 Parsing resume: {resume_path}")
        resume_text = parse_resume_pdf(resume_path)
        vectorstore = build_vector_store(resume_text)
    time.sleep(0.5)

    # ── Step 2: Scrape & Extract Job Posting ───────────────────────────────────
    if skip_scrape:
        print("\n[2/5] Loading existing job requirements…")
        job_data = load_job_json()
        raw_job_text = (
            f"Title: {job_data.get('job_title')}\n"
            f"Required: {', '.join(job_data.get('required_skills', []))}\n"
            f"Responsibilities: {'. '.join(job_data.get('responsibilities', []))}"
        )
    else:
        print(f"\n[2/5] 🔍 Scraping job posting: {job_url}")
        gemini_model = _configure_gemini()
        raw_job_text = scrape_job_posting(job_url)
        if not raw_job_text:
            print("❌ Could not scrape the job URL. Exiting.")
            return
        print("   Extracting structured data with Gemini…")
        job_data = extract_job_json(raw_job_text, gemini_model)
        save_job_json(job_data)
    time.sleep(0.5)

    # ── Step 3: Gap Analysis ───────────────────────────────────────────────────
    print(f"\n[3/5] 🧠 Running skill gap analysis…")
    llm = get_llm()
    gap_analysis = run_gap_analysis(llm, resume_text, raw_job_text)
    print(gap_analysis[:800])
    with open(os.path.join(OUTPUTS_DIR, "gap_analysis.txt"), "w", encoding="utf-8") as f:
        f.write(gap_analysis)
    time.sleep(0.5)

    # ── Step 4: Tailored Content ───────────────────────────────────────────────
    print(f"\n[4/5] ✍️  Generating tailored resume & cover letter…")
    retrieved_context = search_resume(
        vectorstore,
        f"skills achievements experience for {job_data.get('job_title', 'the role')}",
        k=4,
    )
    tailored_bullets = generate_tailored_bullets(llm, resume_text, retrieved_context, job_data)
    cover_letter = generate_cover_letter(llm, resume_text, job_data)

    with open(os.path.join(OUTPUTS_DIR, "tailored_bullets.txt"), "w", encoding="utf-8") as f:
        f.write(tailored_bullets)
    with open(os.path.join(OUTPUTS_DIR, "cover_letter.txt"), "w", encoding="utf-8") as f:
        f.write(cover_letter)

    print("✅ Tailored bullets and cover letter saved.")
    time.sleep(0.5)

    # ── Step 5: Export PDF + Log ───────────────────────────────────────────────
    print(f"\n[5/5] 📄 Exporting PDF and logging to database…")
    pdf_path = export_resume_pdf(tailored_bullets, job_data)
    log_application(
        job_title=job_data.get("job_title", "Unknown"),
        company=job_data.get("company", "Unknown"),
        job_url=job_url if not skip_scrape else "N/A",
        gap_analysis=gap_analysis,
        resume_path=pdf_path,
        cover_letter=cover_letter,
    )

    # ── Summary ────────────────────────────────────────────────────────────────
    import re
    score_match = re.search(r"(\d{1,3})\s*%", gap_analysis)
    match_score = score_match.group(0) if score_match else "N/A"

    print("\n" + "═" * 60)
    print("  ✅  PIPELINE COMPLETE")
    print("═" * 60)
    print(f"  Role       : {job_data.get('job_title')} @ {job_data.get('company')}")
    print(f"  Match Score: {match_score}")
    print(f"  PDF        : {pdf_path}")
    print(f"  Outputs    : {OUTPUTS_DIR}/")
    print(f"\n  Run `streamlit run dashboard.py` to view the tracker.")
    print("═" * 60 + "\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Autonomous Job Application Agent")
    parser.add_argument("--resume", help="Path to your resume PDF.")
    parser.add_argument("--url", help="Job posting URL.")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping; use existing job_requirements.json.",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Skip resume parsing; use existing FAISS vector store.",
    )
    args = parser.parse_args()

    # Interactive fallback if flags not provided
    if not args.skip_parse and not args.resume:
        args.resume = input("Enter path to your resume PDF: ").strip()
    if not args.skip_scrape and not args.url:
        args.url = input("Enter job posting URL: ").strip()

    run_pipeline(
        resume_path=args.resume or "",
        job_url=args.url or "",
        skip_scrape=args.skip_scrape,
        skip_parse=args.skip_parse,
    )


if __name__ == "__main__":
    main()