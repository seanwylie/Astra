#!/usr/bin/env python3
"""
System Validation Script for Astra
Validates all systems, configurations, and integrations are working correctly.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

class SystemValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
        self.root_path = Path(__file__).parent.parent
    
    def run_validation(self):
        """Run complete system validation"""
        print("🔍 Astra System Validation")
        print("=" * 50)
        
        # Core system validation
        self.validate_imports()
        self.validate_configurations()
        self.validate_services()
        self.validate_commands()
        self.validate_file_structure()
        self.validate_data_files()
        
        # Generate report
        self.generate_report()
    
    def validate_imports(self):
        """Validate all critical imports work"""
        print("📦 Validating imports...")
        
        try:
            # Test core service imports
            from app.services import (
                personality_service, memory_service, creative_service,
                learning_service, analytics_service
            )
            self.successes.append("✅ All core services import successfully")
            
            # Test configuration
            from app.config.loader import config_manager
            dc = config_manager.get_discord_config()
            vc = config_manager.get_values_config()
            if dc and vc:
                self.successes.append("✅ Configuration (discord/values) load successfully")
            else:
                self.warnings.append("⚠️ Some config files missing")
            
            # Test command imports
            from app.commands.memory_commands import MemoryCommands
            from app.commands.creative_commands import CreativeCommands
            from app.commands.learning_commands import LearningCommands
            from app.commands.analytics_commands import AnalyticsCommands
            self.successes.append("✅ All command modules import successfully")
            
        except ImportError as e:
            self.issues.append(f"❌ Import error: {e}")
        except Exception as e:
            self.issues.append(f"❌ Unexpected import error: {e}")
    
    def validate_configurations(self):
        """Validate system configurations"""
        print("⚙️ Validating configurations...")
        
        try:
            from app.config.loader import load_config
            discord_c = load_config("discord_config")
            values_c = load_config("values_config")
            if discord_c.get("discord_channel") and values_c.get("values"):
                self.successes.append("✅ System configuration (discord/values) valid")
            else:
                self.warnings.append("⚠️ discord_channel or values missing in config")
        except Exception as e:
            self.issues.append(f"❌ Configuration validation error: {e}")
    
    def validate_services(self):
        """Validate all services are functional"""
        print("🔧 Validating services...")
        
        try:
            # Test personality service
            from app.services.personality_service import personality_service
            current_mode = personality_service.current_mode
            if current_mode in ["curious", "analytical", "creative", "mentor", "philosophical", "balanced"]:
                self.successes.append("✅ Personality service operational")
            else:
                self.warnings.append(f"⚠️ Unexpected personality mode: {current_mode}")
            
            # Test memory service
            from app.services.memory_service import memory_service
            if hasattr(memory_service, 'remember') and hasattr(memory_service, 'recall'):
                self.successes.append("✅ Memory service operational")
            else:
                self.issues.append("❌ Memory service missing core methods")
            
            # Test creative service
            from app.services.creative_service import creative_service
            if hasattr(creative_service, 'create_poem') and hasattr(creative_service, 'write_story'):
                self.successes.append("✅ Creative service operational")
            else:
                self.issues.append("❌ Creative service missing core methods")
            
            # Test learning service
            from app.services.learning_service import learning_service
            if hasattr(learning_service, 'learn_from_text') and hasattr(learning_service, 'generate_quiz'):
                self.successes.append("✅ Learning service operational")
            else:
                self.issues.append("❌ Learning service missing core methods")
            
            # Test analytics service
            from app.services.analytics_service import analytics_service
            if hasattr(analytics_service, 'get_comprehensive_dashboard'):
                self.successes.append("✅ Analytics service operational")
            else:
                self.issues.append("❌ Analytics service missing core methods")
                
        except Exception as e:
            self.issues.append(f"❌ Service validation error: {e}")
    
    def validate_commands(self):
        """Validate command structure"""
        print("🎮 Validating commands...")
        
        try:
            # Count command files
            command_files = list((self.root_path / "beta" / "commands").glob("*_commands.py"))
            command_count = len(command_files)
            
            if command_count >= 7:  # Memory, Creative, Learning, Analytics, Personality, plus others
                self.successes.append(f"✅ Found {command_count} command modules")
            else:
                self.warnings.append(f"⚠️ Only found {command_count} command modules, expected 7+")
            
            # Check for help system
            help_file = self.root_path / "beta" / "commands" / "help_commands.py"
            if help_file.exists():
                self.successes.append("✅ Help system present")
            else:
                self.issues.append("❌ Help system missing")
                
        except Exception as e:
            self.issues.append(f"❌ Command validation error: {e}")
    
    def validate_file_structure(self):
        """Validate file structure"""
        print("📁 Validating file structure...")
        
        required_dirs = [
            "app/commands",
            "app/services",
            "app/config",
            "app/utils",
            "app/core",
            "app/interfaces"
        ]
        
        for dir_path in required_dirs:
            full_path = self.root_path / dir_path
            if full_path.exists():
                self.successes.append(f"✅ Directory exists: {dir_path}")
            else:
                self.issues.append(f"❌ Missing directory: {dir_path}")
        
        # Check for key files
        required_files = [
            "app/main.py",
            "requirements.txt",
            "README.md",
            ".gitignore"
        ]
        
        for file_path in required_files:
            full_path = self.root_path / file_path
            if full_path.exists():
                self.successes.append(f"✅ File exists: {file_path}")
            else:
                self.issues.append(f"❌ Missing file: {file_path}")
    
    def validate_data_files(self):
        """Validate data file structure"""
        print("💾 Validating data files...")
        
        # Check if data files exist (they may not exist initially)
        data_files = [
            "data/user_memories.json",
            "data/learning_data.json",
            "data/analytics_data.json"
        ]
        
        for data_file in data_files:
            file_path = self.root_path / data_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                    self.successes.append(f"✅ Valid JSON: {data_file}")
                except json.JSONDecodeError:
                    self.issues.append(f"❌ Invalid JSON: {data_file}")
            else:
                self.warnings.append(f"⚠️ Data file not found (will be created): {data_file}")
    
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 50)
        print("📋 VALIDATION REPORT")
        print("=" * 50)
        
        print(f"✅ Successes: {len(self.successes)}")
        for success in self.successes:
            print(f"  {success}")
        
        print(f"\n⚠️ Warnings: {len(self.warnings)}")
        for warning in self.warnings:
            print(f"  {warning}")
        
        print(f"\n❌ Issues: {len(self.issues)}")
        for issue in self.issues:
            print(f"  {issue}")
        
        # Overall status
        print(f"\n🎯 OVERALL STATUS:")
        if not self.issues:
            if not self.warnings:
                print("🟢 EXCELLENT - System fully operational with no issues")
            else:
                print("🟡 GOOD - System operational with minor warnings")
        else:
            print("🔴 NEEDS ATTENTION - Critical issues found")
        
        # Summary stats
        total_checks = len(self.successes) + len(self.warnings) + len(self.issues)
        success_rate = (len(self.successes) / total_checks * 100) if total_checks > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}% ({len(self.successes)}/{total_checks})")
        
        success = len(self.issues) == 0
        if success:
            print("\n🚀 System is ready for deployment!")
        else:
            print("\n🔧 Please address the issues before deployment.")
        return success

def main():
    validator = SystemValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🚀 System is ready for deployment!")
        return 0
    else:
        print("\n🔧 Please address the issues before deployment.")
        return 1

if __name__ == "__main__":
    exit(main())