"""
Pydantic schemas for API request/response models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Agent Schemas
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    capabilities: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    memory_settings: Dict[str, Any] = Field(default_factory=dict)
    execution_settings: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=10)
    capabilities: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    objectives: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    memory_settings: Optional[Dict[str, Any]] = None
    execution_settings: Optional[Dict[str, Any]] = None
    status: Optional[AgentStatus] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: Optional[str]
    system_prompt: str
    capabilities: List[str]
    tools: List[str]
    objectives: List[str]
    constraints: List[str]
    memory_settings: Dict[str, Any]
    execution_settings: Dict[str, Any]
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime]
    
    class Config:
        from_attributes = True


# Task Schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    expected_output: Optional[str] = None
    resources: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # Duration in minutes
    assigned_agent_ids: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    expected_output: Optional[str] = None
    resources: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # Duration in minutes
    status: Optional[TaskStatus] = None
    assigned_agent_ids: Optional[List[str]] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    expected_output: Optional[str]
    resources: List[str]
    dependencies: List[str]
    priority: TaskPriority
    deadline: Optional[datetime]
    estimated_duration: Optional[int]  # Duration in minutes
    status: TaskStatus
    results: Dict[str, Any]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    assigned_agent_ids: Optional[List[str]] = Field(default=None)  # Agent IDs for easy form population
    assigned_agents: List[AgentResponse]
    
    class Config:
        from_attributes = True


# Execution Schemas
class ExecutionResponse(BaseModel):
    id: str
    task_id: Optional[str]
    agent_id: Optional[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    output: Dict[str, Any] = Field(default_factory=dict)
    error_details: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: Optional[str]
    memory_usage: Dict[str, Any] = Field(default_factory=dict)
    api_calls_made: List[Dict[str, Any]] = Field(default_factory=list)
    agent_response: Optional[Dict[str, Any]] = Field(default_factory=dict)
    work_directory: Optional[str] = None
    needs_interaction: Optional[bool] = False
    
    class Config:
        from_attributes = True


# Communication Schemas
class AgentMessage(BaseModel):
    from_agent_id: str
    to_agent_id: str
    message_type: str
    content: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
    response_required: bool = False


class AgentMessageResponse(BaseModel):
    id: str
    from_agent_id: str
    to_agent_id: str
    message_type: str
    content: Dict[str, Any]
    context: Dict[str, Any]
    sent_at: datetime
    received_at: Optional[datetime]
    processed_at: Optional[datetime]
    response_required: bool
    
    class Config:
        from_attributes = True


# System Configuration Schemas
class SystemConfigCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: Dict[str, Any]
    description: Optional[str] = None
    category: Optional[str] = None


class SystemConfigUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    category: Optional[str] = None


class SystemConfigResponse(BaseModel):
    id: str
    key: str
    value: Dict[str, Any]
    description: Optional[str]
    category: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard and Status Schemas
class SystemStatus(BaseModel):
    total_agents: int
    active_agents: int
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    system_uptime: str
    memory_usage: Dict[str, Any]
    last_updated: datetime


class AgentStatusSummary(BaseModel):
    agent_id: str
    name: str
    status: AgentStatus
    current_task_id: Optional[str]
    current_task_title: Optional[str]
    tasks_completed_today: int
    average_task_duration: Optional[str]
    last_active: Optional[datetime]


class TaskExecutionRequest(BaseModel):
    task_id: str
    agent_ids: Optional[List[str]] = None  # If None, use task's assigned agents
    force_restart: bool = False
    work_directory: Optional[str] = None  # User-configurable working directory for Claude Code execution


class TaskExecutionResponse(BaseModel):
    execution_id: str
    task_id: str
    status: str
    message: str
    started_at: datetime