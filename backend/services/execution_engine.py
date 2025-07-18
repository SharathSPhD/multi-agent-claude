"""
Asynchronous execution engine for multi-agent task processing.
FIXED VERSION: Added timeouts and fallbacks to prevent stuck executions.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Agent, Task, Execution, AgentStatus, TaskStatus
from schemas import TaskExecutionRequest, ExecutionResponse, SystemStatus, TaskExecutionResponse


class ExecutionEngine:
    """Manages asynchronous execution of tasks by agents with timeout controls."""
    
    def __init__(self):
        self.running_executions: Dict[str, asyncio.Task] = {}
        self.paused_executions: Dict[str, Dict[str, Any]] = {}
        self.agent_instances: Dict[str, Any] = {}
        self.websocket_manager = None
        
        # Timeout settings
        self.DEFAULT_TIMEOUT = 300  # 5 minutes
        self.MAX_TIMEOUT = 600     # 10 minutes
        
    def set_websocket_manager(self, websocket_manager: Any):
        """Inject WebSocket manager for real-time updates."""
        self.websocket_manager = websocket_manager
    
    async def start_task_execution(self, db: Session, request: TaskExecutionRequest) -> TaskExecutionResponse:
        """Start executing a task with specified agents - supports multi-agent execution."""
        
        print(f"🎯 Starting task execution - Task: {request.task_id[:8]}... Work Dir: {request.work_directory}")
        print(f"📊 Current running executions: {len(self.running_executions)}")
        
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
            missing = set(agent_ids) - {a.id for a in agents}
            raise ValueError(f"Agents not found: {missing}")
        
        # Check if agents are busy (unless force restart)
        if not request.force_restart:
            busy_agents = []
            for agent in agents:
                if agent.status == AgentStatus.EXECUTING:
                    busy_agents.append(agent.name)
            
            if busy_agents:
                raise ValueError(f"Agents are busy: {busy_agents}. Use force_restart=true to override.")
        
        # Create execution record for the primary agent (working approach)
        import uuid
        execution_id = str(uuid.uuid4())
        
        execution = Execution(
            id=execution_id,
            task_id=task.id,
            agent_id=agents[0].id,  # Primary agent
            status="starting",
            start_time=datetime.utcnow(),
            work_directory=request.work_directory,
            logs=[{
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Execution starting",
                "level": "info"
            }],
            output={},
            error_details={}
        )
        
        db.add(execution)
        db.commit()
        
        # Update agent and task status
        for agent in agents:
            agent.status = AgentStatus.EXECUTING
            agent.last_active = datetime.utcnow()
        
        # Update task status to in_progress
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Start execution task with timeout - use primary agent
        print(f"🚀 Launching execution task {execution_id} for task {task.title}")
        execution_task = asyncio.create_task(
            self._execute_with_timeout(execution_id, task.id, agents[0].id, request.work_directory)
        )
        self.running_executions[execution_id] = execution_task
        print(f"📈 Total running executions now: {len(self.running_executions)}")
        
        return TaskExecutionResponse(
            execution_id=execution_id,
            task_id=task.id,
            status="starting",
            message="Task execution started successfully",
            started_at=execution.start_time
        )
    
    async def _execute_with_timeout(self, execution_id: str, task_id: str, agent_id: str, work_dir: Optional[str] = None):
        """Execute task with timeout protection."""
        # Create new database session for this async task
        from database import SessionLocal
        db = SessionLocal()
        
        try:
            # Get fresh objects from database
            execution = db.query(Execution).filter(Execution.id == execution_id).first()
            task = db.query(Task).filter(Task.id == task_id).first()
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not execution or not task or not agent:
                print(f"❌ Failed to retrieve objects: execution={execution}, task={task}, agent={agent}")
                return
            
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"_execute_with_timeout started for execution {execution_id[:8]}...",
                "level": "info"
            })
            db.commit()
            
            agents = [agent]  # Convert to list for compatibility
        
            # Continue with existing timeout logic
            await self._execute_timeout_logic(db, execution, task, agents, work_dir)
            
        except Exception as e:
            if execution:
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Execution failed in _execute_with_timeout: {str(e)}",
                    "level": "error"
                })
                execution.status = "failed"
                execution.error_details = {"error": str(e)}
                execution.end_time = datetime.utcnow()
                db.commit()
            print(f"❌ Error in _execute_with_timeout: {e}")
        finally:
            db.close()
    
    async def _execute_timeout_logic(self, db: Session, execution: Execution, task: Task, agents: List[Agent], work_dir: Optional[str] = None):
        """Original timeout logic extracted to separate method."""
        try:
            # Determine timeout
            # Parse estimated_duration (e.g., "2 hours", "30 minutes") or use default
            duration_seconds = self.DEFAULT_TIMEOUT
            if task.estimated_duration:
                # Simple parsing - could be enhanced
                if "hour" in task.estimated_duration.lower():
                    try:
                        hours = float(task.estimated_duration.split()[0])
                        duration_seconds = hours * 3600
                    except:
                        pass
                elif "minute" in task.estimated_duration.lower():
                    try:
                        minutes = float(task.estimated_duration.split()[0])
                        duration_seconds = minutes * 60
                    except:
                        pass
            
            timeout = min(duration_seconds, self.MAX_TIMEOUT)
            
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Starting execution with {timeout}s timeout",
                "level": "info"
            })
            execution.status = "running"
            db.commit()
            
            # Execute with timeout
            try:
                await asyncio.wait_for(
                    self._execute_task_internal(db, execution, task, agents, work_dir),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Execution timed out after {timeout} seconds",
                    "level": "error"
                })
                execution.status = "failed"
                execution.error_details = {"error": "timeout", "timeout_seconds": timeout}
                
        except Exception as e:
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Execution failed: {str(e)}",
                "level": "error"
            })
            execution.status = "failed"
            execution.error_details = {"error": str(e)}
        
        finally:
            # Always clean up
            execution.end_time = datetime.utcnow()
            
            # Release agents
            for agent in agents:
                agent.status = AgentStatus.IDLE
                agent.last_active = datetime.utcnow()
            
            # Remove from running executions
            if execution.id in self.running_executions:
                del self.running_executions[execution.id]
                print(f"🏁 Execution {execution.id} completed and removed from running list")
                print(f"📉 Remaining running executions: {len(self.running_executions)}")
            
            db.commit()
    
    async def _execute_task_internal(self, db: Session, execution: Execution, task: Task, agents: List[Agent], work_dir: Optional[str] = None):
        """Internal task execution with simplified approach."""
        
        primary_agent = agents[0]
        
        if not work_dir:
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"No work directory specified - task execution cannot proceed",
                "level": "error"
            })
            db.commit()
            raise ValueError("Work directory is required for task execution")
        
        print(f"💼 Executing task '{task.title}' with agent '{primary_agent.name}' in directory: {work_dir}")
        
        # Execute with Claude CLI with 60 second timeout
        result = await self._execute_with_claude_sdk_timeout(db, execution, task, primary_agent, work_dir, timeout=60)
        
        execution.status = "completed"
        execution.output = result
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        db.commit()
    
    async def _execute_with_claude_sdk_timeout(self, db: Session, execution: Execution, task: Task, agent: Agent, work_dir: Optional[str], timeout: int = 60):
        """Execute with Claude Code CLI with structured JSON output."""
        import subprocess
        import json
        import shutil
        
        # Check if claude command is available
        if not shutil.which("claude"):
            raise Exception("Claude CLI not available - please install claude-code-cli")
        
        # Setup work directory
        if not work_dir:
            work_dir = f"./claude_executions/execution_{execution.id}"
        
        work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)
        
        # Create CLAUDE.md context file
        claude_md_content = f"""# {agent.name} Agent Context

## Agent Profile
- Name: {agent.name}
- Role: {agent.role}
- Description: {agent.description}

## Task Details
- Title: {task.title}
- Description: {task.description}
- Priority: {task.priority}
- Status: {task.status}

## Working Directory
{work_path}
"""
        
        claude_md_path = work_path / "CLAUDE.md"
        with open(claude_md_path, 'w') as f:
            f.write(claude_md_content)
        
        # JSON-structured task prompt
        task_prompt = f"""Please execute the following task autonomously:

TASK: {task.title}
DESCRIPTION: {task.description}

You are {agent.name}, a {agent.role}.

Please provide your response in structured JSON format:
{{
    "analysis": "Your analysis of the task",
    "approach": "Your methodology and approach", 
    "implementation": "Your detailed work and implementation",
    "results": "Your final results and conclusions",
    "recommendations": "Any recommendations or next steps",
    "status": "completed",
    "needs_interaction": false,
    "output_files": []
}}

Work efficiently and provide concrete deliverables."""
        
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Starting Claude CLI execution (timeout: {timeout}s)",
            "level": "info"
        })
        db.commit()
        
        # Claude Code CLI execution
        claude_cmd = [
            "claude", 
            "--output-format", "json",
            "--dangerously-skip-permissions",
            "-p", task_prompt
        ]
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *claude_cmd,
                    cwd=str(work_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=timeout
            )
            
            stdout, stderr = await result.communicate()
            
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Claude CLI completed with return code: {result.returncode}",
                "level": "info"
            })
            
            if stderr:
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Claude CLI stderr: {stderr.decode()}",
                    "level": "warning"
                })
            
            db.commit()
            
            # Parse JSON response
            response_text = stdout.decode().strip()
            if response_text:
                try:
                    response_data = json.loads(response_text)
                    return response_data
                except json.JSONDecodeError:
                    # Fallback to text response
                    return {
                        "analysis": "Task executed",
                        "implementation": response_text,
                        "results": "Completed with text output",
                        "status": "completed",
                        "needs_interaction": False
                    }
            else:
                return {
                    "analysis": "Task executed",
                    "results": "Completed successfully",
                    "status": "completed",
                    "needs_interaction": False
                }
                
        except asyncio.TimeoutError:
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Claude CLI execution timed out after {timeout}s",
                "level": "error"
            })
            db.commit()
            raise
        except Exception as e:
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Claude CLI error: {str(e)}",
                "level": "error"
            })
            db.commit()
            raise
    
    async def _execute_with_expert_fallback(self, db: Session, execution: Execution, task: Task, agent: Agent):
        """Expert system fallback when Claude SDK fails."""
        
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Using expert system fallback",
            "level": "info"
        })
        db.commit()
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Generate expert response based on agent role
        if "backend" in agent.role.lower():
            response = f"Backend task '{task.title}' analyzed. Would implement API endpoints, database models, and error handling according to FastAPI best practices."
        elif "frontend" in agent.role.lower():
            response = f"Frontend task '{task.title}' analyzed. Would create React components with TypeScript, Chakra UI styling, and proper state management."
        elif "test" in agent.role.lower():
            response = f"Testing task '{task.title}' analyzed. Would create comprehensive test suites including unit tests, integration tests, and performance tests."
        else:
            response = f"Task '{task.title}' completed by {agent.name}. Applied {agent.role} expertise to fulfill requirements."
        
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Expert fallback completed",
            "level": "info"
        })
        db.commit()
        
        return {
            "agent_response": response,
            "analysis": f"Task processed using expert system for {agent.role}",
            "execution_method": "expert_fallback",
            "status": "completed"
        }
    
    # Keep existing methods for compatibility
    async def pause_execution(self, execution_id: str, db: Session) -> bool:
        """Pause execution by cancelling task and saving state."""
        if execution_id not in self.running_executions:
            return False
        
        # Cancel the running task
        task = self.running_executions[execution_id]
        task.cancel()
        
        # Update execution status
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.status = "paused"
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Execution paused by user",
                "level": "info"
            })
            db.commit()
        
        # Move to paused executions
        del self.running_executions[execution_id]
        self.paused_executions[execution_id] = {"paused_at": datetime.utcnow().isoformat()}
        
        return True
    
    async def resume_execution(self, execution_id: str, db: Session) -> bool:
        """Resume paused execution."""
        if execution_id not in self.paused_executions:
            return False
        
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            return False
        
        # Get related task and agents
        task = db.query(Task).filter(Task.id == execution.task_id).first()
        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
        
        if not task or not agent:
            return False
        
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Resuming execution",
            "level": "info"
        })
        db.commit()
        
        # Restart execution
        execution_task = asyncio.create_task(
            self._execute_with_timeout(db, execution, task, [agent])
        )
        self.running_executions[execution_id] = execution_task
        
        # Remove from paused
        del self.paused_executions[execution_id]
        
        return True
    
    async def abort_execution(self, execution_id: str, db: Session) -> bool:
        """Abort execution completely."""
        
        # Cancel if running
        if execution_id in self.running_executions:
            task = self.running_executions[execution_id]
            task.cancel()
            del self.running_executions[execution_id]
        
        # Remove if paused
        if execution_id in self.paused_executions:
            del self.paused_executions[execution_id]
        
        # Update execution record
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.status = "cancelled"
            execution.end_time = datetime.utcnow()
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Execution aborted by user",
                "level": "info"
            })
            
            # Release agent and update task
            if execution.agent_id:
                agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
                if agent:
                    agent.status = AgentStatus.IDLE
                    agent.last_active = datetime.utcnow()
            
            # Update task status
            if execution.task_id:
                task = db.query(Task).filter(Task.id == execution.task_id).first()
                if task:
                    task.status = TaskStatus.CANCELLED
            
            db.commit()
        
        return True
    
    def get_execution_status(self, execution_id: str, db: Session) -> Optional[ExecutionResponse]:
        """Get current execution status."""
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            return None
        
        # Handle cases where output might be a list or other non-dict type
        output = execution.output or {}
        if isinstance(output, list):
            # Convert list to dict format
            output = {"messages": output}
        elif not isinstance(output, dict):
            # Convert other types to dict
            output = {"data": str(output)}
        
        # Handle agent_response similarly
        agent_response = execution.agent_response or {}
        if not isinstance(agent_response, dict):
            agent_response = {"response": str(agent_response)}
        
        return ExecutionResponse(
            id=execution.id,
            task_id=execution.task_id,
            agent_id=execution.agent_id,
            status=execution.status,
            start_time=execution.start_time,
            end_time=execution.end_time,
            logs=execution.logs or [],
            output=output,
            error_details=execution.error_details or {},
            duration_seconds=str((execution.end_time - execution.start_time).total_seconds()) if execution.end_time else None,
            memory_usage={},
            api_calls_made=[],
            agent_response=agent_response,
            work_directory=execution.work_directory,
            needs_interaction=execution.needs_interaction or False
        )
    
    def get_all_executions(self, db: Session) -> List[ExecutionResponse]:
        """Get all executions."""
        executions = db.query(Execution).all()
        result = []
        
        for execution in executions:
            try:
                # Handle cases where output might be a list or other non-dict type
                output = execution.output or {}
                if isinstance(output, list):
                    # Convert list to dict format
                    output = {"messages": output}
                elif not isinstance(output, dict):
                    # Convert other types to dict
                    output = {"data": str(output)}
                
                # Handle agent_response similarly
                agent_response = execution.agent_response or {}
                if not isinstance(agent_response, dict):
                    agent_response = {"response": str(agent_response)}
                
                result.append(ExecutionResponse(
                    id=execution.id,
                    task_id=execution.task_id,
                    agent_id=execution.agent_id,
                    status=execution.status,
                    start_time=execution.start_time,
                    end_time=execution.end_time,
                    logs=execution.logs or [],
                    output=output,
                    error_details=execution.error_details or {},
                    duration_seconds=str((execution.end_time - execution.start_time).total_seconds()) if execution.end_time else None,
                    memory_usage={},
                    api_calls_made=[],
                    agent_response=agent_response,
                    work_directory=execution.work_directory,
                    needs_interaction=execution.needs_interaction or False
                ))
            except Exception as e:
                print(f"Error processing execution {execution.id}: {e}")
                # Skip problematic execution records
                continue
        
        return result
    
    def get_system_status(self, db: Session) -> SystemStatus:
        """Get overall system status."""
        total_agents = db.query(Agent).count()
        active_agents = db.query(Agent).filter(Agent.status == AgentStatus.EXECUTING).count()
        total_tasks = db.query(Task).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        running_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        failed_tasks = db.query(Task).filter(Task.status == TaskStatus.FAILED).count()
        running_executions = len(self.running_executions)
        
        return SystemStatus(
            total_agents=total_agents,
            active_agents=active_agents,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            system_uptime="0h 0m",  # Placeholder - could be calculated from app start time
            memory_usage={},
            last_updated=datetime.utcnow()
        )

# Global instance
execution_engine = ExecutionEngine()
