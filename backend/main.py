"""
FastAPI main application for dynamic multi-agent system.
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio
from datetime import datetime

from database import get_db, engine
from models import Base, Agent, Task, Execution
from schemas import (
    AgentCreate, AgentUpdate, AgentResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    ExecutionResponse, SystemStatus, TaskExecutionRequest, TaskExecutionResponse,
    AgentStatusSummary
)
from services.execution_engine import ExecutionEngine
from services.advanced_orchestrator import (
    advanced_orchestrator, WorkflowPattern, WorkflowExecution, 
    WorkflowType, AgentCommunication
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Multi-Agent System API",
    description="Dynamic multi-agent system with user-configurable agents and asynchronous execution",
    version="2.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://172.21.149.249:3000", "http://172.21.149.249:3001"],  # React dev servers + WSL IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
        """Delete agent."""
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise ValueError("Agent not found")
        
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
        from models import TaskStatus
        
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
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent."""
    try:
        await agent_manager.delete_agent(db, agent_id)
        
        # Broadcast agent deletion
        await websocket_manager.broadcast_agent_event("deleted", {
            "id": agent_id
        })
        
        return {"message": "Agent deleted successfully"}
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
        await execution_engine.stop_execution(db, execution_id)
        
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
    executions = await execution_engine.get_all_executions(db)
    return executions


@app.get("/api/execution/{execution_id}", response_model=ExecutionResponse)
async def get_execution_details(execution_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific execution."""
    execution = await execution_engine.get_execution(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


# Dashboard and System Status Endpoints
@app.get("/api/dashboard/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """Get overall system status and metrics."""
    status = await execution_engine.get_system_status(db)
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
    
    wf_type = WorkflowType(workflow_type) if workflow_type else None
    
    pattern = await advanced_orchestrator.create_workflow_pattern(
        name=name,
        description=description,
        agents=agents,
        tasks=tasks,
        workflow_type=wf_type
    )
    
    return pattern.dict()

@app.get("/api/workflows/patterns")
async def list_workflow_patterns():
    """List all workflow patterns."""
    return [pattern.dict() for pattern in advanced_orchestrator.workflow_patterns.values()]

@app.post("/api/workflows/execute/{pattern_id}")
async def execute_workflow_pattern(
    pattern_id: str,
    context: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """Execute a workflow pattern with real-time monitoring."""
    try:
        execution = await advanced_orchestrator.execute_workflow_pattern(
            pattern_id, db, context
        )
        return execution.dict()
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
async def list_active_executions():
    """List all active workflow executions."""
    return [execution.dict() for execution in advanced_orchestrator.active_executions.values()]

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)