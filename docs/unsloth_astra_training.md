# Exact commands: fine-tune with Unsloth using `data/astra_training.jsonl`

Your file is **Alpaca-style** (`instruction`, `input`, `output`). Use it as below.

---

## 0. One-command format and train

From project root (requires an NVIDIA GPU on the machine). Install deps once: `pip install -r scripts/llm/requirements-llm.txt`. **No GPU on this machine?** Run training on a machine that has an NVIDIA GPU (e.g. your laptop): copy `data/astra_training.jsonl` to it (or clone the repo and run export/convert there), install deps and run the script; then copy the saved adapter back and import into Ollama here. Or use [Unsloth Notebooks](https://docs.unsloth.ai/docs/get-started/unsloth-notebooks) (Colab/Kaggle).

```bash
PYTHONPATH=. .venv/bin/python scripts/llm/train_astra_unsloth.py
```

Options: `--max-steps 120`, `--output-dir data/astra_lora`, `--model unsloth/llama-3.1-8b-unsloth-bnb-4bit`, `--format-only` (load + format only, no training).

Adapter is saved to `data/astra_lora` by default. See `docs/evolution.md` for importing into Ollama.

### Training on a laptop (or any machine with an NVIDIA GPU)

1. **Get the data onto the laptop:** copy `data/astra_training.jsonl` (e.g. `scp`, USB, or clone the repo and run `./scripts/export_corpus_for_training.sh` then `PYTHONPATH=. .venv/bin/python scripts/llm/convert_corpus_for_training.py` there).
2. **On the laptop:** create a venv, then `pip install -r scripts/llm/requirements-llm.txt` (or `pip install unsloth trl transformers torch datasets`). Ensure PyTorch sees the GPU: `python -c "import torch; print(torch.cuda.is_available())"` → `True`.
3. **Train:** from the repo root, `PYTHONPATH=. .venv/bin/python scripts/llm/train_astra_unsloth.py`. If you have limited VRAM (e.g. 6–8 GB), use a smaller model: `--model unsloth/llama-3.2-3b-unsloth-bnb-4bit`.
4. **Copy the adapter back to the server:** the script writes to `data/astra_lora` by default; zip or `scp` that folder to the server, then create the Ollama model there (see `docs/evolution.md`).

---

### If `nvidia-smi` is not found (Ubuntu)

Install NVIDIA driver and utils so the GPU is visible. Pick one version that matches your GPU (535 or 550 are good defaults for recent cards):

```bash
sudo apt update
sudo apt install nvidia-utils-535   # or nvidia-utils-550, nvidia-utils-580, etc.
```

If the driver isn’t installed yet, use the matching driver package (e.g. `nvidia-driver-535`). **Reboot** after installing; then run `nvidia-smi` to confirm. If `nvidia-smi` still says “couldn’t communicate with the NVIDIA driver” after a reboot:

1. **Secure Boot** – If enabled, the NVIDIA kernel module may be blocked. Check: `mokutil --sb-state`. Either disable Secure Boot in BIOS or enroll the NVIDIA key when prompted at boot (the driver install may have printed a one-time password for MOK enrollment).
2. **Kernel module** – See if the module is loaded: `lsmod | grep nvidia`. If empty, check: `dmesg | grep -i nvidia` and `dpkg -l | grep nvidia`. Ensure `linux-headers-$(uname -r)` and `dkms` are installed, then `sudo apt install --reinstall nvidia-driver-535` and reboot.
3. **GPU visible** – Confirm the card is seen: `lspci | grep -i nvidia`. If this prints nothing, the system has no NVIDIA GPU visible (wrong machine, GPU disabled in BIOS, or not installed); the driver cannot load without a device.

After the driver loads, PyTorch (CUDA build) and Unsloth will see the GPU.

---

## 1. Paths (from project root)

- Training file: **`data/astra_training.jsonl`**
- Absolute: **`/home/sean/dev/systems/Astra/data/astra_training.jsonl`**

---

## 2. Regenerate the file (optional)

If you want to re-export and convert before training:

```bash
cd /home/sean/dev/systems/Astra

./scripts/export_corpus_for_training.sh
PYTHONPATH=. .venv/bin/python scripts/convert_corpus_for_training.py
```

Output: `data/astra_training.jsonl` (same path as above).

---

## 3. Load the dataset in Python (Unsloth / Colab / local)

In your Unsloth notebook or script:

```python
from datasets import load_dataset

# From project root, or use absolute path
dataset = load_dataset(
    "json",
    data_files="/home/sean/dev/systems/Astra/data/astra_training.jsonl",
    split="train"
)
# Or if your working directory is project root:
# data_files="data/astra_training.jsonl"
```

---

## 4. Format for Unsloth (Alpaca → single `text` field)

Your rows have `instruction`, `input`, `output`. Map them into one `text` field for `SFTTrainer`:

```python
def format_astra(examples):
    # Llama 3.1–style chat template (adjust if using a different base model):
    template = (
        "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
        "{instruction}\n{input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        "{output}<|eot_id|>"
    )
    texts = []
    for i, inp, out in zip(
        examples["instruction"],
        examples["input"],
        examples["output"],
    ):
        inp_str = inp.strip() if inp else ""
        text = template.format(instruction=i, input=inp_str, output=out)
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(format_astra, batched=True, remove_columns=dataset.column_names)
```

**Simpler option (generic Alpaca-style, any model):**

```python
EOS = tokenizer.eos_token or ""

def format_astra(examples):
    texts = []
    for i, inp, out in zip(
        examples["instruction"],
        examples["input"],
        examples["output"],
    ):
        inp_part = f"\n### Input:\n{inp}" if (inp and inp.strip()) else ""
        text = f"### Instruction:\n{i}{inp_part}\n\n### Response:\n{out}" + EOS
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(format_astra, batched=True, remove_columns=dataset.column_names)
```

Use the same tokenizer you use for the model (e.g. from `FastLanguageModel.from_pretrained(..., tokenizer=...)`).

---

## 5. Train with Unsloth (snippet)

After loading model and tokenizer with `FastLanguageModel.from_pretrained(...)` and preparing `dataset` as above:

```python
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        output_dir="./astra_lora",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        save_strategy="steps",
        save_steps=30,
    ),
)
trainer.train()
```

---

## 6. Save adapter and export to GGUF (for Ollama)

```python
model.save_pretrained_gguf("astra_gguf", tokenizer, quantization_method="q4_k_m")
# Or save LoRA only:
# model.save_pretrained("astra_lora")
```

Then create the Ollama model (see `docs/evolution.md`):

```bash
ollama create astra -f Modelfile.astra
# Modelfile.astra: FROM llama3.2  (or your base); ADAPTER /path/to/astra_gguf or adapter dir
```

---

## 7. One-liner reference

| Step        | Command |
|------------|--------|
| Re-export  | `./scripts/export_corpus_for_training.sh` |
| Convert    | `PYTHONPATH=. .venv/bin/python scripts/convert_corpus_for_training.py` |
| Train file | `data/astra_training.jsonl` |
| Load in Python | `load_dataset("json", data_files="data/astra_training.jsonl", split="train")` |

See `docs/evolution.md` for full flow (export → convert → fine-tune → Ollama → `OLLAMA_MODEL=astra`).
