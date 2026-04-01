"""
analyzer.py — Skill gap analysis, tailored resume bullets, and cover letter generation.

Usage:
    python analyzer.py
    (Reads from data/job_data/job_requirements.json and data/resume_faiss/)
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_API_KEY, GEMINI_MODEL, LLM_TEMP, JOB_DATA_DIR, create_dirs
from resume_parser import load_vector_store, search_resume
from job_scraper import load_job_json


# ── LLM Setup ─────────────────────────────────────────────────────────────────

def get_llm() -> ChatGoogleGenerativeAI:
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY is not set. Add it to your .env file.")
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=LLM_TEMP)


# ── Analysis Functions ─────────────────────────────────────────────────────────

def run_gap_analysis(llm, resume_text: str, job_text: str) -> str:
    """Compare resume against job description and return a gap analysis."""
    prompt = f"""Analyze the candidate's resume against the job requirements.

RESUME:
{resume_text[:5000]}

JOB DESCRIPTION:
{job_text[:5000]}

Tasks:
1. List skills FROM THE RESUME that match the job requirements.
2. List skills REQUIRED BY THE JOB that are MISSING from the resume.
3. Give an estimated match score from 0–100%.
4. Give 3 short recommendations to improve the resume.

Be specific and factual — only use what is actually in the resume.
"""
    response = llm.invoke(prompt)
    return response.content


def generate_tailored_bullets(llm, resume_text: str, retrieved_context: str, job_data: dict) -> str:
    """Rewrite resume bullet points to better match the target role."""
    prompt = f"""You are a professional resume writer.

Using ONLY the candidate information below, rewrite resume bullet points so they fit this target role better.

STRICT RULES:
- Do NOT invent experience
- Do NOT invent metrics
- Do NOT add tools/skills not supported by the resume
- Mirror job keywords only when truthful

CANDIDATE RESUME CONTEXT:
{retrieved_context}

FULL RESUME:
{resume_text[:5000]}

TARGET JOB:
Title: {job_data.get('job_title', 'Software Engineer')}
Company: {job_data.get('company', 'Target Company')}
Required Skills: {', '.join(job_data.get('required_skills', []))}
Preferred Skills: {', '.join(job_data.get('preferred_skills', []))}
Responsibilities: {', '.join(job_data.get('responsibilities', []))}
"""
    response = llm.invoke(prompt)
    return response.content


def generate_cover_letter(llm, resume_text: str, job_data: dict) -> str:
    """Generate a personalized cover letter for the target role."""
    prompt = f"""Write a professional, personalized cover letter for this job application.

Requirements:
- 3 paragraphs
- Under 300 words
- Confident and professional tone
- Mention 2–3 skills that genuinely appear in the resume
- Do not invent experience

RESUME:
{resume_text[:5000]}

JOB:
Title: {job_data.get('job_title', '')}
Company: {job_data.get('company', '')}
Required Skills: {', '.join(job_data.get('required_skills', [])[:8])}
Responsibilities: {', '.join(job_data.get('responsibilities', [])[:6])}
"""
    response = llm.invoke(prompt)
    return response.content


# ── CLI Entry Point ────────────────────────────────────────────────────────────

def main():
    create_dirs()
    print("Loading resources…")

    llm = get_llm()
    vectorstore = load_vector_store()
    job_data = load_job_json()

    # Load resume text from the vector store chunks as a proxy
    resume_text = search_resume(vectorstore, "skills experience education projects", k=10)

    print("\n=== [1/3] SKILL GAP ANALYSIS ===")
    job_text = (
        f"Title: {job_data.get('job_title')}\n"
        f"Required Skills: {', '.join(job_data.get('required_skills', []))}\n"
        f"Preferred Skills: {', '.join(job_data.get('preferred_skills', []))}\n"
        f"Responsibilities: {'. '.join(job_data.get('responsibilities', []))}\n"
        f"Experience: {job_data.get('experience_years', '')}\n"
        f"Education: {job_data.get('education', '')}"
    )
    gap_analysis = run_gap_analysis(llm, resume_text, job_text)
    print(gap_analysis)

    print("\n=== [2/3] TAILORED RESUME BULLETS ===")
    retrieved_context = search_resume(
        vectorstore,
        f"skills achievements experience for {job_data.get('job_title', 'the role')}",
        k=4,
    )
    tailored_bullets = generate_tailored_bullets(llm, resume_text, retrieved_context, job_data)
    print(tailored_bullets)

    print("\n=== [3/3] COVER LETTER ===")
    cover_letter = generate_cover_letter(llm, resume_text, job_data)
    print(cover_letter)

    # Save outputs as text files for reference
    outputs = {
        "gap_analysis.txt": gap_analysis,
        "tailored_bullets.txt": tailored_bullets,
        "cover_letter.txt": cover_letter,
    }
    from config import OUTPUTS_DIR
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    for fname, content in outputs.items():
        path = os.path.join(OUTPUTS_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   Saved: {path}")

    print("\n✅ Analysis complete! Check data/outputs/ for all text files.")
    return gap_analysis, tailored_bullets, cover_letter


if __name__ == "__main__":
    main()