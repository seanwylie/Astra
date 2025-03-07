import subprocess
import os

SANDBOX_DIR = "astra_core/evolution/sandbox"

def run_sandbox_test():
    """Runs the test environment safely"""
    test_script = os.path.join(SANDBOX_DIR, "test_script.py")

    if not os.path.exists(test_script):
        print("⚠ No test script found! Astra needs to create one.")
        return
    
    print("🔬 Running Astra's sandbox test...")
    result = subprocess.run(["python3", test_script], capture_output=True, text=True)

    print("📜 Output:\n", result.stdout)
    if result.stderr:
        print("⚠ Errors:\n", result.stderr)

if __name__ == "__main__":
    run_sandbox_test()
