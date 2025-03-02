import os
import zipfile

# Define important file extensions and size limit (in MB)
IMPORTANT_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".txt", ".md", ".ini"}
SIZE_LIMIT_MB = 50  # Adjust this as needed
EXCLUDED_DIRS = {"venv", "__pycache__", ".git", "logs", "backups", "node_modules", "datasets", "models", "checkpoints", ".mypy_cache", ".pytest_cache", ".vscode", "large_files", "temp"}

# Define zip output name
ZIP_FILENAME = "important_backup.zip"

def should_include(file_path):
    """Check if the file should be included in the zip."""
    if not os.path.isfile(file_path):
        return False  # Ignore directories

    # Get file extension and size
    _, ext = os.path.splitext(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    # Include if it's an important extension and below size limit
    return ext in IMPORTANT_EXTENSIONS and file_size_mb <= SIZE_LIMIT_MB

def zip_important_files(root_dir="."):
    """Create a zip file including only important files."""
    with zipfile.ZipFile(ZIP_FILENAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(root_dir):
            # Skip excluded directories
            if any(excluded in foldername.split(os.sep) for excluded in EXCLUDED_DIRS):
                continue

            for filename in filenames:
                file_path = os.path.join(foldername, filename)

                if should_include(file_path):
                    zipf.write(file_path, os.path.relpath(file_path, root_dir))
                    print(f"✅ Added: {file_path}")

    print(f"\n🎉 Zip created: {ZIP_FILENAME}")

if __name__ == "__main__":
    zip_important_files()
