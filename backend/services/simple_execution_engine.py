"""
Simple execution engine for multi-agent task processing.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

class ExecutionEngine:
    """Simple execution engine for agent tasks."""
    
    def __init__(self):
        self.running_tasks: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
    
    async def execute_task(self, task_id: str, agent_ids: List[str], db: Session) -> Dict[str, Any]:
        """Execute a task with specified agents."""
        
        execution_id = f"exec_{int(time.time())}"
        
        # Mock execution for demo
        execution_data = {
            "id": execution_id,
            "task_id": task_id,
            "agent_ids": agent_ids,
            "status": "completed",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "result": {
                "message": f"Task {task_id} completed successfully by agents {agent_ids}",
                "output": "Mock task execution completed",
                "execution_time": "2.5 seconds"
            }
        }
        
        self.task_history.append(execution_data)
        return execution_data
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific execution."""
        for exec_data in self.task_history:
            if exec_data["id"] == execution_id:
                return exec_data
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "total_executions": len(self.task_history),
            "running_executions": len(self.running_tasks),
            "completed_executions": len([e for e in self.task_history if e["status"] == "completed"]),
            "failed_executions": len([e for e in self.task_history if e["status"] == "failed"]),
            "last_updated": datetime.now()
        }