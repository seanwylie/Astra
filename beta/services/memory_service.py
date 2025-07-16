"""
Memory Service for Astra Beta
Handles conversation memory, user information storage, and context retention.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
from fuzzywuzzy import fuzz
import os

class MemoryService:
    def __init__(self):
        self.memories = {}
        self.conversation_context = []
        self.max_context_length = 50
        self.memory_file = "data/user_memories.json"
        self.load_memories()
    
    def load_memories(self):
        """Load memories from persistent storage"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.memories = data.get('memories', {})
                self.conversation_context = data.get('context', [])
        except FileNotFoundError:
            self.memories = {}
            self.conversation_context = []
        except Exception as e:
            print(f"Error loading memories: {e}")
            self.memories = {}
            self.conversation_context = []
    
    def save_memories(self):
        """Save memories to persistent storage"""
        try:
            data = {
                'memories': self.memories,
                'context': self.conversation_context[-self.max_context_length:],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving memories: {e}")
    
    def remember(self, key: str, value: str, user_id: str = "default") -> str:
        """Store a memory with key-value pair"""
        if user_id not in self.memories:
            self.memories[user_id] = {}
        
        # Clean and normalize the key
        clean_key = key.lower().strip()
        
        # Store with metadata
        self.memories[user_id][clean_key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'access_count': 0
        }
        
        self.save_memories()
        return f"✅ Remembered: {key} → {value}"
    
    def recall(self, key: str, user_id: str = "default") -> str:
        """Retrieve a memory by key"""
        if user_id not in self.memories:
            return f"❌ No memories found for this user"
        
        clean_key = key.lower().strip()
        
        # Exact match first
        if clean_key in self.memories[user_id]:
            memory = self.memories[user_id][clean_key]
            memory['access_count'] += 1
            memory['last_accessed'] = datetime.now().isoformat()
            self.save_memories()
            return f"💭 {key}: {memory['value']}"
        
        # Fuzzy search for similar keys
        best_match = None
        best_score = 0
        
        for stored_key in self.memories[user_id].keys():
            score = fuzz.ratio(clean_key, stored_key)
            if score > best_score and score > 60:  # 60% similarity threshold
                best_score = score
                best_match = stored_key
        
        if best_match:
            memory = self.memories[user_id][best_match]
            memory['access_count'] += 1
            memory['last_accessed'] = datetime.now().isoformat()
            self.save_memories()
            return f"💭 {best_match}: {memory['value']} (fuzzy match: {best_score}%)"
        
        return f"❌ No memory found for '{key}'"
    
    def forget(self, key: str, user_id: str = "default") -> str:
        """Remove a memory by key"""
        if user_id not in self.memories:
            return f"❌ No memories found for this user"
        
        clean_key = key.lower().strip()
        
        if clean_key in self.memories[user_id]:
            value = self.memories[user_id][clean_key]['value']
            del self.memories[user_id][clean_key]
            self.save_memories()
            return f"🗑️ Forgot: {key} → {value}"
        
        return f"❌ No memory found for '{key}'"
    
    def memory_summary(self, user_id: str = "default") -> str:
        """Get a summary of all stored memories"""
        if user_id not in self.memories or not self.memories[user_id]:
            return "📝 No memories stored yet"
        
        memories = self.memories[user_id]
        summary_lines = ["📝 **Memory Summary:**\n"]
        
        # Sort by access count (most accessed first)
        sorted_memories = sorted(
            memories.items(),
            key=lambda x: x[1].get('access_count', 0),
            reverse=True
        )
        
        for key, data in sorted_memories:
            access_info = f" (accessed {data.get('access_count', 0)} times)" if data.get('access_count', 0) > 0 else ""
            summary_lines.append(f"• **{key}**: {data['value']}{access_info}")
        
        summary_lines.append(f"\n📊 Total memories: {len(memories)}")
        return "\n".join(summary_lines)
    
    def add_context(self, message: str, user_id: str = "default", is_user: bool = True):
        """Add message to conversation context"""
        context_entry = {
            'message': message,
            'user_id': user_id,
            'is_user': is_user,
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversation_context.append(context_entry)
        
        # Keep only recent context
        if len(self.conversation_context) > self.max_context_length:
            self.conversation_context = self.conversation_context[-self.max_context_length:]
        
        self.save_memories()
    
    def get_context(self, user_id: str = "default", limit: int = 10) -> List[Dict]:
        """Get recent conversation context for a user"""
        user_context = [
            entry for entry in self.conversation_context
            if entry.get('user_id') == user_id
        ]
        return user_context[-limit:]
    
    def search_memories(self, query: str, user_id: str = "default") -> str:
        """Search through memories using fuzzy matching"""
        if user_id not in self.memories or not self.memories[user_id]:
            return "❌ No memories to search"
        
        query_lower = query.lower()
        matches = []
        
        for key, data in self.memories[user_id].items():
            # Search in both key and value
            key_score = fuzz.partial_ratio(query_lower, key.lower())
            value_score = fuzz.partial_ratio(query_lower, data['value'].lower())
            max_score = max(key_score, value_score)
            
            if max_score > 60:  # 60% similarity threshold for search
                matches.append((key, data['value'], max_score))
        
        if not matches:
            return f"❌ No memories found matching '{query}'"
        
        # Sort by relevance score
        matches.sort(key=lambda x: x[2], reverse=True)
        
        result_lines = [f"🔍 **Search results for '{query}':**\n"]
        for key, value, score in matches[:5]:  # Top 5 results
            result_lines.append(f"• **{key}**: {value} ({score}% match)")
        
        return "\n".join(result_lines)
    
    def get_memory_stats(self, user_id: str = "default") -> str:
        """Get statistics about stored memories"""
        if user_id not in self.memories or not self.memories[user_id]:
            return "📊 No memory statistics available"
        
        memories = self.memories[user_id]
        total_memories = len(memories)
        
        # Calculate access statistics
        total_accesses = sum(data.get('access_count', 0) for data in memories.values())
        avg_accesses = total_accesses / total_memories if total_memories > 0 else 0
        
        # Find most accessed memory
        most_accessed = max(memories.items(), key=lambda x: x[1].get('access_count', 0))
        
        # Calculate age statistics
        now = datetime.now()
        ages = []
        for data in memories.values():
            try:
                created = datetime.fromisoformat(data['timestamp'])
                age_days = (now - created).days
                ages.append(age_days)
            except:
                continue
        
        avg_age = sum(ages) / len(ages) if ages else 0
        
        stats = [
            "📊 **Memory Statistics:**",
            f"• Total memories: {total_memories}",
            f"• Total accesses: {total_accesses}",
            f"• Average accesses per memory: {avg_accesses:.1f}",
            f"• Most accessed: {most_accessed[0]} ({most_accessed[1].get('access_count', 0)} times)",
            f"• Average memory age: {avg_age:.1f} days"
        ]
        
        return "\n".join(stats)

# Global memory service instance
memory_service = MemoryService()