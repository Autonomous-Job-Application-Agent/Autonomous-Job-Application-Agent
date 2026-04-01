"""
resume_parser.py — Parse a PDF resume and build a FAISS vector store.

Usage:
    python resume_parser.py --resume path/to/resume.pdf
"""

import argparse
import os
import shutil
import fitz  # PyMuPDF

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import RESUMES_DIR, FAISS_DIR, EMBED_MODEL, create_dirs


# ── Core Functions ─────────────────────────────────────────────────────────────

def parse_resume_pdf(path: str) -> str:
    """Extract plain text from a PDF resume."""
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    extracted = text.strip()
    print(f"✅ Resume parsed — {len(extracted)} characters extracted.")
    print("--- Preview (first 500 chars) ---")
    print(extracted[:500])
    return extracted


def build_vector_store(resume_text: str) -> FAISS:
    """Chunk the resume text and create a FAISS vector store."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(resume_text)
    docs = [Document(page_content=chunk, metadata={"source": "resume"}) for chunk in chunks]
    print(f"   Resume split into {len(docs)} chunks.")

    print("   Loading embedding model (this may take a moment the first time)…")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    vectorstore = FAISS.from_documents(docs, embeddings)

    # Save locally
    vectorstore.save_local(FAISS_DIR)
    print(f"✅ Vector store saved to: {FAISS_DIR}")

    # Quick sanity check
    results = vectorstore.similarity_search("Python experience", k=2)
    if results:
        print("\nTest query — 'Python experience':")
        print(results[0].page_content[:300])

    return vectorstore


def load_vector_store() -> FAISS:
    """Load an existing FAISS vector store from disk."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    print("✅ Vector store loaded from disk.")
    return vectorstore


def search_resume(vectorstore: FAISS, query: str, k: int = 4) -> str:
    """Search the vector store and return joined chunk text."""
    results = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([r.page_content for r in results])


# ── CLI Entry Point ────────────────────────────────────────────────────────────

def main():
    create_dirs()
    parser = argparse.ArgumentParser(description="Parse a resume PDF and build a vector store.")
    parser.add_argument("--resume", required=True, help="Path to the resume PDF file.")
    args = parser.parse_args()

    resume_path = args.resume
    if not os.path.exists(resume_path):
        print(f"❌ File not found: {resume_path}")
        return

    # Copy to resumes folder
    dest = os.path.join(RESUMES_DIR, os.path.basename(resume_path))
    if resume_path != dest:
        shutil.copy2(resume_path, dest)
        print(f"   Resume copied to: {dest}")

    resume_text = parse_resume_pdf(dest)
    build_vector_store(resume_text)


if __name__ == "__main__":
    main()