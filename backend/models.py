"""
Database models for dynamic multi-agent system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Agent(Base):
    """Dynamic agent definition model."""
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    role = Column(String(255), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    
    # JSON fields for flexible configuration
    capabilities = Column(JSON, default=list)  # List of agent capabilities
    tools = Column(JSON, default=list)  # List of available tools/MCP servers
    objectives = Column(JSON, default=list)  # List of primary objectives
    constraints = Column(JSON, default=list)  # List of constraints/limitations
    
    # Memory and behavior settings
    memory_settings = Column(JSON, default=dict)  # Memory configuration
    execution_settings = Column(JSON, default=dict)  # Execution parameters
    
    # Status and metadata
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime)
    
    # Relationships
    tasks = relationship("Task", back_populates="assigned_agents", secondary="task_agent_assignments")
    executions = relationship("Execution", back_populates="agent")


class Task(Base):
    """Dynamic task definition model."""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Task configuration
    expected_output = Column(Text)  # Description of expected results
    resources = Column(JSON, default=list)  # Required resources/files
    dependencies = Column(JSON, default=list)  # Task dependencies (task IDs)
    
    # Scheduling and priority
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    deadline = Column(DateTime)
    estimated_duration = Column(String(50))  # e.g., "2 hours", "30 minutes"
    
    # Status and results
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    results = Column(JSON, default=dict)  # Task execution results
    error_message = Column(Text)  # Error details if failed
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    assigned_agents = relationship("Agent", back_populates="tasks", secondary="task_agent_assignments")
    executions = relationship("Execution", back_populates="task")


class TaskAgentAssignment(Base):
    """Many-to-many relationship between tasks and agents."""
    __tablename__ = "task_agent_assignments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    role_in_task = Column(String(255))  # e.g., "primary", "collaborator", "reviewer"
    assigned_at = Column(DateTime, default=datetime.utcnow)


class Execution(Base):
    """Task execution tracking model."""
    __tablename__ = "executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    
    # Execution details
    status = Column(String(50), default="started")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    # Execution data
    logs = Column(JSON, default=list)  # Execution logs and messages
    output = Column(JSON, default=dict)  # Execution output/results
    error_details = Column(JSON, default=dict)  # Error information
    agent_response = Column(JSON, default=dict)  # Structured agent response from Claude Code
    work_directory = Column(String(500))  # Working directory for execution
    needs_interaction = Column(Boolean, default=False)  # Whether agent needs user input
    
    # Performance metrics
    duration_seconds = Column(String(50))
    memory_usage = Column(JSON, default=dict)
    api_calls_made = Column(JSON, default=list)
    
    # Relationships
    task = relationship("Task", back_populates="executions")
    agent = relationship("Agent", back_populates="executions")


class AgentCommunication(Base):
    """Agent-to-agent communication log."""
    __tablename__ = "agent_communications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_agent_id = Column(String(36), ForeignKey("agents.id"))
    to_agent_id = Column(String(36), ForeignKey("agents.id"))
    
    # Message details
    message_type = Column(String(50))  # e.g., "task_request", "result_share", "question"
    content = Column(JSON, nullable=False)  # Message content
    context = Column(JSON, default=dict)  # Additional context
    
    # Status
    sent_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    processed_at = Column(DateTime)
    response_required = Column(String(10), default="false")  # "true"/"false"
    
    # Relationships
    from_agent = relationship("Agent", foreign_keys=[from_agent_id])
    to_agent = relationship("Agent", foreign_keys=[to_agent_id])


class WorkflowPattern(Base):
    """Workflow pattern definitions for orchestration."""
    __tablename__ = "workflow_patterns"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_type = Column(String(50), nullable=False)  # orchestrator, parallel, sequential, etc.
    
    # JSON fields for pattern configuration
    agent_ids = Column(JSON, default=list)  # List of agent IDs
    task_ids = Column(JSON, default=list)   # List of task IDs
    dependencies = Column(JSON, default=dict)  # Task dependencies
    config = Column(JSON, default=dict)     # Pattern-specific configuration
    
    # Execution metadata
    user_objective = Column(Text)
    status = Column(String(50), default="active")  # active, archived, deprecated
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowExecution(Base):
    """Workflow execution tracking."""
    __tablename__ = "workflow_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern_id = Column(String(36), ForeignKey("workflow_patterns.id"), nullable=False)
    status = Column(String(50), default="running")  # running, completed, failed, cancelled
    
    # Execution tracking
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    progress_percentage = Column(JSON, default=0)
    current_step = Column(String(255))
    
    # Results and logs
    execution_logs = Column(JSON, default=list)
    results = Column(JSON, default=dict)
    error_details = Column(JSON, default=dict)
    
    # Relationships
    pattern = relationship("WorkflowPattern")


class SystemConfiguration(Base):
    """System-wide configuration settings."""
    __tablename__ = "system_configurations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(100))  # e.g., "execution", "memory", "communication"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)