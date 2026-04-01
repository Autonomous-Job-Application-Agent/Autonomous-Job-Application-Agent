"""
pdf_exporter.py — Generate a styled PDF of the tailored resume.

Usage:
    python pdf_exporter.py
    (Reads tailored_bullets.txt and job_requirements.json from data/)
"""

import datetime
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from config import JOB_DATA_DIR, OUTPUTS_DIR, create_dirs
from job_scraper import load_job_json


# ── Style Definitions ──────────────────────────────────────────────────────────

def _build_styles():
    getSampleStyleSheet()  # initialise defaults
    title_style = ParagraphStyle(
        "Title",
        fontSize=18,
        fontName="Helvetica-Bold",
        spaceAfter=4,
        textColor=colors.HexColor("#1F3864"),
    )
    heading_style = ParagraphStyle(
        "Heading",
        fontSize=12,
        fontName="Helvetica-Bold",
        spaceAfter=4,
        spaceBefore=10,
        textColor=colors.HexColor("#2E75B6"),
    )
    body_style = ParagraphStyle(
        "Body",
        fontSize=10,
        fontName="Helvetica",
        spaceAfter=3,
        leading=14,
    )
    return title_style, heading_style, body_style


# ── Core Function ──────────────────────────────────────────────────────────────

def export_resume_pdf(
    tailored_bullets: str,
    job_data: dict,
    output_filename: str = "tailored_resume.pdf",
) -> str:
    """Build and save a styled PDF resume. Returns the saved path."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUTS_DIR, output_filename)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    title_style, heading_style, body_style = _build_styles()
    story = []

    # ── Header block ────────────────────────────────────────────────────────
    story.append(Paragraph("Tailored Resume", title_style))
    story.append(
        Paragraph(
            f"Prepared for: {job_data.get('job_title', 'Role')} "
            f"at {job_data.get('company', 'Company')}",
            body_style,
        )
    )
    story.append(Paragraph(f"Generated: {datetime.date.today()}", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # ── Bullet content ───────────────────────────────────────────────────────
    for line in tailored_bullets.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.05 * inch))
        elif line.endswith(":") or (len(line) < 60 and not line.startswith("-")):
            story.append(Paragraph(line, heading_style))
        else:
            safe_line = line.lstrip("-• ").replace("&", "&amp;")
            story.append(Paragraph(f"• {safe_line}", body_style))

    doc.build(story)
    print(f"✅ Tailored resume PDF saved to: {output_path}")
    return output_path


# ── CLI Entry Point ────────────────────────────────────────────────────────────

def main():
    create_dirs()

    # Load tailored bullets from text file
    bullets_path = os.path.join(OUTPUTS_DIR, "tailored_bullets.txt")
    if not os.path.exists(bullets_path):
        print(f"❌ {bullets_path} not found — run analyzer.py first.")
        return

    with open(bullets_path, "r", encoding="utf-8") as f:
        tailored_bullets = f.read()

    job_data = load_job_json()
    export_resume_pdf(tailored_bullets, job_data)


if __name__ == "__main__":
    main()