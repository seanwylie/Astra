#!/usr/bin/env python3
"""
Codebase Cleanup Script for Astra Beta
Identifies and removes unused files, cleans up temporary files, and organizes the codebase.
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Dict, Set
import argparse

class CodebaseCleanup:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.root_path = Path(__file__).parent.parent
        self.removed_files = []
        self.cleaned_directories = []
        self.issues_found = []
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🧹 Starting Astra Beta Codebase Cleanup")
        print(f"📁 Root directory: {self.root_path}")
        print(f"🔍 Mode: {'DRY RUN' if self.dry_run else 'LIVE CLEANUP'}")
        print("-" * 50)
        
        # Step 1: Remove Python cache files
        self.clean_python_cache()
        
        # Step 2: Remove temporary and backup files
        self.clean_temporary_files()
        
        # Step 3: Identify unused test files
        self.identify_unused_tests()
        
        # Step 4: Clean up old documentation files
        self.clean_old_documentation()
        
        # Step 5: Organize data files
        self.organize_data_files()
        
        # Step 6: Check for duplicate files
        self.check_for_duplicates()
        
        # Step 7: Validate file structure
        self.validate_file_structure()
        
        # Generate report
        self.generate_cleanup_report()
    
    def clean_python_cache(self):
        """Remove Python cache files and directories"""
        print("🐍 Cleaning Python cache files...")
        
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/.pytest_cache"
        ]
        
        for pattern in cache_patterns:
            for path in self.root_path.glob(pattern):
                if path.is_dir():
                    self._remove_directory(path, "Python cache directory")
                else:
                    self._remove_file(path, "Python cache file")
    
    def clean_temporary_files(self):
        """Remove temporary and backup files"""
        print("🗑️ Cleaning temporary files...")
        
        temp_patterns = [
            "**/*.tmp",
            "**/*.temp",
            "**/*.bak",
            "**/*.backup",
            "**/*~",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.log.old",
            "**/*.log.[0-9]*"
        ]
        
        for pattern in temp_patterns:
            for path in self.root_path.glob(pattern):
                self._remove_file(path, "Temporary file")
        
        # Clean up old log files (keep only recent ones)
        self.clean_old_logs()
    
    def clean_old_logs(self):
        """Clean up old log files"""
        logs_dir = self.root_path / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                # Keep main log files, remove numbered backups
                if any(char.isdigit() for char in log_file.suffix):
                    self._remove_file(log_file, "Old log file")
    
    def identify_unused_tests(self):
        """Identify potentially unused test files"""
        print("🧪 Checking test files...")
        
        test_files = list(self.root_path.glob("**/test_*.py"))
        
        # Check if test files have corresponding source files
        for test_file in test_files:
            if "shimmer" in str(test_file):
                # Shimmer test file seems to be a standalone test
                self.issues_found.append(f"Standalone test file: {test_file}")
        
        # Check for empty test directories
        test_dirs = [
            self.root_path / "tests",
            self.root_path / "beta" / "tests"
        ]
        
        for test_dir in test_dirs:
            if test_dir.exists() and not any(test_dir.iterdir()):
                self._remove_directory(test_dir, "Empty test directory")
    
    def clean_old_documentation(self):
        """Clean up old documentation files"""
        print("📚 Cleaning documentation files...")
        
        # Identify potentially outdated documentation
        doc_files = [
            "BETA_MIGRATION_EVALUATION.md",
            "BETA_OPTIMIZATION_ANALYSIS.md", 
            "LEGACY_CLEANUP_PLAN.md",
            "MIGRATION_PLAN.md",
            "REFACTORING_SUMMARY.md",
            "FINAL_OPTIMIZATION_SUMMARY.md"
        ]
        
        for doc_file in doc_files:
            file_path = self.root_path / doc_file
            if file_path.exists():
                # Move to archive instead of deleting
                archive_dir = self.root_path / "__backups__" / "archived_docs"
                self._archive_file(file_path, archive_dir, "Outdated documentation")
    
    def organize_data_files(self):
        """Organize data files into appropriate directories"""
        print("📊 Organizing data files...")
        
        # Create data directory if it doesn't exist
        data_dir = self.root_path / "data"
        if not data_dir.exists() and not self.dry_run:
            data_dir.mkdir(exist_ok=True)
            print(f"📁 Created data directory: {data_dir}")
        
        # Data files that should be in the data directory
        data_files = [
            "data/analytics_data.json",
            "data/learning_data.json", 
            "data/user_memories.json",
            "data/mind_file_parents.json"
        ]
        
        for data_file in data_files:
            source_path = self.root_path / data_file
            if source_path.exists():
                target_path = data_dir / data_file
                self._move_file(source_path, target_path, "Data file organization")
    
    def check_for_duplicates(self):
        """Check for duplicate files"""
        print("🔍 Checking for duplicate files...")
        
        # Check for potential duplicates
        potential_duplicates = [
            ("utils/config_loader.py", "astra_core/config_loader.py"),
            ("beta/utils/common_utils.py", "utils/json_loader.py")
        ]
        
        for file1, file2 in potential_duplicates:
            path1 = self.root_path / file1
            path2 = self.root_path / file2
            
            if path1.exists() and path2.exists():
                self.issues_found.append(f"Potential duplicate files: {file1} and {file2}")
    
    def validate_file_structure(self):
        """Validate the file structure"""
        print("✅ Validating file structure...")
        
        # Check for required directories
        required_dirs = [
            "beta/commands",
            "beta/services", 
            "beta/config",
            "beta/utils",
            "astra_core",
            "astra_interfaces"
        ]
        
        for dir_path in required_dirs:
            full_path = self.root_path / dir_path
            if not full_path.exists():
                self.issues_found.append(f"Missing required directory: {dir_path}")
        
        # Check for required files
        required_files = [
            "beta/main.py",
            "requirements.txt",
            "README.md",
            ".gitignore"
        ]
        
        for file_path in required_files:
            full_path = self.root_path / file_path
            if not full_path.exists():
                self.issues_found.append(f"Missing required file: {file_path}")
    
    def _remove_file(self, file_path: Path, description: str):
        """Remove a file"""
        if self.dry_run:
            print(f"  🗑️ Would remove {description}: {file_path}")
        else:
            try:
                file_path.unlink()
                print(f"  ✅ Removed {description}: {file_path}")
                self.removed_files.append(str(file_path))
            except Exception as e:
                print(f"  ❌ Failed to remove {file_path}: {e}")
    
    def _remove_directory(self, dir_path: Path, description: str):
        """Remove a directory"""
        if self.dry_run:
            print(f"  🗑️ Would remove {description}: {dir_path}")
        else:
            try:
                shutil.rmtree(dir_path)
                print(f"  ✅ Removed {description}: {dir_path}")
                self.cleaned_directories.append(str(dir_path))
            except Exception as e:
                print(f"  ❌ Failed to remove {dir_path}: {e}")
    
    def _move_file(self, source: Path, target: Path, description: str):
        """Move a file"""
        if self.dry_run:
            print(f"  📦 Would move {description}: {source} → {target}")
        else:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
                print(f"  ✅ Moved {description}: {source} → {target}")
            except Exception as e:
                print(f"  ❌ Failed to move {source}: {e}")
    
    def _archive_file(self, source: Path, archive_dir: Path, description: str):
        """Archive a file"""
        if self.dry_run:
            print(f"  📦 Would archive {description}: {source}")
        else:
            try:
                archive_dir.mkdir(parents=True, exist_ok=True)
                target = archive_dir / source.name
                shutil.move(str(source), str(target))
                print(f"  ✅ Archived {description}: {source} → {target}")
            except Exception as e:
                print(f"  ❌ Failed to archive {source}: {e}")
    
    def generate_cleanup_report(self):
        """Generate a cleanup report"""
        print("\n" + "=" * 50)
        print("📋 CLEANUP REPORT")
        print("=" * 50)
        
        print(f"🗑️ Files removed: {len(self.removed_files)}")
        for file in self.removed_files[:10]:  # Show first 10
            print(f"  - {file}")
        if len(self.removed_files) > 10:
            print(f"  ... and {len(self.removed_files) - 10} more")
        
        print(f"\n📁 Directories cleaned: {len(self.cleaned_directories)}")
        for dir in self.cleaned_directories:
            print(f"  - {dir}")
        
        print(f"\n⚠️ Issues found: {len(self.issues_found)}")
        for issue in self.issues_found:
            print(f"  - {issue}")
        
        if self.dry_run:
            print("\n🔍 This was a DRY RUN. No files were actually modified.")
            print("Run with --execute to perform the actual cleanup.")
        else:
            print("\n✅ Cleanup completed successfully!")
        
        # Save report to file
        report_file = self.root_path / "maintenance" / "cleanup_report.json"
        report_data = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "dry_run": self.dry_run,
            "removed_files": self.removed_files,
            "cleaned_directories": self.cleaned_directories,
            "issues_found": self.issues_found
        }
        
        if not self.dry_run:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"📄 Report saved to: {report_file}")

def main():
    parser = argparse.ArgumentParser(description="Clean up Astra Beta codebase")
    parser.add_argument("--execute", action="store_true", 
                       help="Execute cleanup (default is dry run)")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    cleanup = CodebaseCleanup(dry_run=not args.execute)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()