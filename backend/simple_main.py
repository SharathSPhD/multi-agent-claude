"""
Simplified FastAPI main application for dynamic multi-agent system.
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import uuid

from database import get_db, engine
from models import Base, Agent, Task, Execution, AgentStatus, TaskStatus
from schemas import (
    AgentCreate, AgentUpdate, AgentResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    ExecutionResponse, SystemStatus, TaskExecutionRequest, TaskExecutionResponse,
    AgentStatusSummary
)
from services.execution_engine import ExecutionEngine

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
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize services
execution_engine = ExecutionEngine()

# Simple WebSocket manager placeholder
class SimpleWebSocketManager:
    def __init__(self):
        self.connections = []
    
    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)
    
    def disconnect(self, websocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
    
    async def broadcast(self, message):
        for connection in self.connections[:]:
            try:
                await connection.send_json(message)
            except:
                self.connections.remove(connection)

websocket_manager = SimpleWebSocketManager()


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


# Health check endpoint
@app.get("/api/status")
async def get_status():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Agent Endpoints
@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent with custom configuration."""
    try:
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
        await websocket_manager.broadcast({
            "type": "agent_created",
            "agent": {
                "id": db_agent.id,
                "name": db_agent.name,
                "role": db_agent.role,
                "status": db_agent.status.value
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return db_agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all agents."""
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return agents


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get specific agent by ID."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.put("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    """Update agent configuration."""
    try:
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update fields
        update_data = agent_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_agent, field, value)
        
        db_agent.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_agent)
        
        # Broadcast agent update
        await websocket_manager.broadcast({
            "type": "agent_updated",
            "agent": {
                "id": db_agent.id,
                "name": db_agent.name,
                "role": db_agent.role,
                "status": db_agent.status.value
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return db_agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent."""
    try:
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        db.delete(db_agent)
        db.commit()
        
        # Broadcast agent deletion
        await websocket_manager.broadcast({
            "type": "agent_deleted",
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Task Endpoints
@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    try:
        # Create new task
        db_task = Task(
            id=str(uuid.uuid4()),
            title=task.title,
            description=task.description,
            expected_output=task.expected_output,
            resources=task.resources,
            dependencies=task.dependencies,
            priority=task.priority,
            deadline=task.deadline,
            estimated_duration=task.estimated_duration,
            status=TaskStatus.PENDING,
            results={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Assign agents to task
        if task.assigned_agent_ids:
            agents = db.query(Agent).filter(Agent.id.in_(task.assigned_agent_ids)).all()
            db_task.assigned_agents = agents
            db.commit()
        
        # Broadcast task creation
        await websocket_manager.broadcast({
            "type": "task_created",
            "task": {
                "id": db_task.id,
                "title": db_task.title,
                "status": db_task.status.value,
                "priority": db_task.priority.value
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return db_task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tasks", response_model=List[TaskResponse])
async def list_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tasks."""
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get specific task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks/execute", response_model=TaskExecutionResponse)
async def execute_task(request: TaskExecutionRequest, db: Session = Depends(get_db)):
    """Execute a task with specified agents."""
    try:
        return await execution_engine.start_task_execution(db, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get execution status and details."""
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


# Dashboard Endpoints
@app.get("/api/dashboard/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """Get overall system status."""
    total_agents = db.query(Agent).count()
    active_agents = db.query(Agent).filter(Agent.status == AgentStatus.EXECUTING).count()
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
        system_uptime="Running",
        memory_usage={"status": "healthy"},
        last_updated=datetime.utcnow()
    )


@app.get("/api/dashboard/agents", response_model=List[AgentStatusSummary])
async def get_agent_status_summary(db: Session = Depends(get_db)):
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)