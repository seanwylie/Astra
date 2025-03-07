# astra_core/evolution/sandbox/test_script.py

import subprocess
import psutil
import requests
import os
import re
from astra_core.knowledge import knowledge_manager

CRITICAL_FILES = ["astra_core/processing.py", "astra_core/discord_astra.py"]
LOG_FILES = ["logs/astra_processing.log", "logs/discord_astra.log"]

def test_processing():
    """Ensure Astra can reflect & update knowledge."""
    import astra_core.processing
    astra_core.processing.process_reflection()
    print("✅ Processing module: Reflections & knowledge updates work.")

def test_discord_commands():
    """Simulate Astra processing Discord commands."""
    commands_to_test = ["!reflect", "!trust", "!ask", "!knowledge"]

    for command in commands_to_test:
        print(f"🔍 Testing Discord command: {command}")
        result = subprocess.run(["python3", "astra_core/discord_astra.py", command], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"🚨 Failed on {command}: {result.stderr}")
            exit(1)

        print(f"✅ Passed: {command}")

def check_system_usage():
    """Monitor CPU & memory usage after changes."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    print(f"🖥️ CPU Usage: {cpu_usage}% | RAM Usage: {memory_usage}%")

    if cpu_usage > 85 or memory_usage > 90:
        print("🚨 WARNING: Astra's changes might be consuming too many resources!")
        exit(1)

    print("✅ System usage is within safe limits.")

def test_knowledge_lookup():
    """Ensure Astra can still look up external knowledge."""
    test_concept = "Einstein"
    found = knowledge_manager.retrieve_external_knowledge([test_concept])

    if not found:
        print("🚨 Astra's external lookups are broken!")
        exit(1)

    print("✅ Knowledge lookup works!")

def validate_file_integrity():
    """Ensure Astra's critical files are not corrupted or missing essential functions."""
    for file in CRITICAL_FILES:
        if not os.path.exists(file):
            print(f"🚨 ERROR: {file} is missing!")
            exit(1)

        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) < 100:  # Arbitrary minimum size to detect truncation
            print(f"🚨 ERROR: {file} appears truncated or empty!")
            exit(1)

        if "def " not in content and "class " not in content:
            print(f"🚨 WARNING: {file} does not contain functions or classes. This may be an issue!")

    print("✅ File integrity checks passed!")

def check_logs_for_errors():
    """Scan logs for recent warnings or errors after Astra's modification."""
    error_patterns = [r"ERROR", r"Traceback", r"Exception", r"CRITICAL"]

    for log_file in LOG_FILES:
        if not os.path.exists(log_file):
            print(f"⚠ Skipping log scan: {log_file} does not exist.")
            continue

        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]  # Only scan the last 50 log entries

        for line in lines:
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in error_patterns):
                print(f"🚨 Detected issue in {log_file}: {line.strip()}")
                exit(1)

    print("✅ No critical errors found in logs.")

def run_tests():
    """Run all of Astra's validation tests."""
    try:
        print("🔍 Running Astra's full system test...")

        validate_file_integrity()
        test_processing()
        test_discord_commands()
        check_system_usage()
        test_knowledge_lookup()
        check_logs_for_errors()

        print("🎉 ALL TESTS PASSED! Astra's changes are valid.")
        exit(0)

    except Exception as e:
        print(f"🚨 TEST FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    run_tests()
