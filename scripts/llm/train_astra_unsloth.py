#!/usr/bin/env python3
"""
Format data/astra_training.jsonl and fine-tune with Unsloth (LoRA/QLoRA).

Requires (install separately): unsloth, trl, transformers, torch, datasets
  pip install unsloth trl transformers torch datasets

Usage (from project root):
  PYTHONPATH=. .venv/bin/python scripts/llm/train_astra_unsloth.py
  PYTHONPATH=. .venv/bin/python scripts/llm/train_astra_unsloth.py --max-steps 120 --output-dir data/astra_lora

From scripts/llm:
  python train_astra_unsloth.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "astra_training.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "astra_lora"
DEFAULT_MODEL = "unsloth/llama-3.1-8b-unsloth-bnb-4bit"


def _check_gpu():
    """Ensure PyTorch sees a GPU before Unsloth is imported (Unsloth requires it at import)."""
    import torch
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        return
    print("PyTorch does not see a GPU. Unsloth requires a CUDA GPU.", file=sys.stderr)
    print("  1. Check driver: nvidia-smi", file=sys.stderr)
    print("  2. Reinstall PyTorch with CUDA, e.g.:", file=sys.stderr)
    print("     pip install torch --index-url https://download.pytorch.org/whl/cu121", file=sys.stderr)
    print("  3. Then: pip install unsloth trl transformers datasets", file=sys.stderr)
    sys.exit(1)


def _import_unsloth():
    try:
        from unsloth import FastLanguageModel
        return FastLanguageModel
    except NotImplementedError as e:
        if "accelerator" in str(e).lower() or "gpu" in str(e).lower():
            _check_gpu()
        raise SystemExit(1) from e
    except ImportError as e:
        print("Install Unsloth and deps: pip install unsloth trl transformers torch datasets", file=sys.stderr)
        raise SystemExit(1) from e


def load_and_format_dataset(data_file: Path, tokenizer):
    """Load JSONL and format Alpaca (instruction/input/output) -> single 'text' field."""
    from datasets import load_dataset

    dataset = load_dataset("json", data_files=str(data_file), split="train")
    eos = getattr(tokenizer, "eos_token", None) or ""

    def format_astra(examples):
        texts = []
        for inst, inp, out in zip(
            examples["instruction"],
            examples["input"],
            examples["output"],
        ):
            inp_part = f"\n### Input:\n{inp}" if (inp and inp.strip()) else ""
            text = f"### Instruction:\n{inst}{inp_part}\n\n### Response:\n{out}" + eos
            texts.append(text)
        return {"text": texts}

    formatted = dataset.map(
        format_astra,
        batched=True,
        remove_columns=dataset.column_names,
        num_proc=2,
        desc="Format dataset",
    )
    return formatted


def main():
    parser = argparse.ArgumentParser(description="Format and train Astra corpus with Unsloth")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HuggingFace model id (default: %(default)s)")
    parser.add_argument("--data-file", type=Path, default=DATA_FILE, help="Training JSONL path")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="LoRA adapter output dir")
    parser.add_argument("--max-steps", type=int, default=60, help="Training steps (default 60)")
    parser.add_argument("--max-seq-length", type=int, default=2048, help="Max sequence length")
    parser.add_argument("--format-only", action="store_true", help="Only load and format; do not train")
    args = parser.parse_args()

    if not args.data_file.exists():
        print(f"Data file not found: {args.data_file}", file=sys.stderr)
        print("Run export then: PYTHONPATH=. .venv/bin/python scripts/llm/convert_corpus_for_training.py", file=sys.stderr)
        sys.exit(1)

    _check_gpu()
    FastLanguageModel = _import_unsloth()
    import torch
    from trl import SFTTrainer
    from transformers import TrainingArguments

    print("Loading model and tokenizer...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
    )

    print("Loading and formatting dataset...")
    dataset = load_and_format_dataset(args.data_file, tokenizer)
    print(f"Formatted examples: {dataset.num_rows}")

    if args.format_only:
        print("Format-only: skipping training.")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=args.max_steps,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        save_strategy="steps",
        save_steps=max(10, args.max_steps // 2),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )
    print("Training...")
    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    print(f"Saved adapter and tokenizer to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
