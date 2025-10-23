"""
Simple file-based memory system for conversation history.
This replaces the mem0 dependency which requires OpenAI API access.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
import uuid


class SimpleMemory:
    """Simple file-based memory system for storing conversation history."""
    
    def __init__(self, memory_dir: str = "memory"):
        """Initialize the memory system.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: str) -> str:
        """Get the memory file path for a user."""
        return os.path.join(self.memory_dir, f"{user_id}.json")
    
    def _load_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Load memories for a user."""
        file_path = self._get_user_file(user_id)
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_memories(self, user_id: str, memories: List[Dict[str, Any]]):
        """Save memories for a user."""
        file_path = self._get_user_file(user_id)
        try:
            with open(file_path, 'w') as f:
                json.dump(memories, f, indent=2)
        except IOError:
            pass  # Fail silently
    
    def store(self, content: str, user_id: str, memory_type: str = "general") -> Dict[str, Any]:
        """Store a memory.
        
        Args:
            content: The content to store
            user_id: User identifier
            memory_type: Type of memory (e.g., 'user_question', 'command_execution')
            
        Returns:
            Dictionary with storage result
        """
        memories = self._load_memories(user_id)
        
        memory_entry = {
            "id": str(uuid.uuid4()),
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        memories.append(memory_entry)
        
        # Keep only last 100 memories to prevent file from growing too large
        if len(memories) > 100:
            memories = memories[-100:]
        
        self._save_memories(user_id, memories)
        
        return {
            "status": "success",
            "memory_id": memory_entry["id"]
        }
    
    def retrieve(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories based on a query.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        memories = self._load_memories(user_id)
        
        # Simple text-based search
        query_lower = query.lower()
        matching_memories = []
        
        for memory in reversed(memories):  # Search from most recent
            content_lower = memory["content"].lower()
            if any(word in content_lower for word in query_lower.split()):
                matching_memories.append({
                    "memory": memory["content"],
                    "id": memory["id"],
                    "type": memory["type"],
                    "timestamp": memory["timestamp"]
                })
                
                if len(matching_memories) >= limit:
                    break
        
        return matching_memories
    
    def list_memories(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent memories for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of recent memories
        """
        memories = self._load_memories(user_id)
        
        # Return most recent memories
        recent_memories = memories[-limit:] if len(memories) > limit else memories
        
        return [{
            "memory": memory["content"],
            "id": memory["id"],
            "type": memory["type"],
            "timestamp": memory["timestamp"]
        } for memory in reversed(recent_memories)]
