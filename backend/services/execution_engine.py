"""
Asynchronous execution engine for multi-agent task processing.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Agent, Task, Execution, AgentStatus, TaskStatus
from schemas import TaskExecutionRequest, ExecutionResponse, SystemStatus, TaskExecutionResponse


class ExecutionEngine:
    """Manages asynchronous execution of tasks by agents."""
    
    def __init__(self):
        self.running_executions: Dict[str, asyncio.Task] = {}
        self.agent_instances: Dict[str, Any] = {}  # Placeholder for agent instances
        self.websocket_manager = None  # Will be injected
        
    def set_websocket_manager(self, websocket_manager: Any):
        """Inject WebSocket manager for real-time updates."""
        self.websocket_manager = websocket_manager
    
    async def start_task_execution(self, db: Session, request: TaskExecutionRequest) -> TaskExecutionResponse:
        """Start executing a task with specified agents."""
        
        # Get task from database
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task:
            raise ValueError(f"Task {request.task_id} not found")
        
        # Determine which agents to use
        agent_ids = request.agent_ids or [agent.id for agent in task.assigned_agents]
        if not agent_ids:
            raise ValueError("No agents assigned to task")
        
        # Get agents from database
        agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        if len(agents) != len(agent_ids):
            raise ValueError("Some specified agents not found")
        
        # Check if agents are available
        busy_agents = [agent for agent in agents if agent.status == AgentStatus.EXECUTING]
        if busy_agents and not request.force_restart:
            busy_names = [agent.name for agent in busy_agents]
            raise ValueError(f"Agents are busy: {busy_names}. Use force_restart=true to override.")
        
        # Create execution record
        execution = Execution(
            task_id=task.id,
            agent_id=agents[0].id,  # Primary agent
            status="starting",
            start_time=datetime.utcnow(),
            logs=[{"timestamp": datetime.utcnow().isoformat(), "message": "Execution starting", "level": "info"}]
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Update agent statuses
        for agent in agents:
            agent.status = AgentStatus.EXECUTING
            agent.last_active = datetime.utcnow()
        db.commit()
        
        # Start asynchronous execution
        execution_task = asyncio.create_task(
            self._execute_task_async(db, execution.id, task, agents)
        )
        self.running_executions[execution.id] = execution_task
        
        return TaskExecutionResponse(
            execution_id=execution.id,
            task_id=task.id,
            status="started",
            message=f"Task execution started with {len(agents)} agent(s)",
            started_at=execution.start_time
        )
    
    async def _execute_task_async(self, db: Session, execution_id: str, task: Task, agents: List[Agent]):
        """Execute task asynchronously with multiple agents."""
        
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        
        try:
            # Initialize agent instances if needed
            for agent in agents:
                if agent.id not in self.agent_instances:
                    # Placeholder for agent wrapper - will be implemented with actual MCP integration
                    self.agent_instances[agent.id] = {
                        "agent": agent,
                        "initialized": True,
                        "status": "ready"
                    }
            
            # Update execution status
            execution.status = "running"
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Starting task execution with agents: {[a.name for a in agents]}",
                "level": "info"
            })
            db.commit()
            
            # Broadcast execution update
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "execution_update",
                    "execution_id": execution_id,
                    "status": "running",
                    "message": "Task execution in progress",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Execute task based on number of agents
            if len(agents) == 1:
                # Single agent execution
                result = await self._execute_single_agent(agents[0], task, execution, db)
            else:
                # Multi-agent collaboration
                result = await self._execute_multi_agent(agents, task, execution, db)
            
            # Update task and execution with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.results = result
            
            execution.status = "completed"
            execution.end_time = datetime.utcnow()
            execution.output = result
            execution.duration_seconds = str((execution.end_time - execution.start_time).total_seconds())
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Task execution completed successfully",
                "level": "info"
            })
            
            # Update agent statuses
            for agent in agents:
                agent.status = AgentStatus.IDLE
                agent.last_active = datetime.utcnow()
            
            db.commit()
            
            # Broadcast completion
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "execution_completed",
                    "execution_id": execution_id,
                    "task_id": task.id,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            # Handle execution error
            error_message = str(e)
            
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            
            execution.status = "failed"
            execution.end_time = datetime.utcnow()
            execution.error_details = {"error": error_message, "type": type(e).__name__}
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Task execution failed: {error_message}",
                "level": "error"
            })
            
            # Reset agent statuses
            for agent in agents:
                agent.status = AgentStatus.ERROR
                agent.last_active = datetime.utcnow()
            
            db.commit()
            
            # Broadcast error
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    "type": "execution_failed",
                    "execution_id": execution_id,
                    "task_id": task.id,
                    "error": error_message,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        finally:
            # Clean up
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
    
    async def _execute_single_agent(self, agent: Agent, task: Task, execution: Execution, db: Session) -> Dict[str, Any]:
        """Execute task with a single agent."""
        
        agent_instance = self.agent_instances[agent.id]
        
        # Prepare task context
        task_context = {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "expected_output": task.expected_output,
            "resources": task.resources,
            "priority": task.priority.value,
            "deadline": task.deadline.isoformat() if task.deadline else None
        }
        
        # Execute task (mock implementation for now)
        await asyncio.sleep(1)  # Simulate task execution
        result = {
            "status": "completed",
            "message": f"Task '{task.title}' executed by agent {agent.name}",
            "output": f"Mock execution result for task: {task.description}",
            "agent_capabilities_used": agent.capabilities[:3]  # Use first 3 capabilities
        }
        
        # Log progress
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Agent {agent.name} completed task",
            "level": "info",
            "agent_id": agent.id
        })
        db.commit()
        
        return {
            "primary_agent": agent.name,
            "execution_type": "single_agent",
            "result": result,
            "completion_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_multi_agent(self, agents: List[Agent], task: Task, execution: Execution, db: Session) -> Dict[str, Any]:
        """Execute task with multiple agents collaborating."""
        
        primary_agent = agents[0]
        collaborating_agents = agents[1:]
        
        # Phase 1: Primary agent analyzes task and creates plan
        primary_instance = self.agent_instances[primary_agent.id]
        
        planning_context = {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "expected_output": task.expected_output,
            "resources": task.resources,
            "priority": task.priority.value,
            "collaborating_agents": [{"name": agent.name, "role": agent.role, "capabilities": agent.capabilities} for agent in collaborating_agents],
            "phase": "planning"
        }
        
        # Create execution plan (mock implementation)
        await asyncio.sleep(0.5)  # Simulate planning
        plan = {
            "status": "planned",
            "strategy": f"Multi-agent execution strategy for: {task.title}",
            "subtasks": [
                f"Subtask 1: Research and analysis for {task.description[:50]}...",
                f"Subtask 2: Implementation planning",
                f"Subtask 3: Quality review and validation"
            ],
            "estimated_duration": "5-10 minutes",
            "agent_assignments": [agent.name for agent in collaborating_agents]
        }
        
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Primary agent {primary_agent.name} created execution plan",
            "level": "info",
            "agent_id": primary_agent.id
        })
        db.commit()
        
        # Broadcast planning completion
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "planning_completed",
                "execution_id": execution.id,
                "plan": plan,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Phase 2: Execute subtasks with collaborating agents
        subtask_results = {}
        
        if collaborating_agents and isinstance(plan, dict) and "subtasks" in plan:
            # Execute subtasks in parallel
            subtask_futures = []
            
            for i, subtask in enumerate(plan["subtasks"]):
                if i < len(collaborating_agents):
                    agent = collaborating_agents[i]
                    agent_instance = self.agent_instances[agent.id]
                    
                    subtask_context = {
                        "task_id": task.id,
                        "subtask": subtask,
                        "parent_plan": plan,
                        "phase": "execution"
                    }
                    
                    # Mock subtask execution
                    async def execute_subtask(agent, subtask):
                        await asyncio.sleep(0.5)  # Simulate work
                        return {
                            "status": "completed",
                            "subtask": subtask,
                            "agent": agent.name,
                            "output": f"Completed: {subtask}",
                            "capabilities_used": agent.capabilities[:2]
                        }
                    
                    future = execute_subtask(agent, subtask)
                    subtask_futures.append((agent, future))
            
            # Wait for all subtasks to complete
            for agent, future in subtask_futures:
                try:
                    result = await future
                    subtask_results[agent.name] = result
                    
                    execution.logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Agent {agent.name} completed subtask",
                        "level": "info",
                        "agent_id": agent.id
                    })
                    
                except Exception as e:
                    subtask_results[agent.name] = {"error": str(e)}
                    
                    execution.logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Agent {agent.name} failed subtask: {str(e)}",
                        "level": "error",
                        "agent_id": agent.id
                    })
            
            db.commit()
        
        # Phase 3: Primary agent synthesizes results
        synthesis_context = {
            "task_id": task.id,
            "original_task": {
                "title": task.title,
                "description": task.description,
                "expected_output": task.expected_output
            },
            "plan": plan,
            "subtask_results": subtask_results,
            "phase": "synthesis"
        }
        
        final_result = await primary_instance.execute_task(synthesis_context)
        
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Primary agent {primary_agent.name} synthesized final result",
            "level": "info",
            "agent_id": primary_agent.id
        })
        db.commit()
        
        return {
            "primary_agent": primary_agent.name,
            "collaborating_agents": [agent.name for agent in collaborating_agents],
            "execution_type": "multi_agent_collaboration",
            "plan": plan,
            "subtask_results": subtask_results,
            "final_result": final_result,
            "completion_time": datetime.utcnow().isoformat()
        }
    
    async def stop_execution(self, db: Session, execution_id: str):
        """Stop a running execution."""
        
        if execution_id in self.running_executions:
            # Cancel the asyncio task
            self.running_executions[execution_id].cancel()
            del self.running_executions[execution_id]
            
            # Update database
            execution = db.query(Execution).filter(Execution.id == execution_id).first()
            if execution:
                execution.status = "cancelled"
                execution.end_time = datetime.utcnow()
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Execution cancelled by user",
                    "level": "warning"
                })
                
                # Update task status
                task = db.query(Task).filter(Task.id == execution.task_id).first()
                if task:
                    task.status = TaskStatus.CANCELLED
                
                # Reset agent statuses
                agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
                if agent:
                    agent.status = AgentStatus.IDLE
                
                db.commit()
    
    async def get_system_status(self, db: Session) -> SystemStatus:
        """Get overall system status and metrics."""
        
        # Count agents by status
        total_agents = db.query(Agent).count()
        active_agents = db.query(Agent).filter(Agent.status == AgentStatus.EXECUTING).count()
        
        # Count tasks by status
        total_tasks = db.query(Task).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        running_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        failed_tasks = db.query(Task).filter(Task.status == TaskStatus.FAILED).count()
        
        return SystemStatus(
            total_agents=total_agents,
            active_agents=active_agents,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            system_uptime="24:00:00",  # TODO: Calculate actual uptime
            memory_usage={"used": "256MB", "total": "1GB"},  # TODO: Get actual memory usage
            last_updated=datetime.utcnow()
        )
    
    async def get_all_executions(self, db: Session) -> List[ExecutionResponse]:
        """Get all executions."""
        executions = db.query(Execution).all()
        return [ExecutionResponse.from_orm(execution) for execution in executions]
    
    async def get_execution(self, db: Session, execution_id: str) -> Optional[ExecutionResponse]:
        """Get specific execution by ID."""
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        return ExecutionResponse.from_orm(execution) if execution else None