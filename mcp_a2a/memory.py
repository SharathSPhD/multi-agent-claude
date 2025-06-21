"""
Agent memory management using MCP memory servers.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class AgentMemory:
    """
    Memory management for individual agents using MCP memory protocol.
    """
    
    def __init__(self, memory_store_name: str, base_path: Optional[Path] = None):
        self.memory_store_name = memory_store_name
        self.base_path = base_path or Path("/mnt/e/Development/mcp_a2a/memory")
        self.agent_memory_path = self.base_path / memory_store_name
        self.tasks_cache: Dict[str, Any] = {}
        self.results_cache: Dict[str, Any] = {}
        self.conversations_cache: List[Dict[str, Any]] = []
        self.logger = logger.bind(memory_store=memory_store_name)
        
    async def initialize(self):
        """Initialize agent memory store."""
        try:
            # Create memory directory structure
            self.agent_memory_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.agent_memory_path / "tasks").mkdir(exist_ok=True)
            (self.agent_memory_path / "results").mkdir(exist_ok=True)
            (self.agent_memory_path / "conversations").mkdir(exist_ok=True)
            (self.agent_memory_path / "knowledge").mkdir(exist_ok=True)
            
            # Load existing data
            await self._load_existing_data()
            
            self.logger.info("Agent memory initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize memory", error=str(e))
            raise
    
    async def _load_existing_data(self):
        """Load existing memory data from files."""
        try:
            # Load tasks
            tasks_file = self.agent_memory_path / "tasks" / "tasks.json"
            if tasks_file.exists():
                with open(tasks_file, 'r') as f:
                    self.tasks_cache = json.load(f)
            
            # Load results
            results_file = self.agent_memory_path / "results" / "results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    self.results_cache = json.load(f)
            
            # Load conversations
            conversations_file = self.agent_memory_path / "conversations" / "conversations.json"
            if conversations_file.exists():
                with open(conversations_file, 'r') as f:
                    self.conversations_cache = json.load(f)
                    
        except Exception as e:
            self.logger.warning("Could not load existing memory data", error=str(e))
    
    async def store_task(self, task_id: str, task: Dict[str, Any]):
        """Store task information in memory."""
        task_data = {
            "id": task_id,
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "status": "submitted"
        }
        
        self.tasks_cache[task_id] = task_data
        
        # Persist to file
        await self._save_tasks()
        
        self.logger.debug("Task stored in memory", task_id=task_id)
    
    async def store_result(self, task_id: str, result: Any):
        """Store task result in memory."""
        result_data = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        
        self.results_cache[task_id] = result_data
        
        # Update task status
        if task_id in self.tasks_cache:
            self.tasks_cache[task_id]["status"] = "completed"
            self.tasks_cache[task_id]["completed_at"] = datetime.now().isoformat()
        
        # Persist to files
        await self._save_results()
        await self._save_tasks()
        
        self.logger.debug("Result stored in memory", task_id=task_id)
    
    async def store_conversation(self, message: str, response: str, context: Optional[Dict[str, Any]] = None):
        """Store conversation exchange in memory."""
        conversation_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "context": context or {}
        }
        
        self.conversations_cache.append(conversation_data)
        
        # Keep only last 100 conversations in memory
        if len(self.conversations_cache) > 100:
            self.conversations_cache = self.conversations_cache[-100:]
        
        # Persist to file
        await self._save_conversations()
        
        self.logger.debug("Conversation stored in memory")
    
    async def store_knowledge(self, key: str, value: Any, category: str = "general"):
        """Store knowledge/facts in memory."""
        knowledge_file = self.agent_memory_path / "knowledge" / f"{category}.json"
        
        # Load existing knowledge
        knowledge_data = {}
        if knowledge_file.exists():
            try:
                with open(knowledge_file, 'r') as f:
                    knowledge_data = json.load(f)
            except:
                pass
        
        # Store new knowledge
        knowledge_data[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save back to file
        knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        with open(knowledge_file, 'w') as f:
            json.dump(knowledge_data, f, indent=2)
        
        self.logger.debug("Knowledge stored", key=key, category=category)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task information from memory."""
        return self.tasks_cache.get(task_id)
    
    async def get_result(self, task_id: str) -> Optional[Any]:
        """Retrieve task result from memory."""
        result_data = self.results_cache.get(task_id)
        return result_data.get("result") if result_data else None
    
    async def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations from memory."""
        return self.conversations_cache[-limit:] if self.conversations_cache else []
    
    async def get_knowledge(self, key: str, category: str = "general") -> Optional[Any]:
        """Retrieve knowledge from memory."""
        knowledge_file = self.agent_memory_path / "knowledge" / f"{category}.json"
        
        if not knowledge_file.exists():
            return None
        
        try:
            with open(knowledge_file, 'r') as f:
                knowledge_data = json.load(f)
                entry = knowledge_data.get(key)
                return entry.get("value") if entry else None
        except:
            return None
    
    async def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search tasks by description or content."""
        results = []
        query_lower = query.lower()
        
        for task_data in self.tasks_cache.values():
            task = task_data.get("task", {})
            description = task.get("description", "").lower()
            content = str(task).lower()
            
            if query_lower in description or query_lower in content:
                results.append(task_data)
        
        return results
    
    async def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Search conversations by content."""
        results = []
        query_lower = query.lower()
        
        for conv in self.conversations_cache:
            message = conv.get("message", "").lower()
            response = conv.get("response", "").lower()
            
            if query_lower in message or query_lower in response:
                results.append(conv)
        
        return results
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored tasks."""
        total_tasks = len(self.tasks_cache)
        completed_tasks = sum(1 for task in self.tasks_cache.values() 
                             if task.get("status") == "completed")
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks,
            "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
        }
    
    async def _save_tasks(self):
        """Save tasks cache to file."""
        tasks_file = self.agent_memory_path / "tasks" / "tasks.json"
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(tasks_file, 'w') as f:
            json.dump(self.tasks_cache, f, indent=2)
    
    async def _save_results(self):
        """Save results cache to file."""
        results_file = self.agent_memory_path / "results" / "results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results_cache, f, indent=2)
    
    async def _save_conversations(self):
        """Save conversations cache to file."""
        conversations_file = self.agent_memory_path / "conversations" / "conversations.json"
        conversations_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(conversations_file, 'w') as f:
            json.dump(self.conversations_cache, f, indent=2)
    
    async def clear_memory(self, confirm: bool = False):
        """Clear all memory data (use with caution)."""
        if not confirm:
            raise ValueError("Must confirm memory clearing with confirm=True")
        
        self.tasks_cache.clear()
        self.results_cache.clear()
        self.conversations_cache.clear()
        
        # Clear files
        for file_path in [
            self.agent_memory_path / "tasks" / "tasks.json",
            self.agent_memory_path / "results" / "results.json",
            self.agent_memory_path / "conversations" / "conversations.json"
        ]:
            if file_path.exists():
                file_path.unlink()
        
        # Clear knowledge files
        knowledge_dir = self.agent_memory_path / "knowledge"
        if knowledge_dir.exists():
            for knowledge_file in knowledge_dir.glob("*.json"):
                knowledge_file.unlink()
        
        self.logger.warning("Agent memory cleared")


class SystemMemory:
    """
    System-wide memory management for the multi-agent system.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path("/mnt/e/Development/mcp_a2a/memory")
        self.agent_memories: Dict[str, AgentMemory] = {}
        self.system_events: List[Dict[str, Any]] = []
        self.logger = logger.bind(component="system_memory")
    
    async def initialize(self):
        """Initialize system memory."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger.info("System memory initialized")
    
    async def get_agent_memory(self, agent_name: str) -> AgentMemory:
        """Get or create agent memory."""
        if agent_name not in self.agent_memories:
            agent_memory = AgentMemory(f"{agent_name}_memory", self.base_path)
            await agent_memory.initialize()
            self.agent_memories[agent_name] = agent_memory
        
        return self.agent_memories[agent_name]
    
    async def log_system_event(self, event_type: str, description: str, data: Optional[Dict[str, Any]] = None):
        """Log system-wide events."""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "data": data or {}
        }
        
        self.system_events.append(event)
        
        # Keep only last 1000 events
        if len(self.system_events) > 1000:
            self.system_events = self.system_events[-1000:]
        
        # Persist to file
        events_file = self.base_path / "system_events.json"
        with open(events_file, 'w') as f:
            json.dump(self.system_events, f, indent=2)
        
        self.logger.info("System event logged", event_type=event_type)
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        agent_stats = {}
        
        for agent_name, memory in self.agent_memories.items():
            agent_stats[agent_name] = await memory.get_task_statistics()
        
        return {
            "agent_count": len(self.agent_memories),
            "total_events": len(self.system_events),
            "agent_statistics": agent_stats
        }