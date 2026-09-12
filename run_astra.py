#!/usr/bin/env python3
"""Run Astra from project root: python3 run_astra.py or python3 -m app.main"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.main import main

if __name__ == "__main__":
    main()
