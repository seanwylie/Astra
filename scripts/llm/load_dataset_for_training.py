"""Load data/astra_training.jsonl for Unsloth/TRL. Run from scripts/llm or project root."""
from pathlib import Path

from datasets import load_dataset

# Resolve path: works from scripts/llm or project root
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "astra_training.jsonl"


def main():
    dataset = load_dataset("json", data_files=str(DATA_FILE), split="train")
    print(f"Examples: {dataset.num_rows}")
    print(f"Columns: {dataset.column_names}")
    if dataset.num_rows:
        ex = dataset[0]
        print(f"Sample keys: {list(ex.keys())}")
    return dataset


if __name__ == "__main__":
    main()