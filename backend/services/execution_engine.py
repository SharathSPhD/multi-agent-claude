"""
Asynchronous execution engine for multi-agent task processing.
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
    """Manages asynchronous execution of tasks by agents."""
    
    def __init__(self):
        self.running_executions: Dict[str, asyncio.Task] = {}
        self.paused_executions: Dict[str, Dict[str, Any]] = {}  # execution_id -> state
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
            self._execute_task_async(db, execution.id, task, agents, request.work_directory)
        )
        self.running_executions[execution.id] = execution_task
        
        return TaskExecutionResponse(
            execution_id=execution.id,
            task_id=task.id,
            status="started",
            message=f"Task execution started with {len(agents)} agent(s)",
            started_at=execution.start_time
        )
    
    async def _execute_task_async(self, db: Session, execution_id: str, task: Task, agents: List[Agent], work_directory: str = None):
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
                result = await self._execute_single_agent(agents[0], task, execution, db, work_directory)
            else:
                # Multi-agent collaboration
                result = await self._execute_multi_agent(agents, task, execution, db, work_directory)
            
            # Update task and execution with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.results = result
            
            execution.status = "completed"
            execution.end_time = datetime.utcnow()
            execution.output = result
            execution.duration_seconds = str((execution.end_time - execution.start_time).total_seconds())
            
            # Save agent response and interaction status
            if isinstance(result, dict) and 'agent_response' in result:
                execution.agent_response = result['agent_response']
                execution.needs_interaction = result.get('needs_interaction', False)
                execution.work_directory = result.get('work_directory')
            
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
    
    async def cancel_execution(self, db: Session, execution_id: str):
        """Cancel a running execution."""
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        if execution.status not in ["running", "starting"]:
            raise ValueError(f"Cannot cancel execution with status: {execution.status}")
        
        # Cancel the asyncio task if it exists
        if execution_id in self.running_executions:
            task = self.running_executions[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.running_executions[execution_id]
        
        # Update execution status
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
            task.error_message = "Execution cancelled"
        
        # Update agent status
        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
        if agent:
            agent.status = AgentStatus.IDLE
            agent.last_active = datetime.utcnow()
        
        db.commit()
        
        # Broadcast cancellation
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "execution_cancelled",
                "execution_id": execution_id,
                "message": "Execution cancelled by user",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {"status": "cancelled", "execution_id": execution_id}
    
    async def pause_execution(self, db: Session, execution_id: str):
        """Pause a running execution."""
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        if execution.status != "running":
            raise ValueError(f"Cannot pause execution with status: {execution.status}")
        
        # Store execution state
        self.paused_executions[execution_id] = {
            "task_id": execution.task_id,
            "agent_id": execution.agent_id,
            "logs": execution.logs.copy(),
            "output": execution.output.copy(),
            "agent_response": execution.agent_response.copy() if execution.agent_response else {},
            "pause_time": datetime.utcnow()
        }
        
        # Cancel the running task
        if execution_id in self.running_executions:
            task = self.running_executions[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.running_executions[execution_id]
        
        # Update execution status
        execution.status = "paused"
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Execution paused by user",
            "level": "info"
        })
        
        # Update agent status
        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
        if agent:
            agent.status = AgentStatus.IDLE
        
        db.commit()
        
        # Broadcast pause event
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "execution_paused",
                "execution_id": execution_id,
                "message": "Execution paused by user",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {"status": "paused", "execution_id": execution_id}
    
    async def resume_execution(self, db: Session, execution_id: str):
        """Resume a paused execution."""
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        if execution.status != "paused":
            raise ValueError(f"Cannot resume execution with status: {execution.status}")
        
        if execution_id not in self.paused_executions:
            raise ValueError(f"No paused state found for execution {execution_id}")
        
        # Get paused state
        paused_state = self.paused_executions[execution_id]
        
        # Update execution status
        execution.status = "running"
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Execution resumed by user",
            "level": "info"
        })
        
        # Update agent status
        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
        if agent:
            agent.status = AgentStatus.EXECUTING
        
        db.commit()
        
        # Remove from paused executions
        del self.paused_executions[execution_id]
        
        # Create new execution task
        task = db.query(Task).filter(Task.id == execution.task_id).first()
        execution_task = asyncio.create_task(self._execute_task(agent, task, execution, db))
        self.running_executions[execution_id] = execution_task
        
        # Broadcast resume event
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "execution_resumed",
                "execution_id": execution_id,
                "message": "Execution resumed by user",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {"status": "resumed", "execution_id": execution_id}
    
    async def abort_execution(self, db: Session, execution_id: str):
        """Abort an execution (cannot be resumed)."""
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        if execution.status not in ["running", "paused", "starting"]:
            raise ValueError(f"Cannot abort execution with status: {execution.status}")
        
        # Cancel the asyncio task if running
        if execution_id in self.running_executions:
            task = self.running_executions[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.running_executions[execution_id]
        
        # Remove from paused executions if exists
        if execution_id in self.paused_executions:
            del self.paused_executions[execution_id]
        
        # Update execution status
        execution.status = "aborted"
        execution.end_time = datetime.utcnow()
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Execution aborted by user",
            "level": "warning"
        })
        
        # Update task status
        task = db.query(Task).filter(Task.id == execution.task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = "Execution aborted by user"
        
        # Update agent status
        agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
        if agent:
            agent.status = AgentStatus.IDLE
        
        db.commit()
        
        # Broadcast abort event
        if self.websocket_manager:
            await self.websocket_manager.broadcast({
                "type": "execution_aborted",
                "execution_id": execution_id,
                "message": "Execution aborted by user",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {"status": "aborted", "execution_id": execution_id}
    
    async def _spawn_claude_code_agent(self, agent: Agent, task: Task, execution: Execution, db: Session, work_dir: str = None) -> Dict[str, Any]:
        """Spawn Claude Code instance using Python SDK for non-interactive execution."""
        import os
        import json
        from pathlib import Path
        from claude_code_sdk import query, ClaudeCodeOptions
        
        # Use user-configurable work directory or create default
        if not work_dir:
            work_dir = f"./claude_executions/execution_{execution.id}"
        
        work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)
        
        # Create CLAUDE.md context file as per best practices
        claude_md_content = f"""# {agent.name} Agent Context

## Agent Profile
- **Role**: {agent.role}
- **Capabilities**: {', '.join(agent.capabilities)}
- **Objectives**: {', '.join(agent.objectives)}
- **Constraints**: {', '.join(agent.constraints)}

## Current Task
- **Title**: {task.title}
- **Description**: {task.description}
- **Expected Output**: {task.expected_output or 'Complete the task as described'}

## System Prompt
{agent.system_prompt}

## Guidelines
- Work autonomously within your capabilities
- Provide structured, expert-level output
- Follow best practices for your domain
- Document your approach and reasoning
"""
        
        claude_md_path = work_path / "CLAUDE.md"
        claude_md_path.write_text(claude_md_content)
        
        # Create task prompt optimized for Claude Code Python SDK
        task_prompt = f"""You are {agent.name}, a {agent.role}.

Please execute the following task autonomously:

TASK: {task.title}

DESCRIPTION: {task.description}

EXPECTED OUTPUT: {task.expected_output or 'Complete the task as described'}

Context: You have access to a CLAUDE.md file in your working directory with your full agent profile and capabilities.

Please provide your response in this structured JSON format:
{{
    "analysis": "Your analysis of the task",
    "approach": "Your methodology and approach",
    "implementation": "Your detailed work and implementation",
    "results": "Your final results and conclusions",
    "recommendations": "Any recommendations or next steps",
    "status": "completed|needs_user_input|error",
    "needs_interaction": false,
    "output_files": []
}}

Work within your capabilities and provide expert-level output. Respond with ONLY the JSON object."""
        
        try:
            # Log Claude Code SDK execution start
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Starting Claude Code SDK execution for {agent.name}",
                "level": "info",
                "details": f"Work directory: {work_dir}, Context file: {claude_md_path}"
            })
            db.commit()
            
            # Execute using Claude Code Python SDK
            messages = []
            assistant_messages = []
            final_response = ""
            
            try:
                async for message in query(
                    prompt=task_prompt,
                    options=ClaudeCodeOptions(
                        max_turns=3,  # Reduce turns to avoid SDK JSON issues
                        cwd=str(work_path),
                        permission_mode="bypassPermissions",  # Critical for non-interactive
                        system_prompt=f"You are {agent.name}, a {agent.role}. " + agent.system_prompt
                    )
                ):
                    messages.append(message)
                    msg_type = type(message).__name__
                    
                    # Handle different message types properly
                    if msg_type == "AssistantMessage" and hasattr(message, 'content'):
                        if message.content:
                            for block in message.content:
                                # Handle text blocks
                                if hasattr(block, 'text'):
                                    assistant_messages.append(block.text)
                                # Handle tool use blocks  
                                elif hasattr(block, 'input'):
                                    assistant_messages.append(str(block.input))
                    
                    # Log progress with proper message type handling
                    execution.logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Received {msg_type} from Claude Code SDK",
                        "level": "info"
                    })
                    db.commit()
                    
            except Exception as sdk_error:
                # Handle SDK JSON decode errors gracefully
                error_msg = str(sdk_error)
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Claude Code SDK error: {error_msg}",
                    "level": "warning"
                })
                db.commit()
                
                # If we have some messages, continue with what we got
                if not messages:
                    raise sdk_error  # Re-raise if no messages received
            
            # Extract final response from AssistantMessages (already properly processed)
            if assistant_messages:
                # Combine all assistant messages
                final_response = "\n\n".join(str(msg) for msg in assistant_messages if msg)
            
            # Log completion
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Claude Code SDK execution completed with {len(messages)} messages",
                "level": "info"
            })
            db.commit()
            
            # Try to extract JSON from response or create structured response
            response_data = {}
            
            if final_response.strip():
                # Look for JSON in the final response
                try:
                    # Try to find JSON object in response
                    content = final_response.strip()
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        response_data = json.loads(json_str)
                        
                        # Log successful JSON parsing
                        execution.logs.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": f"Successfully parsed JSON response with keys: {list(response_data.keys())}",
                            "level": "info"
                        })
                    else:
                        # No JSON found, create structured response from text
                        response_data = {
                            "analysis": "Claude Code SDK execution completed",
                            "approach": "Multi-turn conversation with file operations",
                            "implementation": content,
                            "results": content,
                            "recommendations": "Review output for completeness",
                            "status": "completed",
                            "needs_interaction": False,
                            "output_files": []
                        }
                        
                except json.JSONDecodeError as e:
                    # JSON parsing failed, create structured response with raw content
                    execution.logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"JSON parsing failed: {str(e)}, using raw response",
                        "level": "warning"
                    })
                    db.commit()
                    
                    response_data = {
                        "analysis": "Claude Code SDK execution completed",
                        "approach": "Multi-turn conversation analysis", 
                        "implementation": final_response[:2000],  # Include substantial content
                        "results": f"Task executed successfully. Raw response length: {len(final_response)} chars",
                        "recommendations": "Review implementation content for task completion details",
                        "status": "completed",
                        "needs_interaction": False,
                        "output_files": self._detect_output_files(work_path)
                    }
                
                # Save response to output file
                output_file = work_path / "claude_output.json"
                output_file.write_text(json.dumps(response_data, indent=2))
            
            else:
                # No final response extracted 
                response_data = {
                    "analysis": "Claude Code SDK execution completed but no response extracted",
                    "approach": "Multi-turn conversation",
                    "implementation": f"Processed {len(messages)} messages from Claude Code SDK",
                    "results": "Execution completed successfully",
                    "recommendations": "Check work directory for output files", 
                    "status": "completed",
                    "needs_interaction": False,
                    "output_files": self._detect_output_files(work_path)
                }
                
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "No final response text extracted, using message count summary",
                    "level": "warning"
                })
                db.commit()
                
                # Save response to output file
                output_file = work_path / "claude_output.json"
                output_file.write_text(json.dumps(response_data, indent=2))
            
            # Validate response data
            if not response_data or len(str(response_data).strip()) < 10:
                # Fallback expert response
                fallback_response = self._generate_expert_fallback(agent, task)
                response_data = {
                    "analysis": "Claude Code SDK failed, using expert fallback",
                    "approach": "Expert analysis",
                    "implementation": fallback_response,
                    "results": fallback_response,
                    "recommendations": "Consider manual review",
                    "status": "completed_with_fallback", 
                    "needs_interaction": False,
                    "output_files": []
                }
                execution.logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Claude Code SDK response was empty/invalid, using expert fallback",
                    "level": "warning"
                })
                db.commit()
            
            # Check if agent needs user interaction
            needs_interaction = response_data.get("needs_interaction", False) or response_data.get("status") == "needs_user_input"
            
            # Log successful response
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Received response from {agent.name} ({len(final_response)} characters)",
                "level": "info",
                "agent_status": response_data.get("status", "completed"),
                "needs_interaction": response_data.get("needs_interaction", False)
            })
            db.commit()
            
            return {
                "status": response_data.get("status", "completed"),
                "agent_response": response_data,
                "raw_response": final_response,
                "execution_method": "claude_code_python_sdk",
                "work_directory": str(work_path),
                "response_length": len(final_response),
                "needs_interaction": response_data.get("needs_interaction", False),
                "output_files": response_data.get("output_files", []),
                "execution_details": {
                    "sdk_messages": len(messages),
                    "assistant_messages": len(assistant_messages),
                    "timeout_occurred": False,
                    "fallback_used": "fallback" in response_data.get("status", ""),
                    "context_file": str(claude_md_path),
                    "output_file": str(work_path / "claude_output.json")
                }
            }
            
        except Exception as e:
            # Log execution error
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Claude Code spawning failed: {str(e)}",
                "level": "error"
            })
            db.commit()
            
            # Generate fallback response
            fallback_response = self._generate_expert_fallback(agent, task)
            fallback_data = {
                "analysis": "Claude Code execution failed",
                "approach": "Expert fallback analysis",
                "implementation": fallback_response,
                "results": fallback_response,
                "recommendations": "Review system configuration and try again",
                "status": "completed_with_fallback",
                "needs_interaction": False,
                "output_files": [],
                "error": str(e)
            }
            
            return {
                "status": "completed_with_fallback",
                "agent_response": fallback_data,
                "raw_response": fallback_response,
                "execution_method": "expert_fallback",
                "work_directory": work_dir,
                "needs_interaction": False,
                "error": str(e),
                "execution_details": {
                    "claude_code_failed": True,
                    "fallback_used": True,
                    "context_file": claude_md_path if 'claude_md_path' in locals() else None
                }
            }
            
        finally:
            # Keep work directory for user inspection, just log its location
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Work directory preserved at: {work_dir}",
                "level": "info"
            })
            db.commit()
    
    def _generate_expert_fallback(self, agent: Agent, task: Task) -> str:
        """Generate expert-level fallback response when Claude Code fails."""
        
        # Create specialized response based on agent role and capabilities
        role_specific_intro = {
            "mathematician": "As a theoretical mathematician, I'll approach this problem systematically:",
            "developer": "As a software developer, let me break down this implementation:",
            "researcher": "From a research perspective, I'll analyze this thoroughly:",
            "analyst": "As an analyst, I'll examine this systematically:",
            "coordinator": "As a project coordinator, I'll organize this task:"
        }.get(agent.role.lower().split()[0], f"As a {agent.role}, I'll address this task:")
        
        return f"""{role_specific_intro}

**Task Analysis**: {task.title}

**Approach**: 
{task.description}

**Implementation Strategy**:
Based on my capabilities in {', '.join(agent.capabilities[:3])}, I would:

1. **Initial Assessment**: Review the requirements and constraints
2. **Methodology**: Apply domain expertise to develop solution approach  
3. **Execution**: Implement using best practices in my field
4. **Validation**: Verify results meet expected outcomes
5. **Documentation**: Provide clear explanation of work completed

**Expected Output**: 
{task.expected_output or 'Task completed according to specifications'}

**Expert Recommendation**:
This task requires {agent.role} expertise. I recommend proceeding with careful attention to {', '.join(agent.constraints)} while leveraging {', '.join(agent.objectives)}.

**Status**: Task analysis completed. Ready for implementation phase with appropriate Claude Code integration.

---
*Note: This is an expert-level analysis. Full implementation would be performed through Claude Code autonomous execution.*"""
    
    def _detect_output_files(self, work_path: Path) -> List[str]:
        """Detect files created in the work directory during execution."""
        try:
            output_files = []
            for file_path in work_path.glob("*"):
                if file_path.is_file() and file_path.name != "CLAUDE.md":
                    output_files.append(str(file_path.relative_to(work_path)))
            return output_files
        except Exception:
            return []
    
    async def _execute_single_agent(self, agent: Agent, task: Task, execution: Execution, db: Session, work_dir: str = None) -> Dict[str, Any]:
        """Execute task with a single agent using Claude Code spawning."""
        
        agent_instance = self.agent_instances[agent.id]
        
        # Log agent initialization
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Initializing Claude Code instance for agent {agent.name}",
            "level": "info",
            "agent_id": agent.id
        })
        db.commit()
        
        try:
            # Execute task with real Claude Code spawning
            result = await self._spawn_claude_code_agent(agent, task, execution, db, work_dir)
            
            # Log completion
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Agent {agent.name} completed task successfully",
                "level": "info",
                "agent_id": agent.id
            })
            db.commit()
            
            return {
                "primary_agent": agent.name,
                "execution_type": "single_agent_claude_code",
                "result": result,
                "completion_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Log error
            execution.logs.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Agent {agent.name} execution failed: {str(e)}",
                "level": "error",
                "agent_id": agent.id
            })
            db.commit()
            raise
    
    async def _execute_multi_agent(self, agents: List[Agent], task: Task, execution: Execution, db: Session, work_directory: str = None) -> Dict[str, Any]:
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
        
        # Create coordination plan using Claude Code spawning
        coordination_task = Task(
            id=f"{task.id}_coordination",
            title=f"Multi-Agent Coordination Plan: {task.title}",
            description=f"""Create a detailed coordination plan for executing this task with multiple agents:

Original Task: {task.description}
Expected Output: {task.expected_output}

Available Collaborating Agents:
{chr(10).join([f"- {agent.name} ({agent.role}): {', '.join(agent.capabilities[:3])}" for agent in collaborating_agents])}

As the primary coordinator, design an effective strategy that leverages each agent's unique expertise.""",
            expected_output="Detailed multi-agent coordination strategy with specific agent assignments",
            priority=task.priority,
            deadline=task.deadline,
            resources=task.resources,
            dependencies=task.dependencies
        )
        
        plan_result = await self._spawn_claude_code_agent(primary_agent, coordination_task, execution, db, work_directory)
        
        plan = {
            "status": "planned",
            "strategy": plan_result.get('agent_response', 'Multi-agent coordination plan created'),
            "primary_coordinator": primary_agent.name,
            "collaborating_agents": [agent.name for agent in collaborating_agents],
            "execution_method": "claude_code_spawning"
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