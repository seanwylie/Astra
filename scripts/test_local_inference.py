#!/usr/bin/env python3
"""Quick test that local inference (Ollama) is available. Run from project root: PYTHONPATH=. .venv/bin/python scripts/test_local_inference.py"""
from pathlib import Path

# Load .env from project root so OLLAMA_BASE_URL is set when running this script standalone
_root = Path(__file__).resolve().parent.parent
_env = _root / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

from app.core.evolution.local_inference import (
    is_local_inference_available,
    query_local_model,
    get_last_inference_error,
)

print("Local inference available:", is_local_inference_available())
if is_local_inference_available():
    r = query_local_model("Say hello in one short sentence.")
    print("Test response:", r or "(none)")
    if r is None:
        err = get_last_inference_error()
        if err:
            print("Error:", err)
        print("Hint: ensure Ollama is running (ollama serve) and the model is loaded (ollama run llama3.2). Check: ollama list")
