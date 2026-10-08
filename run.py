"""
GBPIET Campus AI Assistant - Local Runner
Runs the FastAPI web server on http://127.0.0.1:8000
"""

import uvicorn
import webbrowser
import os
import sys

def main():
    print("=" * 65)
    print("  IEEE GenAI Build 2026 - Campus Chatbot Challenge")
    print("  GBPIET Campus AI Assistant (Docling + Hybrid RAG + Voice)")
    print("=" * 65)
    print("\nStarting local server on http://127.0.0.1:8000 ...")
    print("Press CTRL+C to stop.\n")

    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
