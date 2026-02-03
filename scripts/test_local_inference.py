#!/usr/bin/env python3
"""Quick test that local inference (Ollama) is available. 
Run from project root: PYTHONPATH=. .venv/bin/python scripts/test_local_inference.py
"""
import os
from pathlib import Path

# Load .env from project root
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

# Grab the configured model name so we know what we're actually testing
target_model = os.getenv("OLLAMA_MODEL", "astra")

print(f"Testing local inference for model: {target_model}")
print("Local inference available:", is_local_inference_available())

if is_local_inference_available():
    # Specific test to ensure Astra's identity is active
    r = query_local_model("Astra, who are you?")
    print("-" * 20)
    print("Astra's Response:", r or "(none)")
    print("-" * 20)
    
    if r is None:
        err = get_last_inference_error()
        if err:
            print("Error details:", err)
        print(f"Hint: Ensure Ollama is running (`ollama serve`) and the model '{target_model}' is created.")
        print(f"Check: Run `ollama list` and verify '{target_model}' exists.")
    elif "I am Astra" not in r and "Astra" not in r:
        print("⚠️ Warning: Response received, but Astra's identity was not detected.")
        print("Verify your Modelfile.astra was built correctly: `ollama create astra -f Modelfile.astra`")