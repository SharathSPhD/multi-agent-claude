"""
FastAPI main application for dynamic multi-agent system.
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio
from datetime import datetime

from database import get_db, engine
from models import Base, Agent, Task, Execution, TaskStatus, AgentStatus
from schemas import (
    AgentCreate, AgentUpdate, AgentResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    ExecutionResponse, SystemStatus, TaskExecutionRequest, TaskExecutionResponse,
    AgentStatusSummary
)
from services.execution_engine import ExecutionEngine
from services.advanced_orchestrator import (
    advanced_orchestrator, WorkflowType, AgentCommunication
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Cleanup orphaned executions on startup
def cleanup_orphaned_executions():
    """Remove executions with NULL task_id or agent_id that cause validation errors"""
    with engine.connect() as connection:
        # Delete executions with NULL task_id or agent_id
        connection.execute(
            text("DELETE FROM executions WHERE task_id IS NULL OR agent_id IS NULL")
        )
        connection.commit()
        print("🧹 Cleaned up orphaned executions")

# Run cleanup
try:
    cleanup_orphaned_executions()
except Exception as e:
    print(f"⚠️  Cleanup warning: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="MCP Multi-Agent System API",
    description="Dynamic multi-agent system with user-configurable agents and asynchronous execution",
    version="2.0.0"
)

# Dynamic CORS configuration for WSL and local development
import subprocess
import socket

def get_wsl_ips():
    """Get all possible WSL IP addresses for CORS"""
    origins = [
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173"
    ]
    
    try:
        # Get WSL IP addresses
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.stdout:
            for ip in result.stdout.strip().split():
                if ip and not ip.startswith('127.'):
                    origins.extend([
                        f"http://{ip}:3000",
                        f"http://{ip}:3001",
                        f"http://{ip}:5173"
                    ])
    except:
        pass
    
    return origins

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_wsl_ips(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MCP Multi-Agent System API", "version": "2.0.0", "status": "running"}

# Service Classes
class AgentManager:
    """Manages agent lifecycle and operations."""
    
    async def create_agent(self, db: Session, agent_data: AgentCreate) -> Agent:
        """Create a new agent."""
        from models import AgentStatus
        
        db_agent = Agent(
            id=str(uuid.uuid4()),
            name=agent_data.name,
            role=agent_data.role,
            description=agent_data.description,
            system_prompt=agent_data.system_prompt,
            capabilities=agent_data.capabilities,
            tools=agent_data.tools,
            objectives=agent_data.objectives,
            constraints=agent_data.constraints,
            memory_settings=agent_data.memory_settings,
            execution_settings=agent_data.execution_settings,
            status=AgentStatus.IDLE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        return db_agent
    
    async def list_agents(self, db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
        """List all agents."""
        return db.query(Agent).offset(skip).limit(limit).all()
    
    async def get_agent(self, db: Session, agent_id: str) -> Agent:
        """Get agent by ID."""
        return db.query(Agent).filter(Agent.id == agent_id).first()
    
    async def update_agent(self, db: Session, agent_id: str, agent_update: AgentUpdate) -> Agent:
        """Update agent."""
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise ValueError("Agent not found")
        
        update_data = agent_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_agent, field, value)
        
        db_agent.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_agent)
        return db_agent
    
    async def delete_agent(self, db: Session, agent_id: str):
        """Delete agent with proper relationship cleanup."""
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise ValueError("Agent not found")
        
        # First, remove agent from all task assignments
        from models import TaskAgentAssignment
        db.query(TaskAgentAssignment).filter(TaskAgentAssignment.agent_id == agent_id).delete()
        
        # Delete all executions for this agent
        db.query(Execution).filter(Execution.agent_id == agent_id).delete()
        
        # Finally delete the agent
        db.delete(db_agent)
        db.commit()
    
    async def get_agent_status_summaries(self, db: Session) -> List[AgentStatusSummary]:
        """Get summary of all agent statuses."""
        agents = db.query(Agent).all()
        summaries = []
        
        for agent in agents:
            # Get current task if any
            current_execution = db.query(Execution).filter(
                Execution.agent_id == agent.id,
                Execution.status.in_(["running", "starting"])
            ).first()
            
            # Count completed tasks today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            tasks_today = db.query(Execution).filter(
                Execution.agent_id == agent.id,
                Execution.status == "completed",
                Execution.end_time >= today_start
            ).count()
            
            summaries.append(AgentStatusSummary(
                agent_id=agent.id,
                name=agent.name,
                status=agent.status,
                current_task_id=current_execution.task_id if current_execution else None,
                current_task_title=None,  # Would need to join with Task table
                tasks_completed_today=tasks_today,
                average_task_duration=None,  # Would need calculation
                last_active=agent.last_active
            ))
        
        return summaries


class TaskScheduler:
    """Manages task scheduling and lifecycle."""
    
    async def create_task(self, db: Session, task_data: TaskCreate) -> Task:
        """Create a new task."""
        
        db_task = Task(
            id=str(uuid.uuid4()),
            title=task_data.title,
            description=task_data.description,
            expected_output=task_data.expected_output,
            resources=task_data.resources,
            dependencies=task_data.dependencies,
            priority=task_data.priority,
            deadline=task_data.deadline,
            estimated_duration=task_data.estimated_duration,
            status=TaskStatus.PENDING,
            results={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Assign agents to task
        if task_data.assigned_agent_ids:
            agents = db.query(Agent).filter(Agent.id.in_(task_data.assigned_agent_ids)).all()
            db_task.assigned_agents = agents
            db.commit()
        
        return db_task
    
    async def list_tasks(self, db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
        """List all tasks."""
        return db.query(Task).offset(skip).limit(limit).all()
    
    async def get_task(self, db: Session, task_id: str) -> Task:
        """Get task by ID."""
        return db.query(Task).filter(Task.id == task_id).first()
    
    async def update_task(self, db: Session, task_id: str, task_update: TaskUpdate) -> Task:
        """Update task."""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise ValueError("Task not found")
        
        update_data = task_update.dict(exclude_unset=True)
        
        # Handle assigned_agent_ids separately for relationship management
        assigned_agent_ids = update_data.pop('assigned_agent_ids', None)
        
        # Update regular fields
        for field, value in update_data.items():
            setattr(db_task, field, value)
        
        # Update agent assignments if provided
        if assigned_agent_ids is not None:
            # Clear existing assignments
            db_task.assigned_agents.clear()
            
            # Add new assignments
            if assigned_agent_ids:
                agents = db.query(Agent).filter(Agent.id.in_(assigned_agent_ids)).all()
                db_task.assigned_agents.extend(agents)
        
        db_task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_task)
        return db_task
    
    async def delete_task(self, db: Session, task_id: str):
        """Delete task."""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise ValueError("Task not found")
        
        db.delete(db_task)
        db.commit()


class WebSocketManager:
    """Manages WebSocket connections and real-time updates."""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.utcnow(),
            "subscriptions": ["all"]  # Default subscription to all events
        }
        
        # Send welcome message
        await self.send_to_connection(websocket, {
            "type": "connection_established",
            "message": "Connected to MCP Multi-Agent System",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket in self.connections:
            self.connections.remove(websocket)
        if websocket in self.connection_info:
            del self.connection_info[websocket]
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            # Connection is broken, remove it
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], subscription_filter: str = None):
        """Broadcast message to all connected clients."""
        if not self.connections:
            return
        
        # Add metadata
        message["broadcast_id"] = str(uuid.uuid4())
        message["server_timestamp"] = datetime.utcnow().isoformat()
        
        # Send to all connections (or filtered by subscription)
        disconnected = []
        for websocket in self.connections[:]:
            try:
                # Check subscription filter if provided
                if subscription_filter:
                    subscriptions = self.connection_info.get(websocket, {}).get("subscriptions", [])
                    if subscription_filter not in subscriptions and "all" not in subscriptions:
                        continue
                
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_system_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast system-level events."""
        await self.broadcast({
            "type": "system_event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_agent_event(self, event_type: str, agent_data: Dict[str, Any]):
        """Broadcast agent-related events."""
        await self.broadcast({
            "type": "agent_event",
            "event_type": event_type,
            "agent": agent_data,
            "timestamp": datetime.utcnow().isoformat()
        }, subscription_filter="agents")
    
    async def broadcast_task_event(self, event_type: str, task_data: Dict[str, Any]):
        """Broadcast task-related events."""
        await self.broadcast({
            "type": "task_event", 
            "event_type": event_type,
            "task": task_data,
            "timestamp": datetime.utcnow().isoformat()
        }, subscription_filter="tasks")
    
    async def broadcast_execution_event(self, event_type: str, execution_data: Dict[str, Any]):
        """Broadcast execution-related events."""
        await self.broadcast({
            "type": "execution_event",
            "event_type": event_type,
            "execution": execution_data,
            "timestamp": datetime.utcnow().isoformat()
        }, subscription_filter="executions")
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about all connections."""
        return {
            "total_connections": len(self.connections),
            "connections": [
                {
                    "connected_at": info["connected_at"].isoformat(),
                    "subscriptions": info["subscriptions"]
                }
                for info in self.connection_info.values()
            ]
        }


# Initialize services
agent_manager = AgentManager()
task_scheduler = TaskScheduler()
execution_engine = ExecutionEngine()
websocket_manager = WebSocketManager()

# Configure execution engine with WebSocket manager
execution_engine.set_websocket_manager(websocket_manager)


# WebSocket endpoint for real-time updates
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            await websocket_manager.broadcast({
                "type": "echo",
                "message": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


# Agent Endpoints
@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent with custom configuration."""
    try:
        from models import AgentStatus
        import uuid
        
        # Create new agent
        db_agent = Agent(
            id=str(uuid.uuid4()),
            name=agent.name,
            role=agent.role,
            description=agent.description,
            system_prompt=agent.system_prompt,
            capabilities=agent.capabilities,
            tools=agent.tools,
            objectives=agent.objectives,
            constraints=agent.constraints,
            memory_settings=agent.memory_settings,
            execution_settings=agent.execution_settings,
            status=AgentStatus.IDLE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        
        # Broadcast agent creation
        await websocket_manager.broadcast_agent_event("created", {
            "id": db_agent.id,
            "name": db_agent.name,
            "role": db_agent.role,
            "status": db_agent.status.value
        })
        
        return db_agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all agents."""
    agents = await agent_manager.list_agents(db, skip=skip, limit=limit)
    return agents


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get specific agent by ID."""
    agent = await agent_manager.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.put("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    """Update agent configuration."""
    try:
        db_agent = await agent_manager.update_agent(db, agent_id, agent_update)
        
        # Broadcast agent update
        await websocket_manager.broadcast_agent_event("updated", {
            "id": db_agent.id,
            "name": db_agent.name,
            "role": db_agent.role,
            "status": db_agent.status.value
        })
        
        return db_agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, force: bool = False, db: Session = Depends(get_db)):
    """Delete an agent with proper task handling."""
    try:
        # Check if agent exists
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check for running executions
        running_executions = db.query(Execution).filter(
            Execution.agent_id == agent_id,
            Execution.status.in_(["running", "starting", "paused"])
        ).all()
        
        if running_executions and not force:
            return {
                "message": "Cannot delete agent with running executions",
                "running_executions": len(running_executions),
                "suggestion": "Cancel running executions first or use force=true"
            }
        
        # Cancel all running executions if force=True
        if running_executions and force:
            for execution in running_executions:
                try:
                    await execution_engine.abort_execution(db, execution.id)
                except Exception as e:
                    print(f"Failed to abort execution {execution.id}: {e}")
        
        # Get associated tasks
        associated_tasks = db.query(Task).join(Task.assigned_agents).filter(Agent.id == agent_id).all()
        
        # Handle task reassignment or cancellation
        task_updates = []
        for task in associated_tasks:
            # Remove agent from task's assigned agents
            task.assigned_agents = [a for a in task.assigned_agents if a.id != agent_id]
            
            # If no agents left, mark task as pending reassignment
            if not task.assigned_agents:
                task.status = TaskStatus.PENDING
                task.error_message = f"Agent {agent.name} was deleted"
            
            task_updates.append({
                "task_id": task.id,
                "task_title": task.title,
                "remaining_agents": len(task.assigned_agents)
            })
        
        # Delete the agent
        await agent_manager.delete_agent(db, agent_id)
        
        # Broadcast agent deletion with task info
        await websocket_manager.broadcast_agent_event("deleted", {
            "id": agent_id,
            "name": agent.name,
            "affected_tasks": len(associated_tasks),
            "task_updates": task_updates
        })
        
        return {
            "message": "Agent deleted successfully",
            "affected_tasks": len(associated_tasks),
            "task_updates": task_updates,
            "cancelled_executions": len(running_executions) if force else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Task Endpoints
@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    try:
        db_task = await task_scheduler.create_task(db, task)
        
        # Broadcast task creation
        await websocket_manager.broadcast_task_event("created", {
            "id": db_task.id,
            "title": db_task.title,
            "status": db_task.status.value,
            "priority": db_task.priority.value
        })
        
        return db_task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tasks", response_model=List[TaskResponse])
async def list_tasks(skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)):
    """List all tasks with optional status filter."""
    tasks = await task_scheduler.list_tasks(db, skip=skip, limit=limit)
    return tasks


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get specific task by ID."""
    task = await task_scheduler.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update task configuration."""
    try:
        db_task = await task_scheduler.update_task(db, task_id, task_update)
        
        # Broadcast task update
        await websocket_manager.broadcast({
            "type": "task_updated",
            "task": TaskResponse.from_orm(db_task).dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return db_task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task."""
    try:
        await task_scheduler.delete_task(db, task_id)
        
        # Broadcast task deletion
        await websocket_manager.broadcast({
            "type": "task_deleted",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tasks/execute", response_model=TaskExecutionResponse)
async def execute_task_endpoint(request: TaskExecutionRequest, db: Session = Depends(get_db)):
    """Execute a task with specified agents."""
    try:
        execution = await execution_engine.start_task_execution(db, request)
        
        # Broadcast execution start
        await websocket_manager.broadcast_execution_event("started", {
            "execution_id": execution.execution_id,
            "task_id": execution.task_id,
            "status": execution.status
        })
        
        return execution
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Execution Endpoints
@app.post("/api/execution/start", response_model=TaskExecutionResponse)
async def start_task_execution(request: TaskExecutionRequest, db: Session = Depends(get_db)):
    """Start executing a task with specified agents."""
    try:
        execution = await execution_engine.start_task_execution(db, request)
        
        # Broadcast execution start
        await websocket_manager.broadcast({
            "type": "execution_started",
            "execution": execution.dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return execution
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/execution/stop/{execution_id}")
async def stop_execution(execution_id: str, db: Session = Depends(get_db)):
    """Stop a running execution."""
    try:
        await execution_engine.abort_execution(execution_id, db)
        
        # Broadcast execution stop
        await websocket_manager.broadcast({
            "type": "execution_stopped",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"message": "Execution stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/execution/status", response_model=List[ExecutionResponse])
async def get_execution_status(db: Session = Depends(get_db)):
    """Get status of all current executions."""
    executions = execution_engine.get_all_executions(db)
    return executions


@app.get("/api/execution/{execution_id}", response_model=ExecutionResponse)
async def get_execution_details(execution_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific execution."""
    execution = execution_engine.get_execution_status(execution_id, db)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@app.post("/api/execution/{execution_id}/cancel")
async def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    """Cancel a running execution."""
    try:
        result = await execution_engine.abort_execution(execution_id, db)
        return {"message": f"Execution {execution_id} cancelled", "success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/execution/{execution_id}/pause")
async def pause_execution(execution_id: str, db: Session = Depends(get_db)):
    """Pause a running execution."""
    try:
        result = await execution_engine.pause_execution(execution_id, db)
        return {"message": f"Execution {execution_id} paused", "success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/execution/{execution_id}/resume")
async def resume_execution(execution_id: str, db: Session = Depends(get_db)):
    """Resume a paused execution."""
    try:
        result = await execution_engine.resume_execution(execution_id, db)
        return {"message": f"Execution {execution_id} resumed", "success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/execution/{execution_id}/abort")
async def abort_execution(execution_id: str, db: Session = Depends(get_db)):
    """Abort an execution (cannot be resumed)."""
    try:
        result = await execution_engine.abort_execution(execution_id, db)
        return {"message": f"Execution {execution_id} aborted", "success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Dashboard and System Status Endpoints
@app.get("/api/dashboard/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """Get overall system status and metrics."""
    status = execution_engine.get_system_status(db)
    return status


@app.get("/api/dashboard/agents", response_model=List[AgentStatusSummary])
async def get_agent_status_summary(db: Session = Depends(get_db)):
    """Get summary of all agent statuses."""
    summaries = await agent_manager.get_agent_status_summaries(db)
    return summaries


# Advanced Orchestration Endpoints
@app.post("/api/workflows/analyze")
async def analyze_workflow_requirements(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Analyze and recommend the best workflow pattern for given agents and tasks."""
    try:
        agents_ids = request.get("agents_ids", [])
        task_ids = request.get("task_ids", [])
        user_objective = request.get("user_objective", "")
        
        agents = db.query(Agent).filter(Agent.id.in_(agents_ids)).all()
        tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
        
        workflow_analysis = await advanced_orchestrator.analyze_workflow_requirements(
            agents, tasks, user_objective
        )
        
        # Extract recommended workflow from the analysis result
        if hasattr(workflow_analysis, 'recommended_workflow'):
            recommended_workflow = workflow_analysis.recommended_workflow.value if hasattr(workflow_analysis.recommended_workflow, 'value') else str(workflow_analysis.recommended_workflow)
        else:
            recommended_workflow = "parallel"  # default fallback
        
        return {
            "recommended_workflow": recommended_workflow,
            "analysis": {
                "agent_count": len(agents),
                "task_count": len(tasks),
                "has_dependencies": any("depends" in (task.description or "").lower() for task in tasks),
                "user_objective": user_objective
            }
        }
    except Exception as e:
        print(f"ERROR in analyze_workflow_requirements: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/workflows/patterns")
async def create_workflow_pattern(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create an advanced workflow pattern."""
    from models import WorkflowPattern
    
    name = request.get("name", "")
    description = request.get("description", "")
    agent_ids = request.get("agent_ids", [])
    task_ids = request.get("task_ids", [])
    user_objective = request.get("user_objective", "")
    workflow_type = request.get("workflow_type")
    
    agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    
    if not agents or not tasks:
        raise HTTPException(status_code=404, detail="Agents or tasks not found")
    
    # Create in-memory pattern for orchestrator
    wf_type = None
    if workflow_type:
        try:
            # Try direct mapping first
            wf_type = WorkflowType(workflow_type.lower())
        except ValueError:
            # If that fails, try to find by uppercase name
            for wf in WorkflowType:
                if wf.name == workflow_type.upper():
                    wf_type = wf
                    break
            if not wf_type:
                raise HTTPException(status_code=400, detail=f"Invalid workflow type: {workflow_type}")
    pattern = await advanced_orchestrator.create_workflow_pattern(
        name=name,
        description=description,
        agents=agents,
        tasks=tasks,
        workflow_type=wf_type
    )
    
    # Save to database
    from models import WorkflowPattern as DBWorkflowPattern
    db_pattern = DBWorkflowPattern(
        id=pattern.id,
        name=name,
        description=description,
        workflow_type=workflow_type or "parallel",
        agent_ids=agent_ids,
        task_ids=task_ids,
        user_objective=user_objective,
        config={"pattern_data": "created_from_api"}
    )
    db.add(db_pattern)
    db.commit()
    db.refresh(db_pattern)
    
    return {
        "id": db_pattern.id,
        "name": db_pattern.name,
        "description": db_pattern.description,
        "workflow_type": db_pattern.workflow_type,
        "agent_ids": db_pattern.agent_ids,
        "task_ids": db_pattern.task_ids,
        "user_objective": db_pattern.user_objective,
        "status": db_pattern.status,
        "created_at": db_pattern.created_at.isoformat()
    }

@app.get("/api/workflows/patterns")
async def list_workflow_patterns(db: Session = Depends(get_db)):
    """List all workflow patterns."""
    from models import WorkflowPattern
    
    patterns = db.query(WorkflowPattern).filter(WorkflowPattern.status == "active").all()
    return [{
        "id": pattern.id,
        "name": pattern.name,
        "description": pattern.description,
        "workflow_type": pattern.workflow_type,
        "agent_ids": pattern.agent_ids,
        "task_ids": pattern.task_ids,
        "user_objective": pattern.user_objective,
        "status": pattern.status,
        "created_at": pattern.created_at.isoformat()
    } for pattern in patterns]

@app.post("/api/workflows/execute/{pattern_id}")
async def execute_workflow_pattern(
    pattern_id: str,
    context: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """Execute a workflow pattern with real-time monitoring."""
    from models import WorkflowPattern, WorkflowExecution
    
    try:
        # Get pattern from database
        db_pattern = db.query(WorkflowPattern).filter(WorkflowPattern.id == pattern_id).first()
        if not db_pattern:
            raise HTTPException(status_code=404, detail="Workflow pattern not found")
        
        # Create workflow execution record
        workflow_execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            pattern_id=pattern_id,
            status="running"
        )
        db.add(workflow_execution)
        db.commit()
        
        # Get agents and tasks for the pattern
        from services.advanced_orchestrator import WorkflowPattern as OrchestratorPattern
        
        # Debug output to file
        with open('/tmp/workflow_debug.log', 'a') as f:
            f.write(f"DB Pattern agent_ids: {db_pattern.agent_ids}, type: {type(db_pattern.agent_ids)}\n")
            f.write(f"DB Pattern task_ids: {db_pattern.task_ids}, type: {type(db_pattern.task_ids)}\n")
        
        agents = db.query(Agent).filter(Agent.id.in_(db_pattern.agent_ids)).all()
        tasks = db.query(Task).filter(Task.id.in_(db_pattern.task_ids)).all()
        
        with open('/tmp/workflow_debug.log', 'a') as f:
            f.write(f"Found {len(agents)} agents: {[a.name for a in agents]}\n")
            f.write(f"Found {len(tasks)} tasks: {[t.title for t in tasks]}\n")
        
        # Convert DB pattern to orchestrator pattern
        orchestrator_pattern = OrchestratorPattern(
            id=db_pattern.id,
            name=db_pattern.name,
            description=db_pattern.description,
            workflow_type=db_pattern.workflow_type,
            agents=[agent.id for agent in agents],
            tasks=[task.id for task in tasks],
            config=db_pattern.config or {},
            created_at=db_pattern.created_at,
            updated_at=datetime.utcnow()
        )
        
        # Execute with orchestrator
        try:
            with open('/tmp/workflow_debug.log', 'a') as f:
                f.write(f"Executing workflow with {len(agents)} agents and {len(tasks)} tasks\n")
                for agent in agents:
                    f.write(f"Agent: {agent.name}, description: {getattr(agent, 'description', 'None')}\n")
                for task in tasks:
                    f.write(f"Task: {task.title}, description: {getattr(task, 'description', 'None')}\n")
                f.write(f"About to call advanced_orchestrator.execute_workflow\n")
            
            execution = await advanced_orchestrator.execute_workflow(
                orchestrator_pattern, agents, tasks, db
            )
            
            with open('/tmp/workflow_debug.log', 'a') as f:
                f.write(f"Orchestrator execution completed successfully\n")
                
        except Exception as ex:
            with open('/tmp/workflow_debug.log', 'a') as f:
                f.write(f"Orchestrator execution error: {str(ex)}\n")
                import traceback
                f.write(f"Traceback: {traceback.format_exc()}\n")
            raise
        
        # Update workflow execution status
        workflow_execution.status = execution.status if hasattr(execution, 'status') else "completed"
        workflow_execution.result = execution.dict() if hasattr(execution, 'dict') else {}
        db.commit()
        
        return {
            "id": workflow_execution.id,
            "pattern_id": pattern_id,
            "status": workflow_execution.status,
            "result": workflow_execution.result or {},
            "started_at": workflow_execution.start_time.isoformat() if workflow_execution.start_time else None
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@app.get("/api/workflows/executions/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get real-time execution status."""
    execution = advanced_orchestrator.get_execution_status(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution.dict()

@app.get("/api/workflows/executions")
async def list_active_executions(db: Session = Depends(get_db)):
    """List all active workflow executions."""
    from models import WorkflowExecution
    
    executions = db.query(WorkflowExecution).filter(WorkflowExecution.status.in_(["running", "paused"])).all()
    return [{
        "id": execution.id,
        "pattern_id": execution.pattern_id,
        "status": execution.status,
        "progress": execution.progress_percentage,
        "results": execution.results,
        "started_at": execution.start_time.isoformat(),
        "completed_at": execution.end_time.isoformat() if execution.end_time else None
    } for execution in executions]

@app.post("/api/workflows/executions/{execution_id}/abort")
async def abort_workflow_execution(execution_id: str, db: Session = Depends(get_db)):
    """Abort a running workflow execution."""
    from models import WorkflowExecution
    
    try:
        # Find the execution
        execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Workflow execution not found")
        
        if execution.status not in ["running", "paused"]:
            raise HTTPException(status_code=400, detail=f"Cannot abort execution with status: {execution.status}")
        
        # Update status to cancelled
        execution.status = "cancelled"
        execution.end_time = datetime.utcnow()
        
        # Try to stop the orchestrator execution if it's running
        try:
            advanced_orchestrator.stop_execution(execution_id)
        except Exception as e:
            print(f"Warning: Could not stop orchestrator execution {execution_id}: {e}")
        
        db.commit()
        
        return {"message": "Workflow execution aborted successfully", "execution_id": execution_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to abort workflow execution: {str(e)}")

@app.get("/api/workflows/communications/{execution_id}")
async def get_agent_communications(execution_id: str):
    """Get agent communications for specific execution."""
    communications = advanced_orchestrator.get_agent_communications(execution_id)
    return [comm.dict() for comm in communications]

@app.get("/api/workflows/types")
async def get_workflow_types():
    """Get available workflow types and their descriptions."""
    return {
        "SEQUENTIAL": "Execute tasks one after another in order",
        "PARALLEL": "Execute independent tasks simultaneously", 
        "ORCHESTRATOR": "Dynamic planning and coordination of complex workflows",
        "ROUTER": "Route tasks to the most suitable agents based on criteria",
        "EVALUATOR_OPTIMIZER": "Iterative improvement through evaluation and optimization",
        "SWARM": "Collaborative agent behavior with dynamic task assignment",
        "ADAPTIVE": "Automatically adapt workflow pattern based on execution context"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


# Project Management Endpoints
@app.post("/api/project/load-from-directory")
async def load_from_directory(request: dict, db: Session = Depends(get_db)):
    """Load agents and tasks from project directory"""
    import os
    import json
    
    directory = request.get("directory", "./")
    force_reload = request.get("force_reload", False)
    
    try:
        results = {
            "agents_loaded": 0,
            "tasks_loaded": 0,
            "errors": [],
            "files_processed": []
        }
        
        if not os.path.exists(directory):
            raise HTTPException(status_code=400, detail=f"Directory not found: {directory}")
        
        # Look for agent and task files
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if not os.path.isfile(file_path):
                continue
                
            try:
                # Try to load structured files (JSON)
                if filename.endswith(('.json', '.agents.json', '.tasks.json')):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if 'agents' in filename.lower() or 'agents' in data:
                        agents_data = data.get('agents', data if isinstance(data, list) else [data])
                        for agent_data in agents_data:
                            try:
                                # Check if agent already exists
                                existing = db.query(Agent).filter(Agent.name == agent_data.get('name')).first()
                                if existing and not force_reload:
                                    continue
                                    
                                if existing and force_reload:
                                    db.delete(existing)
                                    db.commit()  # Commit deletion before creating new
                                
                                db_agent = Agent(
                                    id=str(uuid.uuid4()),
                                    name=agent_data.get('name', 'Unknown Agent'),
                                    role=agent_data.get('role', 'General Agent'),
                                    description=agent_data.get('description'),
                                    system_prompt=agent_data.get('system_prompt', f"You are {agent_data.get('name', 'an agent')}."),
                                    capabilities=agent_data.get('capabilities', []),
                                    tools=agent_data.get('tools', []),
                                    objectives=agent_data.get('objectives', []),
                                    constraints=agent_data.get('constraints', []),
                                    status=AgentStatus.IDLE
                                )
                                db.add(db_agent)
                                results["agents_loaded"] += 1
                            except Exception as e:
                                results["errors"].append(f"Error loading agent from {filename}: {str(e)}")
                    
                    if 'tasks' in filename.lower() or 'tasks' in data:
                        tasks_data = data.get('tasks', data if isinstance(data, list) else [data])
                        for task_data in tasks_data:
                            try:
                                # Check if task already exists
                                existing = db.query(Task).filter(Task.title == task_data.get('title')).first()
                                if existing and not force_reload:
                                    continue
                                    
                                if existing and force_reload:
                                    db.delete(existing)
                                    db.commit()  # Commit deletion before creating new
                                
                                db_task = Task(
                                    id=str(uuid.uuid4()),
                                    title=task_data.get('title', 'Untitled Task'),
                                    description=task_data.get('description', ''),
                                    expected_output=task_data.get('expected_output'),
                                    resources=task_data.get('resources', []),
                                    dependencies=task_data.get('dependencies', []),
                                    priority=task_data.get('priority', 'medium'),
                                    status=TaskStatus.PENDING
                                )
                                db.add(db_task)
                                
                                # Handle agent assignments if specified
                                if 'assigned_agents' in task_data:
                                    from models import TaskAgentAssignment
                                    for agent_name in task_data['assigned_agents']:
                                        agent = db.query(Agent).filter(Agent.name == agent_name).first()
                                        if agent:
                                            assignment = TaskAgentAssignment(
                                                task_id=db_task.id,
                                                agent_id=agent.id
                                            )
                                            db.add(assignment)
                                
                                results["tasks_loaded"] += 1
                            except Exception as e:
                                results["errors"].append(f"Error loading task from {filename}: {str(e)}")
                
                results["files_processed"].append(filename)
                
            except Exception as e:
                results["errors"].append(f"Error processing {filename}: {str(e)}")
        
        db.commit()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/project/directory-info")
async def get_directory_info(directory: str = "./"):
    """Get information about files in a directory"""
    import os
    
    try:
        if not os.path.exists(directory):
            return {"exists": False, "error": "Directory not found"}
        
        files = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_info = {
                    "name": filename,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path),
                    "type": "structured" if filename.endswith(('.json',)) else "unstructured" if filename.endswith(('.txt', '.md', '.mdx')) else "other"
                }
                files.append(file_info)
        
        return {
            "exists": True,
            "directory": directory,
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}


# System Metrics Endpoint
@app.get("/api/system/metrics")
async def get_system_metrics(db: Session = Depends(get_db)):
    """Get comprehensive system metrics including memory, CPU, connections, and database performance."""
    import sys
    import os
    import platform
    import shutil
    import time
    from datetime import datetime
    
    # Check if psutil is available
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
    
    def get_memory_usage():
        """Get memory usage statistics."""
        if PSUTIL_AVAILABLE:
            memory = psutil.virtual_memory()
            return {
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "available_mb": round(memory.available / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "percentage": memory.percent,
                "free_mb": round(memory.free / (1024 * 1024), 2)
            }
        else:
            # Fallback using /proc/meminfo on Linux systems
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                lines = meminfo.split('\n')
                mem_dict = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        mem_dict[key.strip()] = value.strip()
                
                total_kb = int(mem_dict.get('MemTotal', '0').split()[0])
                free_kb = int(mem_dict.get('MemFree', '0').split()[0])
                available_kb = int(mem_dict.get('MemAvailable', str(free_kb)).split()[0])
                used_kb = total_kb - free_kb
                
                return {
                    "total_mb": round(total_kb / 1024, 2),
                    "available_mb": round(available_kb / 1024, 2),
                    "used_mb": round(used_kb / 1024, 2),
                    "percentage": round((used_kb / total_kb) * 100, 2) if total_kb > 0 else 0,
                    "free_mb": round(free_kb / 1024, 2)
                }
            except Exception as e:
                return {"error": f"Cannot read memory info: {str(e)}"}
    
    def get_cpu_usage():
        """Get CPU usage statistics."""
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                "percentage": cpu_percent,
                "cores": {
                    "physical": psutil.cpu_count(logical=False),
                    "logical": cpu_count
                },
                "frequency": {
                    "current_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
                    "min_mhz": round(cpu_freq.min, 2) if cpu_freq else None,
                    "max_mhz": round(cpu_freq.max, 2) if cpu_freq else None
                }
            }
        else:
            # Fallback using load average
            try:
                cpu_count = os.cpu_count() or 1
                try:
                    with open('/proc/loadavg', 'r') as f:
                        load_avg = float(f.read().split()[0])
                    cpu_percentage = min(100, (load_avg / cpu_count) * 100)
                except:
                    cpu_percentage = 0
                
                return {
                    "percentage": round(cpu_percentage, 2),
                    "cores": {"physical": cpu_count, "logical": cpu_count},
                    "frequency": {"current_mhz": None, "min_mhz": None, "max_mhz": None}
                }
            except Exception as e:
                return {"error": f"Cannot read CPU info: {str(e)}"}
    
    def get_active_connections():
        """Get active network connections."""
        if PSUTIL_AVAILABLE:
            try:
                connections = psutil.net_connections()
                established = len([c for c in connections if c.status == psutil.CONN_ESTABLISHED])
                listening = len([c for c in connections if c.status == psutil.CONN_LISTEN])
                
                return {
                    "total": len(connections),
                    "established": established,
                    "listening": listening
                }
            except Exception:
                return {"total": 0, "established": 0, "listening": 0, "error": "Permission denied"}
        else:
            # Simplified fallback
            return {"total": 0, "established": 0, "listening": 0, "note": "Limited connection info without psutil"}
    
    def get_disk_usage():
        """Get disk usage statistics."""
        try:
            if PSUTIL_AVAILABLE:
                disk = psutil.disk_usage('/')
                return {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percentage": round((disk.used / disk.total) * 100, 2)
                }
            else:
                disk = shutil.disk_usage('/')
                return {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round((disk.total - disk.free) / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percentage": round(((disk.total - disk.free) / disk.total) * 100, 2)
                }
        except Exception as e:
            return {"error": f"Cannot read disk info: {str(e)}"}
    
    def get_database_performance():
        """Get database performance metrics."""
        try:
            start_time = time.time()
            
            # Basic connection test
            db.execute(text("SELECT 1"))
            connection_time = round((time.time() - start_time) * 1000, 2)
            
            # Count records in main tables
            agent_count = db.execute(text("SELECT COUNT(*) FROM agents")).scalar()
            task_count = db.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
            execution_count = db.execute(text("SELECT COUNT(*) FROM executions")).scalar()
            
            # Active executions
            active_executions = db.execute(
                text("SELECT COUNT(*) FROM executions WHERE status IN ('running', 'starting', 'paused')")
            ).scalar()
            
            return {
                "connection_time_ms": connection_time,
                "table_counts": {
                    "agents": agent_count,
                    "tasks": task_count,
                    "executions": execution_count
                },
                "active_executions": active_executions,
                "status": "healthy"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_system_info():
        """Get general system information."""
        try:
            return {
                "hostname": platform.node(),
                "platform": platform.system(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Cannot read system info: {str(e)}"}
    
    try:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "memory": get_memory_usage(),
            "cpu": get_cpu_usage(),
            "disk": get_disk_usage(),
            "network": {
                "connections": get_active_connections()
            },
            "database": get_database_performance(),
            "system": get_system_info(),
            "websocket_connections": websocket_manager.get_connection_count(),
            "psutil_available": PSUTIL_AVAILABLE,
            "status": "healthy"
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)