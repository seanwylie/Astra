#!/usr/bin/env python3
import argparse
import subprocess
import openai
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

client = OpenAI()  # Uses OPENAI_API_KEY from environment


openai.api_key = os.getenv("OPENAI_API_KEY")

def get_git_diff():
    result = subprocess.run(["git", "diff"], capture_output=True, text=True)
    return result.stdout.strip()

def get_file_contents(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"

def query_gpt(prompt, model="gpt-4", max_tokens=800):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a careful and helpful coding assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()


def run_mode(mode, source):
    if source == "diff":
        context = get_git_diff()
    else:
        context = get_file_contents(source)

    if not context:
        return "[zed_agent] No input provided."

    if mode == "review":
        prompt = f"Review this code diff and suggest improvements or issues:\n\n{context}"
    elif mode == "patch":
        prompt = f"Generate a unified diff that refactors or improves this code:\n\n{context}"
    elif mode == "summary":
        prompt = f"Summarize the intent and purpose of these changes as if writing a commit message:\n\n{context}"
    else:
        return f"[zed_agent] Unknown mode: {mode}"

    return query_gpt(prompt)

def main():
    parser = argparse.ArgumentParser(description="Agentic GPT-powered dev assistant")
    parser.add_argument("--mode", required=True, choices=["review", "patch", "summary"])
    parser.add_argument("--source", default="diff", help="Source file path or 'diff' (default: git diff)")
    parser.add_argument("--log", action="store_true", help="Log result to Astra reflections")

    args = parser.parse_args()
    output = run_mode(args.mode, args.source)
    print(f"\n🧠 ZedAgent ({args.mode}) Output:\n\n{output}")

    if args.log:
        log_dir = os.path.expanduser("~/astra_reflections/")
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.utcnow().isoformat()
        filename = f"{log_dir}zed_{args.mode}_{ts}.txt"
        with open(filename, "w") as f:
            f.write(output)
        print(f"\n📝 Logged to: {filename}")

if __name__ == "__main__":
    main()
