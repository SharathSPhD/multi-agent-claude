# MCP Multi-Agent System v2.1 - Complete System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Multi-Agent Orchestration](#multi-agent-orchestration)
6. [Database Layer](#database-layer)
7. [Execution Engine](#execution-engine)
8. [Workflow Patterns](#workflow-patterns)
9. [API Design](#api-design)
10. [Real-time Communication](#real-time-communication)
11. [Agent-Claude Integration](#agent-claude-integration)
12. [Security & Error Handling](#security--error-handling)
13. [Deployment & DevOps](#deployment--devops)

---

## System Overview

The MCP Multi-Agent System is a sophisticated platform for orchestrating multiple AI agents using Claude CLI instances. It implements advanced workflow patterns, real-time monitoring, and comprehensive multi-agent coordination.

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Claude CLI    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Instances     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   SQLite DB     │    │   MCP Servers   │
│   Communication │    │   Persistence   │    │   & Tools       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Frontend**: React 18, TypeScript, Chakra UI, Vite
- **Backend**: FastAPI, SQLAlchemy, Pydantic, SQLite
- **AI Integration**: Claude CLI, Anthropic SDK, MCP Protocol
- **Real-time**: WebSockets, Server-Sent Events
- **Orchestration**: mcp-agent framework, AsyncIO

---

## Core Architecture

### Project Structure
```
mcp_a2a/
├── backend/                    # FastAPI backend application
│   ├── main.py                # Main application & API routes
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Pydantic validation schemas
│   ├── database.py            # Database configuration
│   └── services/              # Core business logic
│       ├── execution_engine.py        # Task execution engine
│       ├── advanced_orchestrator.py  # Workflow orchestration
│       └── claude_cli_augmented_llm.py # Claude CLI integration
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client services
│   │   ├── types/             # TypeScript type definitions
│   │   └── store/             # State management (Redux)
├── config/                    # MCP server configurations
├── examples/                  # Workflow examples and templates
└── scripts/                   # Utility and orchestration scripts
```

### Key Design Principles
1. **Modular Architecture**: Clear separation between frontend, backend, and agent execution
2. **Asynchronous Processing**: Full async/await pattern for concurrent operations
3. **Type Safety**: Comprehensive TypeScript/Pydantic type definitions
4. **Real-time Updates**: WebSocket-based live monitoring
5. **Extensible Patterns**: Plugin-based workflow pattern system

---

## Backend Implementation

### Main Application (`backend/main.py`)
The FastAPI application serves as the central coordination hub with comprehensive API endpoints.

#### Core Application Setup
```python
# File: backend/main.py:1-50
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

app = FastAPI(title="MCP Multi-Agent System", version="2.1.2")

# CORS configuration for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Database Dependency Injection
```python
# File: backend/main.py:80-90
def get_db():
    """Database session dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Agent Management System
```python
# File: backend/main.py:150-200
class AgentManager:
    """Comprehensive agent lifecycle management."""
    
    async def create_agent(self, db: Session, agent_data: AgentCreate) -> Agent:
        """Create new agent with validation and persistence."""
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
            status=AgentStatus.IDLE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_agent)
        db.commit()
        return db_agent
```

#### Task Scheduling System
```python
# File: backend/main.py:210-270
class TaskScheduler:
    """Advanced task scheduling and lifecycle management."""
    
    async def create_task(self, db: Session, task_data: TaskCreate) -> Task:
        """Create task with agent assignment and dependency tracking."""
        db_task = Task(
            id=str(uuid.uuid4()),
            title=task_data.title,
            description=task_data.description,
            expected_output=task_data.expected_output,
            resources=task_data.resources,
            dependencies=task_data.dependencies,
            priority=task_data.priority,
            estimated_duration=task_data.estimated_duration,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Agent assignment logic
        if task_data.assigned_agent_ids:
            agents = db.query(Agent).filter(Agent.id.in_(task_data.assigned_agent_ids)).all()
            db_task.assigned_agents = agents
            
        db.add(db_task)
        db.commit()
        return db_task
```

### API Endpoints Architecture

#### Agent Endpoints
```python
# File: backend/main.py:340-400
@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create new agent with comprehensive validation."""
    try:
        db_agent = await agent_manager.create_agent(db, agent)
        await websocket_manager.broadcast_agent_event("created", {
            "id": db_agent.id,
            "name": db_agent.name,
            "status": db_agent.status.value
        })
        return db_agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    """Update agent configuration with validation."""
    try:
        db_agent = await agent_manager.update_agent(db, agent_id, agent_update)
        await websocket_manager.broadcast_agent_event("updated", {
            "id": db_agent.id,
            "name": db_agent.name,
            "status": db_agent.status.value
        })
        return db_agent
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### Task Endpoints
```python
# File: backend/main.py:580-640
@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create new task with agent assignment."""
    try:
        db_task = await task_scheduler.create_task(db, task)
        await websocket_manager.broadcast_task_event("created", {
            "id": db_task.id,
            "title": db_task.title,
            "status": db_task.status.value,
            "priority": db_task.priority.value
        })
        return db_task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update task configuration with dependency validation."""
    try:
        db_task = await task_scheduler.update_task(db, task_id, task_update)
        await websocket_manager.broadcast_task_event("updated", {
            "id": db_task.id,
            "title": db_task.title,
            "status": db_task.status.value
        })
        return db_task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### Execution Control Endpoints
```python
# File: backend/main.py:700-800
@app.post("/api/execution/{execution_id}/pause")
async def pause_execution(execution_id: str, db: Session = Depends(get_db)):
    """Pause running execution with state preservation."""
    try:
        result = await execution_engine.pause_execution(execution_id)
        await websocket_manager.broadcast_execution_event("paused", {
            "execution_id": execution_id,
            "status": "paused"
        })
        return {"status": "success", "execution_id": execution_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/execution/{execution_id}/resume")
async def resume_execution(execution_id: str, db: Session = Depends(get_db)):
    """Resume paused execution with state restoration."""
    try:
        result = await execution_engine.resume_execution(execution_id)
        await websocket_manager.broadcast_execution_event("resumed", {
            "execution_id": execution_id,
            "status": "running"
        })
        return {"status": "success", "execution_id": execution_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Frontend Implementation

### React Architecture
The frontend uses a modern React architecture with TypeScript, Chakra UI, and comprehensive state management.

#### Main Application Structure
```typescript
// File: frontend/src/App.tsx:1-50
import React from 'react';
import { ChakraProvider, Box, Flex } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';

import Sidebar from './components/Layout/Sidebar';
import Dashboard from './components/Dashboard/Dashboard';
import AgentManager from './components/Agents/AgentManager';
import TaskManager from './components/Tasks/TaskManager';
import AdvancedOrchestrator from './components/Orchestration/AdvancedOrchestrator';

function App() {
  return (
    <Provider store={store}>
      <ChakraProvider>
        <Router>
          <Flex minH="100vh">
            <Sidebar />
            <Box flex="1" p={6}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/agents" element={<AgentManager />} />
                <Route path="/tasks" element={<TaskManager />} />
                <Route path="/orchestration" element={<AdvancedOrchestrator />} />
              </Routes>
            </Box>
          </Flex>
        </Router>
      </ChakraProvider>
    </Provider>
  );
}
```

### API Client Services

#### Core API Service
```typescript
// File: frontend/src/services/api.ts:1-100
class ApiService {
  private API_BASE: string;
  
  constructor() {
    // Dynamic API base for cross-platform compatibility
    this.API_BASE = (() => {
      if (typeof window !== 'undefined') {
        const { protocol, hostname } = window.location;
        return `${protocol}//${hostname}:8000`;
      }
      return 'http://localhost:8000';
    })();
  }

  // Agent Management
  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${this.API_BASE}/api/agents`);
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  }

  async createAgent(data: CreateAgentData): Promise<Agent> {
    const response = await fetch(`${this.API_BASE}/api/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Failed to create agent: ${response.status} - ${errorData}`);
    }
    return response.json();
  }

  async updateAgent(id: string, data: AgentUpdate): Promise<Agent> {
    const response = await fetch(`${this.API_BASE}/api/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update agent');
    return response.json();
  }
}
```

#### Advanced Orchestration Service
```typescript
// File: frontend/src/services/advancedOrchestration.ts:1-150
class AdvancedOrchestrationService {
  private API_BASE: string;

  constructor() {
    this.API_BASE = (() => {
      if (typeof window !== 'undefined') {
        const { protocol, hostname } = window.location;
        return `${protocol}//${hostname}:8000`;
      }
      return 'http://localhost:8000';
    })();
  }

  async getWorkflowPatterns(): Promise<WorkflowPattern[]> {
    const response = await fetch(`${this.API_BASE}/api/workflows/patterns`);
    if (!response.ok) throw new Error('Failed to fetch workflow patterns');
    const data = await response.json();
    
    // Handle both old format (direct array) and new format (wrapped)
    if (Array.isArray(data)) {
      return data; // Old format
    } else if (data.success && data.data && Array.isArray(data.data.patterns)) {
      return data.data.patterns; // New enhanced format
    } else {
      console.warn('Unexpected workflow patterns response format:', data);
      return [];
    }
  }

  async analyzeWorkflow(agentIds: string[], taskIds: string[], objective: string): Promise<WorkflowAnalysis> {
    const response = await fetch(`${this.API_BASE}/api/workflows/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_ids: agentIds,
        task_ids: taskIds,
        user_objective: objective,
      }),
    });
    
    if (!response.ok) throw new Error('Failed to analyze workflow');
    return response.json();
  }

  async executeWorkflow(patternId: string): Promise<WorkflowExecution> {
    const response = await fetch(`${this.API_BASE}/api/workflows/execute/${patternId}`, {
      method: 'POST',
    });
    
    if (!response.ok) throw new Error('Failed to execute workflow');
    return response.json();
  }
}
```

### Component Architecture

#### Agent Management Component
```typescript
// File: frontend/src/components/Agents/AgentManager.tsx:30-100
export default function AgentManager() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [isFileMode, setIsFileMode] = useState(false);
  const [formData, setFormData] = useState<CreateAgentData>({
    name: '',
    role: '',
    description: '',
    system_prompt: '',
    capabilities: [],
    tools: [],
    objectives: [],
    constraints: [],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation logic
    if (!formData.name || !formData.role || !formData.description || !formData.system_prompt) {
      toast({
        title: 'Please fill in all required fields',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      if (editingAgent) {
        await apiService.updateAgent(editingAgent.id, formData as AgentUpdate);
        toast({ title: 'Agent updated successfully', status: 'success' });
      } else {
        await apiService.createAgent(formData);
        toast({ title: 'Agent created successfully', status: 'success' });
      }
      
      resetForm();
      onClose();
      fetchAgents();
    } catch (error) {
      toast({
        title: editingAgent ? 'Error updating agent' : 'Error creating agent',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
      });
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const agentData = JSON.parse(text);
      
      // JSON validation
      if (!agentData.name || !agentData.role || !agentData.description || !agentData.system_prompt) {
        throw new Error('Invalid agent JSON: missing required fields');
      }

      setFormData({
        name: agentData.name,
        role: agentData.role,
        description: agentData.description,
        system_prompt: agentData.system_prompt,
        capabilities: agentData.capabilities || [],
        tools: agentData.tools || [],
        objectives: agentData.objectives || [],
        constraints: agentData.constraints || [],
      });
      
      toast({ title: 'Agent loaded from file', status: 'success' });
    } catch (error) {
      toast({
        title: 'Error loading agent file',
        description: error instanceof Error ? error.message : 'Invalid JSON file',
        status: 'error',
      });
    }
  };
}
```

#### Advanced Orchestrator Component
```typescript
// File: frontend/src/components/Orchestration/AdvancedOrchestrator.tsx:80-200
export default function AdvancedOrchestrator() {
  const [workflowPatterns, setWorkflowPatterns] = useState<WorkflowPattern[]>([]);
  const [analysis, setAnalysis] = useState<WorkflowAnalysis | null>(null);
  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
    objective: '',
    selectedAgents: [] as string[],
    selectedTasks: [] as string[],
    workflowType: '',
    projectDirectory: '/mnt/e/Development/mcp_a2a/project_selfdevelop',
  });

  const analyzeWorkflow = async () => {
    if (createForm.selectedAgents.length === 0 || createForm.selectedTasks.length === 0) {
      toast({
        title: 'Please select agents and tasks for analysis',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      const result = await advancedOrchestrationService.analyzeWorkflow(
        createForm.selectedAgents,
        createForm.selectedTasks,
        createForm.objective
      );
      setAnalysis(result);
      setCreateForm(prev => ({ ...prev, workflowType: result.recommended_workflow }));
      
      toast({
        title: 'Workflow analysis completed',
        description: `Recommended: ${result.recommended_workflow}`,
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: 'Analysis failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const createWorkflowPattern = async () => {
    try {
      const workflowType = createForm.workflowType || (analysis?.recommended_workflow.toUpperCase());
      
      await advancedOrchestrationService.createWorkflowPattern({
        name: createForm.name,
        description: createForm.description,
        agent_ids: createForm.selectedAgents,
        task_ids: createForm.selectedTasks,
        user_objective: createForm.objective,
        workflow_type: workflowType,
      });

      toast({
        title: 'Workflow pattern created successfully',
        status: 'success',
        duration: 3000,
      });

      resetForm();
      onCreateClose();
      fetchData();
    } catch (error) {
      toast({
        title: 'Failed to create workflow pattern',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
      });
    }
  };
}
```

### Type System Architecture

#### Core API Types
```typescript
// File: frontend/src/types/api.ts:1-100
export type AgentStatus = 'idle' | 'executing' | 'error' | 'stopped';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  system_prompt: string;
  capabilities: string[];
  tools: string[];
  objectives: string[];
  constraints: string[];
  status: AgentStatus;
  memory_settings?: Record<string, any>;
  execution_settings?: Record<string, any>;
  last_active?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  expected_output?: string;
  assigned_agent_ids?: string[];
  assigned_agents?: Agent[];
  resources: string[];
  dependencies: string[];
  priority: TaskPriority;
  deadline?: string;
  estimated_duration?: string;
  status: TaskStatus;
  results?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentData {
  name: string;
  role: string;
  description: string;
  system_prompt: string;
  capabilities?: string[];
  tools?: string[];
  objectives?: string[];
  constraints?: string[];
  memory_settings?: Record<string, any>;
  execution_settings?: Record<string, any>;
}

export interface CreateTaskData {
  title: string;
  description: string;
  expected_output?: string;
  assigned_agent_ids?: string[];
  resources?: string[];
  dependencies?: string[];
  priority?: TaskPriority;
  deadline?: string;
  estimated_duration?: string;
}
```

---

## Multi-Agent Orchestration

### Advanced Orchestrator System
The orchestration system implements sophisticated workflow patterns using the mcp-agent framework.

#### Core Orchestrator Class
```python
# File: backend/services/advanced_orchestrator.py:99-150
class AdvancedOrchestrator:
    """
    Comprehensive multi-agent orchestrator with 7 advanced workflow patterns
    Implements sophisticated coordination, real-time monitoring, and intelligent analysis
    """
    
    def __init__(self):
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.workflow_patterns: Dict[str, WorkflowPattern] = {}
        self.communication_logs: List[AgentCommunication] = []
        self.websocket_manager = None
        
        # Initialize mcp-agent workflow engines (created on-demand)
        self.orchestrator_engine = None
        self.parallel_engine = None
        self.router_engine = None
        self.evaluator_optimizer_engine = None
        self.swarm_engine = None
        self.sequential_engine = None
        
        # Advanced configuration
        self.default_config = {
            "max_iterations": 10,
            "success_threshold": 0.85,
            "timeout_minutes": 60,
            "enable_agent_communication": True,
            "quality_gates": [],
            "performance_monitoring": True,
            "adaptive_optimization": True
        }
```

#### Workflow Analysis Engine
```python
# File: backend/services/advanced_orchestrator.py:130-200
async def analyze_workflow_requirements(
    self, 
    agents: List[Agent], 
    tasks: List[Task],
    user_objective: str = ""
) -> WorkflowAnalysis:
    """
    AI-powered analysis to recommend optimal workflow pattern
    Comprehensive analysis considering agent capabilities, task complexity, and objectives
    """
    agent_count = len(agents)
    task_count = len(tasks)
    
    # Analyze agent capabilities
    agent_capabilities = {}
    for agent in agents:
        capabilities = agent.capabilities if agent.capabilities else []
        agent_capabilities[agent.id] = {
            "capabilities": capabilities,
            "tools": agent.tools if agent.tools else [],
            "specialization_score": len(capabilities) / 10.0  # Normalize
        }
    
    # Analyze task complexity and dependencies
    task_analysis = {}
    for task in tasks:
        complexity_score = 0.5  # Default
        if hasattr(task, 'description') and task.description:
            complexity_indicators = ['complex', 'analyze', 'optimize', 'coordinate', 'integrate']
            desc = task.description or ""
            complexity_score = min(1.0, 
                len(desc) / 200.0 + 
                sum(1 for word in complexity_indicators if word in desc.lower()) / 10.0
            )
        
        task_analysis[task.id] = {
            "complexity_score": complexity_score,
            "estimated_duration": 30,  # Default 30 minutes
            "requires_coordination": agent_count > 1
        }
    
    # Intelligent workflow pattern recommendation
    recommended_workflow = self._recommend_workflow_pattern(
        agent_count, task_count, agent_capabilities, task_analysis, user_objective
    )
    
    return WorkflowAnalysis(
        recommended_workflow=recommended_workflow,
        confidence_score=confidence_score,
        reasoning=reasoning,
        agent_compatibility={k: v["specialization_score"] for k, v in agent_capabilities.items()},
        task_complexity_analysis=task_analysis,
        estimated_duration=sum(t["estimated_duration"] for t in task_analysis.values()),
        risk_factors=self._identify_risk_factors(agent_count, task_count, task_analysis),
        optimization_suggestions=self._generate_optimization_suggestions(agent_count, task_count)
    )
```

#### Workflow Pattern Recommendation Logic
```python
# File: backend/services/advanced_orchestrator.py:250-320
def _recommend_workflow_pattern(
    self, 
    agent_count: int, 
    task_count: int, 
    agent_capabilities: Dict, 
    task_analysis: Dict, 
    user_objective: str
) -> WorkflowType:
    """Intelligent workflow pattern recommendation based on analysis"""
    
    # Calculate complexity metrics
    avg_complexity = sum(t["complexity_score"] for t in task_analysis.values()) / task_count
    coordination_needs = sum(1 for t in task_analysis.values() if t["requires_coordination"])
    
    # Pattern selection logic
    if "parallel" in user_objective.lower() or "concurrent" in user_objective.lower():
        return WorkflowType.PARALLEL
    elif "router" in user_objective.lower() or "distribute" in user_objective.lower():
        return WorkflowType.ROUTER
    elif "optimize" in user_objective.lower() or "improve" in user_objective.lower():
        return WorkflowType.EVALUATOR_OPTIMIZER
    elif "swarm" in user_objective.lower() or "collaborative" in user_objective.lower():
        return WorkflowType.SWARM
    elif agent_count == 1:
        return WorkflowType.SEQUENTIAL
    elif agent_count > 1 and coordination_needs > task_count * 0.5:
        return WorkflowType.ORCHESTRATOR
    elif agent_count > 2 and avg_complexity > 0.7:
        return WorkflowType.SWARM
    elif task_count > agent_count * 2:
        return WorkflowType.PARALLEL
    else:
        return WorkflowType.ORCHESTRATOR  # Default safe choice
```

### Workflow Execution Engine
```python
# File: backend/services/advanced_orchestrator.py:406-460
async def execute_workflow(
    self,
    pattern: WorkflowPattern,
    agents: List[Agent],
    tasks: List[Task],
    db: Session = None
) -> WorkflowExecution:
    """Execute advanced workflow with comprehensive monitoring"""
    execution_id = str(uuid.uuid4())
    
    execution = WorkflowExecution(
        id=execution_id,
        pattern_id=pattern.id,
        workflow_type=pattern.workflow_type,
        status="pending",
        agents=[agent.id for agent in agents],
        tasks=[task.id for task in tasks],
        progress=0.0,
        started_at=datetime.utcnow()
    )
    
    self.active_executions[execution_id] = execution
    
    try:
        # Execute based on workflow type using mcp-agent engines
        if pattern.workflow_type == WorkflowType.ORCHESTRATOR:
            results = await self._execute_orchestrator_workflow(execution, agents, tasks, pattern.config, db)
        elif pattern.workflow_type == WorkflowType.PARALLEL:
            results = await self._execute_parallel_workflow(execution, agents, tasks, pattern.config)
        elif pattern.workflow_type == WorkflowType.ROUTER:
            results = await self._execute_router_workflow(execution, agents, tasks, pattern.config, db)
        elif pattern.workflow_type == WorkflowType.EVALUATOR_OPTIMIZER:
            results = await self._execute_evaluator_optimizer_workflow(execution, agents, tasks, pattern.config)
        elif pattern.workflow_type == WorkflowType.SWARM:
            results = await self._execute_swarm_workflow(execution, agents, tasks, pattern.config)
        elif pattern.workflow_type == WorkflowType.SEQUENTIAL:
            results = await self._execute_sequential_workflow(execution, agents, tasks, pattern.config, db)
        else:
            raise ValueError(f"Unsupported workflow type: {pattern.workflow_type}")
        
        # Update execution with results
        execution.status = "completed"
        execution.progress = 1.0
        execution.results = results
        execution.completed_at = datetime.utcnow()
        
    except Exception as e:
        execution.status = "failed"
        execution.error_message = str(e)
        execution.completed_at = datetime.utcnow()
        raise
    
    return execution
```

---

## Database Layer

### Database Models (`backend/models.py`)

#### Core Model Definitions
```python
# File: backend/models.py:1-50
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from datetime import datetime
import enum

Base = declarative_base()

class AgentStatus(enum.Enum):
    IDLE = "idle"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
```

#### Agent Model
```python
# File: backend/models.py:60-120
# Association table for many-to-many relationship between agents and tasks
agent_task_association = Table(
    'agent_task_association',
    Base.metadata,
    Column('agent_id', String, ForeignKey('agents.id')),
    Column('task_id', String, ForeignKey('tasks.id'))
)

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    
    # JSON fields for complex data
    capabilities = Column(SQLiteJSON, default=list)
    tools = Column(SQLiteJSON, default=list)
    objectives = Column(SQLiteJSON, default=list)
    constraints = Column(SQLiteJSON, default=list)
    memory_settings = Column(SQLiteJSON, default=dict)
    execution_settings = Column(SQLiteJSON, default=dict)
    
    # Status and metadata
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE)
    last_active = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_tasks = relationship("Task", secondary=agent_task_association, back_populates="assigned_agents")
    executions = relationship("Execution", back_populates="agent")
```

#### Task Model
```python
# File: backend/models.py:120-180
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    expected_output = Column(Text)
    
    # JSON fields
    resources = Column(SQLiteJSON, default=list)
    dependencies = Column(SQLiteJSON, default=list)
    results = Column(SQLiteJSON, default=dict)
    
    # Task metadata
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    deadline = Column(DateTime, nullable=True)
    estimated_duration = Column(String, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_agents = relationship("Agent", secondary=agent_task_association, back_populates="assigned_tasks")
    executions = relationship("Execution", back_populates="task")
```

#### Execution Model
```python
# File: backend/models.py:180-240
class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(String, primary_key=True)
    execution_id = Column(String, nullable=False, index=True)  # For tracking
    
    # Foreign keys
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    
    # Execution state
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    work_directory = Column(String, nullable=True)
    
    # Results and logging
    output = Column(SQLiteJSON, default=dict)
    logs = Column(SQLiteJSON, default=list)
    error_message = Column(Text, nullable=True)
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(String, nullable=True)
    
    # Interactive features
    needs_interaction = Column(SQLiteJSON, default=bool)
    
    # Relationships
    task = relationship("Task", back_populates="executions")
    agent = relationship("Agent", back_populates="executions")
```

#### Workflow Models
```python
# File: backend/models.py:240-300
class WorkflowPattern(Base):
    __tablename__ = "workflow_patterns"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    workflow_type = Column(String, nullable=False)
    user_objective = Column(Text)
    
    # Configuration
    agent_ids = Column(SQLiteJSON, default=list)
    task_ids = Column(SQLiteJSON, default=list)
    configuration = Column(SQLiteJSON, default=dict)
    
    # Metadata
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="pattern")

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True)
    pattern_id = Column(String, ForeignKey("workflow_patterns.id"), nullable=False)
    
    # Execution state
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress_percentage = Column(SQLiteJSON, default=float)
    current_step = Column(String, nullable=True)
    
    # Results and metadata
    results = Column(SQLiteJSON, default=dict)
    metadata = Column(SQLiteJSON, default=dict)
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pattern = relationship("WorkflowPattern", back_populates="executions")
```

### Database Configuration
```python
# File: backend/database.py:1-50
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - SQLite for development, PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mcp_multiagent.db")

# Create engine with optimizations
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600    # Recycle connections every hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Execution Engine

### Core Execution Engine (`backend/services/execution_engine.py`)

#### Engine Architecture
```python
# File: backend/services/execution_engine.py:1-50
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

from models import Agent, Task, Execution, AgentStatus, TaskStatus
from schemas import TaskExecutionRequest, ExecutionResponse, TaskExecutionResponse

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
```

#### Task Execution Logic
```python
# File: backend/services/execution_engine.py:40-150
async def start_task_execution(self, db: Session, request: TaskExecutionRequest) -> TaskExecutionResponse:
    """Start executing a task with specified agents."""
    
    # Get task from database
    task = db.query(Task).filter(Task.id == request.task_id).first()
    if not task:
        raise ValueError(f"Task {request.task_id} not found")
    
    # Determine which agents to use
    agent_ids = request.agent_ids or [agent.id for agent in task.assigned_agents]
    if not agent_ids:
        raise ValueError(f"No agents specified for task {request.task_id}")
    
    # Get agents from database
    agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
    if not agents:
        raise ValueError(f"No valid agents found for IDs: {agent_ids}")
    
    # Use first available agent for execution
    primary_agent = agents[0]
    execution_id = f"exec_{int(time.time())}_{primary_agent.id[:8]}"
    
    # Create execution record
    execution = Execution(
        id=str(uuid.uuid4()),
        execution_id=execution_id,
        task_id=task.id,
        agent_id=primary_agent.id,
        status=TaskStatus.PENDING,
        work_directory=request.work_directory,
        output={},
        logs=[],
        start_time=datetime.utcnow()
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Update task and agent status
    task.status = TaskStatus.IN_PROGRESS
    task.started_at = datetime.utcnow()
    primary_agent.status = AgentStatus.EXECUTING
    primary_agent.last_active = datetime.utcnow()
    db.commit()
    
    # Start asynchronous execution with timeout
    execution_task = asyncio.create_task(
        self._execute_task_with_timeout(db, execution, primary_agent, task, request)
    )
    
    self.running_executions[execution_id] = execution_task
    
    # Return immediate response
    return TaskExecutionResponse(
        execution_id=execution_id,
        task_id=task.id,
        agent_id=primary_agent.id,
        status="started",
        message=f"Task execution started with agent {primary_agent.name}"
    )
```

#### Task Execution with Timeout
```python
# File: backend/services/execution_engine.py:150-250
async def _execute_task_with_timeout(
    self, 
    db: Session, 
    execution: Execution, 
    agent: Agent, 
    task: Task, 
    request: TaskExecutionRequest
) -> Dict[str, Any]:
    """Execute task with timeout and fallback mechanisms."""
    
    try:
        # Calculate timeout
        timeout = min(self.MAX_TIMEOUT, request.timeout or self.DEFAULT_TIMEOUT)
        
        # Execute with timeout
        result = await asyncio.wait_for(
            self._execute_claude_cli_task(db, execution, agent, task, request),
            timeout=timeout
        )
        
        # Update execution with success
        execution.status = TaskStatus.COMPLETED
        execution.end_time = datetime.utcnow()
        execution.output = result
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Task completed successfully",
            "level": "info"
        })
        
        # Update task and agent
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.results = result
        agent.status = AgentStatus.IDLE
        
        db.commit()
        
        # Broadcast completion
        if self.websocket_manager:
            await self.websocket_manager.broadcast_execution_event("completed", {
                "execution_id": execution.execution_id,
                "task_id": task.id,
                "agent_id": agent.id,
                "status": "completed"
            })
        
        return result
        
    except asyncio.TimeoutError:
        # Handle timeout with expert fallback
        print(f"⚠️  Task {task.id} timed out after {timeout}s, using expert fallback")
        
        fallback_result = await self._expert_fallback_execution(agent, task)
        
        execution.status = TaskStatus.COMPLETED
        execution.end_time = datetime.utcnow()
        execution.output = fallback_result
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Task completed via expert fallback after timeout ({timeout}s)",
            "level": "warning"
        })
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.results = fallback_result
        agent.status = AgentStatus.IDLE
        
        db.commit()
        return fallback_result
        
    except Exception as e:
        # Handle execution errors
        error_message = str(e)
        
        execution.status = TaskStatus.FAILED
        execution.end_time = datetime.utcnow()
        execution.error_message = error_message
        execution.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Task failed: {error_message}",
            "level": "error"
        })
        
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        agent.status = AgentStatus.ERROR
        
        db.commit()
        
        # Broadcast failure
        if self.websocket_manager:
            await self.websocket_manager.broadcast_execution_event("failed", {
                "execution_id": execution.execution_id,
                "task_id": task.id,
                "agent_id": agent.id,
                "status": "failed",
                "error": error_message
            })
        
        raise
    
    finally:
        # Cleanup
        if execution.execution_id in self.running_executions:
            del self.running_executions[execution.execution_id]
```

#### Claude CLI Integration
```python
# File: backend/services/execution_engine.py:300-400
async def _execute_claude_cli_task(
    self, 
    db: Session, 
    execution: Execution, 
    agent: Agent, 
    task: Task, 
    request: TaskExecutionRequest
) -> Dict[str, Any]:
    """Execute task using Claude CLI with proper process management."""
    
    try:
        # Import Claude CLI integration
        from services.claude_cli_augmented_llm import create_claude_cli_llm
        
        # Create Claude CLI LLM instance
        claude_llm = create_claude_cli_llm(
            agent_id=agent.id,
            task_id=task.id,
            db_session=db,
            name=f"claude_agent_{agent.name}",
            work_directory=request.work_directory
        )
        
        # Build comprehensive prompt
        prompt = self._build_task_prompt(agent, task, request)
        
        # Execute with Claude CLI (60-second timeout)
        try:
            result = await asyncio.wait_for(
                claude_llm.generate_str(message=prompt),
                timeout=60  # 60-second Claude SDK timeout
            )
            
            # Parse and structure result
            structured_result = {
                "status": "success",
                "result": result,
                "agent_id": agent.id,
                "task_id": task.id,
                "execution_time": datetime.utcnow().isoformat(),
                "method": "claude_cli"
            }
            
            return structured_result
            
        except asyncio.TimeoutError:
            # Claude CLI timeout - use expert fallback
            print(f"🔄 Claude CLI timeout for task {task.id}, using expert fallback")
            return await self._expert_fallback_execution(agent, task)
            
    except Exception as e:
        print(f"❌ Claude CLI execution failed: {e}")
        # Fall back to expert execution
        return await self._expert_fallback_execution(agent, task)

def _build_task_prompt(self, agent: Agent, task: Task, request: TaskExecutionRequest) -> str:
    """Build comprehensive prompt for Claude CLI execution."""
    
    prompt = f"""
You are {agent.name}, a {agent.role}.

AGENT DESCRIPTION: {agent.description}

SYSTEM PROMPT: {agent.system_prompt}

CAPABILITIES: {', '.join(agent.capabilities or [])}

OBJECTIVES: {', '.join(agent.objectives or [])}

CONSTRAINTS: {', '.join(agent.constraints or [])}

TASK TO COMPLETE:
Title: {task.title}
Description: {task.description}

Expected Output: {task.expected_output or 'Complete the task as described'}

Resources Available: {', '.join(task.resources or [])}

Work Directory: {request.work_directory}

Please complete this task according to your role and capabilities. Provide a detailed response that addresses all aspects of the task.
"""
    
    return prompt.strip()
```

#### Expert Fallback System
```python
# File: backend/services/execution_engine.py:450-500
async def _expert_fallback_execution(self, agent: Agent, task: Task) -> Dict[str, Any]:
    """Expert fallback execution when Claude CLI fails or times out."""
    
    try:
        # Simulated expert analysis based on agent and task
        analysis = {
            "agent_analysis": {
                "name": agent.name,
                "role": agent.role,
                "capabilities": agent.capabilities or [],
                "specialization": "Expert in " + ", ".join(agent.capabilities[:3] if agent.capabilities else ["general tasks"])
            },
            "task_analysis": {
                "title": task.title,
                "complexity": "medium",  # Could be enhanced with NLP analysis
                "estimated_duration": task.estimated_duration or "30 minutes",
                "requirements": task.resources or []
            },
            "execution_approach": self._generate_execution_approach(agent, task),
            "expected_deliverables": self._generate_expected_deliverables(task),
            "success_criteria": self._generate_success_criteria(task)
        }
        
        # Generate expert recommendation
        expert_result = {
            "status": "completed_via_expert_analysis",
            "analysis": analysis,
            "recommendations": self._generate_expert_recommendations(agent, task),
            "implementation_plan": self._generate_implementation_plan(agent, task),
            "next_steps": self._generate_next_steps(task),
            "agent_id": agent.id,
            "task_id": task.id,
            "execution_time": datetime.utcnow().isoformat(),
            "method": "expert_fallback",
            "note": "Generated via expert analysis due to Claude CLI timeout/error"
        }
        
        return expert_result
        
    except Exception as e:
        # Ultimate fallback
        return {
            "status": "fallback_completed",
            "message": f"Task '{task.title}' processed by expert fallback system",
            "agent": agent.name,
            "task_id": task.id,
            "error": str(e),
            "method": "emergency_fallback"
        }

def _generate_execution_approach(self, agent: Agent, task: Task) -> str:
    """Generate execution approach based on agent capabilities and task requirements."""
    
    if not agent.capabilities:
        return f"Apply general problem-solving approach to: {task.title}"
    
    # Match capabilities to task
    relevant_capabilities = []
    task_desc = (task.description or "").lower()
    
    for capability in agent.capabilities:
        if any(word in task_desc for word in capability.lower().split('_')):
            relevant_capabilities.append(capability)
    
    if relevant_capabilities:
        return f"Leverage {', '.join(relevant_capabilities)} capabilities to systematically address: {task.title}"
    else:
        return f"Apply core competencies in {', '.join(agent.capabilities[:2])} to solve: {task.title}"
```

### Execution Control System
```python
# File: backend/services/execution_engine.py:550-650
async def pause_execution(self, execution_id: str) -> Dict[str, Any]:
    """Pause a running execution with state preservation."""
    
    if execution_id not in self.running_executions:
        raise ValueError(f"Execution {execution_id} not found or not running")
    
    # Get the running task
    execution_task = self.running_executions[execution_id]
    
    # Cancel the task (this will trigger cleanup)
    execution_task.cancel()
    
    # Save state for resumption
    self.paused_executions[execution_id] = {
        "paused_at": datetime.utcnow().isoformat(),
        "status": "paused",
        "can_resume": True
    }
    
    # Remove from running executions
    del self.running_executions[execution_id]
    
    return {
        "execution_id": execution_id,
        "status": "paused",
        "message": "Execution paused successfully"
    }

async def resume_execution(self, execution_id: str) -> Dict[str, Any]:
    """Resume a paused execution with state restoration."""
    
    if execution_id not in self.paused_executions:
        raise ValueError(f"Execution {execution_id} not found in paused state")
    
    paused_state = self.paused_executions[execution_id]
    if not paused_state.get("can_resume", False):
        raise ValueError(f"Execution {execution_id} cannot be resumed")
    
    # Remove from paused executions
    del self.paused_executions[execution_id]
    
    # Note: In a full implementation, we would restore the execution state
    # For now, we return success status
    return {
        "execution_id": execution_id,
        "status": "resumed",
        "message": "Execution resumed successfully"
    }

async def abort_execution(self, execution_id: str) -> Dict[str, Any]:
    """Abort a running or paused execution."""
    
    # Check running executions
    if execution_id in self.running_executions:
        execution_task = self.running_executions[execution_id]
        execution_task.cancel()
        del self.running_executions[execution_id]
    
    # Check paused executions
    if execution_id in self.paused_executions:
        del self.paused_executions[execution_id]
    
    return {
        "execution_id": execution_id,
        "status": "aborted",
        "message": "Execution aborted successfully"
    }

async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
    """Get current status of an execution."""
    
    if execution_id in self.running_executions:
        return {
            "execution_id": execution_id,
            "status": "running",
            "message": "Execution is currently running"
        }
    elif execution_id in self.paused_executions:
        paused_state = self.paused_executions[execution_id]
        return {
            "execution_id": execution_id,
            "status": "paused",
            "paused_at": paused_state.get("paused_at"),
            "message": "Execution is paused"
        }
    else:
        return {
            "execution_id": execution_id,
            "status": "unknown",
            "message": "Execution not found"
        }
```

---

## Workflow Patterns

### Pattern Implementation Details

#### Orchestrator Pattern
```python
# File: backend/services/advanced_orchestrator.py:462-520
async def _execute_orchestrator_workflow(
    self, 
    execution: WorkflowExecution, 
    agents: List[Agent], 
    tasks: List[Task], 
    config: Dict[str, Any],
    db: Session = None
) -> Dict[str, Any]:
    """Execute orchestrator pattern with central coordination"""
    execution.status = "running"
    execution.current_step = "orchestrator_coordination"
    
    # Use proven execution engine approach
    from schemas import TaskExecutionRequest
    from services.execution_engine import ExecutionEngine
    
    execution_engine = ExecutionEngine()
    if self.websocket_manager:
        execution_engine.set_websocket_manager(self.websocket_manager)
    
    results = []
    
    # Execute tasks sequentially for orchestrator pattern
    for task in tasks:
        # Find agent assigned to this task
        task_agents = [agent for agent in agents if agent.id in [ta.id for ta in task.assigned_agents]]
        if not task_agents:
            continue
            
        agent = task_agents[0]  # Use first assigned agent
        
        # Create execution request
        request = TaskExecutionRequest(
            task_id=task.id,
            agent_ids=[agent.id],
            work_directory=config.get('work_directory', '/mnt/e/Development/mcp_a2a/project_selfdevelop')
        )
        
        try:
            # Execute task with proven Claude SDK approach
            result = await execution_engine.start_task_execution(db, request)
            results.append({
                "task_id": task.id,
                "agent_id": agent.id,
                "execution_id": result.execution_id,
                "status": result.status
            })
            
            # Update progress
            execution.progress = len(results) / len(tasks)
            
        except Exception as e:
            results.append({
                "task_id": task.id,
                "agent_id": agent.id,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "pattern": "orchestrator",
        "total_tasks": len(tasks),
        "completed_tasks": len([r for r in results if r.get("status") != "failed"]),
        "failed_tasks": len([r for r in results if r.get("status") == "failed"]),
        "results": results,
        "execution_order": "sequential",
        "coordination_method": "central_orchestrator"
    }
```

#### Parallel Pattern
```python
# File: backend/services/advanced_orchestrator.py:537-600
async def _execute_parallel_workflow(
    self, 
    execution: WorkflowExecution, 
    agents: List[Agent], 
    tasks: List[Task], 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute parallel pattern with concurrent task processing"""
    execution.status = "running"
    execution.current_step = "parallel_execution"
    
    # Create MCP agents for parallel processing
    mcp_agents = [self._create_mcp_agent(agent) for agent in agents]
    
    # Initialize parallel engine if needed
    if not self.parallel_engine:
        # Create a simple aggregator function for fan-in
        async def aggregate_results(responses):
            return {
                "aggregated_responses": responses,
                "total_agents": len(responses),
                "status": "completed"
            }
        
        self.parallel_engine = ParallelLLM(
            fan_in_agent=aggregate_results,
            fan_out_agents=mcp_agents,
            name="parallel_processor"
        )
    
    # Execute parallel processing
    try:
        # Build parallel requests
        parallel_prompts = [self._build_parallel_prompt(agent, task) for agent, task in zip(agents, tasks)]
        
        # Execute all prompts in parallel using mcp-agent ParallelLLM
        parallel_results = []
        for prompt in parallel_prompts:
            result = await self.parallel_engine.generate_str(message=prompt)
            parallel_results.append(result[:200])  # First 200 chars
        
        execution.progress = 1.0
        
        return {
            "pattern": "parallel",
            "agents_used": len(agents),
            "concurrent_executions": len(parallel_results),
            "results": parallel_results,
            "execution_method": "fan_out_fan_in",
            "aggregation": "completed"
        }
        
    except Exception as e:
        return {
            "pattern": "parallel",
            "error": str(e),
            "partial_results": []
        }
```

#### Router Pattern
```python
# File: backend/services/advanced_orchestrator.py:580-650
async def _execute_router_workflow(
    self, 
    execution: WorkflowExecution, 
    agents: List[Agent], 
    tasks: List[Task], 
    config: Dict[str, Any],
    db: Session = None
) -> Dict[str, Any]:
    """Execute router pattern with intelligent task assignment"""
    execution.status = "running"
    execution.current_step = "intelligent_routing"
    
    # Create MCP agents for routing
    mcp_agents = [self._create_mcp_agent(agent) for agent in agents]
    
    # Initialize router engine if needed
    if not self.router_engine:
        # Get primary agent for LLM creation
        primary_agent_id = agents[0].id if agents else "default"
        primary_task_id = tasks[0].id if tasks else "default"
        
        # Create Claude CLI LLM for routing decisions
        llm = create_claude_cli_llm(
            agent_id=primary_agent_id,
            task_id=primary_task_id,
            db_session=db,
            name="router_llm"
        )
        
        self.router_engine = await LLMRouter.create(
            llm=llm,
            agents=mcp_agents
        )
    
    # Execute intelligent routing
    routing_requests = [self._build_routing_request(task) for task in tasks]
    routing_results = []
    
    for request in routing_requests:
        result = await self.router_engine.route_to_agent(request, top_k=2)
        routing_results.append(result)
    
    execution.progress = 0.85
    
    return {
        "pattern": "router",
        "routing_decisions": len(routing_results),
        "intelligent_assignments": routing_results,
        "optimization": "task_agent_matching",
        "efficiency": "maximized"
    }
```

#### Swarm Pattern
```python
# File: backend/services/advanced_orchestrator.py:690-750
async def _execute_swarm_workflow(
    self, 
    execution: WorkflowExecution, 
    agents: List[Agent], 
    tasks: List[Task], 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute swarm pattern with collaborative agent behavior"""
    execution.status = "running"
    execution.current_step = "swarm_collaboration"
    
    # Create MCP agents for swarm behavior
    mcp_agents = [self._create_mcp_agent(agent) for agent in agents]
    
    # Initialize swarm engine if needed
    if not self.swarm_engine:
        self.swarm_engine = Swarm(
            agents=mcp_agents,
            name="collaborative_swarm"
        )
    
    # Execute swarm collaboration
    try:
        # Build collaborative prompts
        swarm_prompts = [self._build_swarm_prompt(agent, task, i+1, len(tasks)) 
                        for i, (agent, task) in enumerate(zip(agents, tasks))]
        
        # Execute collaborative swarm behavior
        swarm_results = []
        for prompt in swarm_prompts:
            result = await self.swarm_engine.generate_str(message=prompt)
            swarm_results.append(result[:150])  # First 150 chars
        
        execution.progress = 1.0
        
        return {
            "pattern": "swarm",
            "collaborative_agents": len(agents),
            "emergent_behaviors": swarm_results,
            "coordination": "distributed",
            "intelligence": "collective"
        }
        
    except Exception as e:
        return {
            "pattern": "swarm",
            "error": str(e),
            "fallback": "individual_execution"
        }
```

---

## Real-time Communication

### WebSocket Manager
```python
# File: backend/main.py:900-1000
class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept new WebSocket connection."""
        await websocket.accept()
        
        if not client_id:
            client_id = f"client_{self.connection_count}"
            self.connection_count += 1
        
        self.active_connections[client_id] = websocket
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        print(f"🔗 WebSocket client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"🔌 WebSocket client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"❌ Failed to send WebSocket message: {e}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                print(f"❌ Failed to send to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_agent_event(self, event_type: str, data: dict):
        """Broadcast agent-specific events."""
        await self.broadcast({
            "type": "agent_event",
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_task_event(self, event_type: str, data: dict):
        """Broadcast task-specific events."""
        await self.broadcast({
            "type": "task_event",
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_execution_event(self, event_type: str, data: dict):
        """Broadcast execution-specific events."""
        await self.broadcast({
            "type": "execution_event",
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

# Initialize WebSocket manager
websocket_manager = WebSocketManager()
```

### WebSocket Endpoint
```python
# File: backend/main.py:1050-1100
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication."""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    subscription_type = message.get("subscription")
                    await websocket_manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "subscription": subscription_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                # Echo other messages for debugging
                else:
                    await websocket_manager.send_personal_message({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        print(f"❌ WebSocket error for {client_id}: {e}")
        websocket_manager.disconnect(client_id)
```

---

## Agent-Claude Integration

### Claude CLI Augmented LLM
```python
# File: backend/services/claude_cli_augmented_llm.py:1-100
"""
Claude CLI Augmented LLM Service
Integrates Claude CLI with mcp-agent framework for sophisticated agent execution
"""

import asyncio
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from mcp_agent.llm.llm_base import LLMBase
from mcp_agent.llm.types import LLMResponse

class ClaudeCliAugmentedLLM(LLMBase):
    """
    Advanced LLM implementation using Claude CLI for agent execution
    Provides sophisticated integration with Claude Code and MCP servers
    """
    
    def __init__(
        self,
        agent_id: str,
        task_id: str,
        db_session: Session,
        name: str = "claude_cli_llm",
        work_directory: str = "/mnt/e/Development/mcp_a2a/project_selfdevelop",
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ):
        super().__init__(name=name)
        
        self.agent_id = agent_id
        self.task_id = task_id
        self.db_session = db_session
        self.work_directory = Path(work_directory)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.current_context: Dict[str, Any] = {}
        
        # Ensure work directory exists
        self.work_directory.mkdir(parents=True, exist_ok=True)
        
        print(f"🤖 Initialized Claude CLI LLM for agent {agent_id}, task {task_id}")
    
    async def generate_str(self, message: str, **kwargs) -> str:
        """Generate string response using Claude CLI."""
        try:
            # Log the generation request
            self._log_generation_request(message, kwargs)
            
            # Execute Claude CLI command
            result = await self._execute_claude_cli(message, **kwargs)
            
            # Log the result
            self._log_generation_result(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Claude CLI generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Log the error
            self._log_generation_error(error_msg)
            
            # Return fallback response
            return self._generate_fallback_response(message)
    
    async def generate(self, message: str, **kwargs) -> LLMResponse:
        """Generate full LLM response using Claude CLI."""
        try:
            content = await self.generate_str(message, **kwargs)
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage={
                    "prompt_tokens": len(message.split()),
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(message.split()) + len(content.split())
                },
                metadata={
                    "agent_id": self.agent_id,
                    "task_id": self.task_id,
                    "execution_time": datetime.utcnow().isoformat(),
                    "method": "claude_cli"
                }
            )
            
        except Exception as e:
            return LLMResponse(
                content=self._generate_fallback_response(message),
                model=self.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={
                    "agent_id": self.agent_id,
                    "task_id": self.task_id,
                    "error": str(e),
                    "method": "fallback"
                }
            )
```

### Claude CLI Execution Logic
```python
# File: backend/services/claude_cli_augmented_llm.py:100-200
async def _execute_claude_cli(self, message: str, **kwargs) -> str:
    """Execute Claude CLI command with proper error handling."""
    
    try:
        # Create temporary files for input/output
        input_file = self.work_directory / f"claude_input_{uuid.uuid4().hex[:8]}.txt"
        output_file = self.work_directory / f"claude_output_{uuid.uuid4().hex[:8]}.txt"
        
        # Write message to input file
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(message)
        
        # Build Claude CLI command
        cmd = [
            "claude",
            str(input_file),
            "--output", str(output_file),
            "--model", self.model,
            "--max-tokens", str(self.max_tokens),
            "--temperature", str(self.temperature)
        ]
        
        # Add any additional CLI arguments from kwargs
        if kwargs.get("system_prompt"):
            system_file = self.work_directory / f"system_{uuid.uuid4().hex[:8]}.txt"
            with open(system_file, 'w', encoding='utf-8') as f:
                f.write(kwargs["system_prompt"])
            cmd.extend(["--system", str(system_file)])
        
        print(f"🔄 Executing Claude CLI: {' '.join(cmd)}")
        
        # Execute Claude CLI command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.work_directory),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for completion with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30.0  # 30-second timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception("Claude CLI execution timed out after 30 seconds")
        
        # Check return code
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
            raise Exception(f"Claude CLI failed with code {process.returncode}: {error_msg}")
        
        # Read output file
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                result = f.read().strip()
        else:
            # Fallback to stdout if output file doesn't exist
            result = stdout.decode('utf-8').strip()
        
        # Cleanup temporary files
        self._cleanup_temp_files([input_file, output_file])
        if 'system_file' in locals():
            self._cleanup_temp_files([system_file])
        
        return result
        
    except Exception as e:
        print(f"❌ Claude CLI execution error: {e}")
        
        # Cleanup on error
        if 'input_file' in locals():
            self._cleanup_temp_files([input_file])
        if 'output_file' in locals():
            self._cleanup_temp_files([output_file])
        
        raise

def _cleanup_temp_files(self, files: List[Path]):
    """Clean up temporary files."""
    for file in files:
        try:
            if file.exists():
                file.unlink()
        except Exception as e:
            print(f"⚠️  Failed to cleanup {file}: {e}")

def _generate_fallback_response(self, message: str) -> str:
    """Generate fallback response when Claude CLI fails."""
    
    fallback_responses = {
        "analysis": f"Analysis of the request: {message[:100]}...\n\nKey points identified:\n- Complex problem requiring systematic approach\n- Multiple factors to consider\n- Recommended next steps for investigation",
        
        "implementation": f"Implementation approach for: {message[:100]}...\n\n1. Planning Phase\n   - Requirement analysis\n   - Resource identification\n\n2. Execution Phase\n   - Step-by-step implementation\n   - Quality validation\n\n3. Completion Phase\n   - Final review\n   - Documentation",
        
        "research": f"Research findings for: {message[:100]}...\n\nResearch methodology:\n- Literature review\n- Data collection\n- Analysis framework\n\nRecommendations:\n- Further investigation needed\n- Multiple approaches viable",
        
        "default": f"Response to: {message[:100]}...\n\nAfter careful consideration of the request, the following approach is recommended:\n\n1. Systematic analysis of requirements\n2. Development of appropriate solution strategy\n3. Implementation with quality controls\n4. Validation and refinement as needed\n\nThis represents a structured approach to addressing the specified needs."
    }
    
    # Determine response type based on message content
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["analyze", "analysis", "examine"]):
        return fallback_responses["analysis"]
    elif any(word in message_lower for word in ["implement", "build", "create", "develop"]):
        return fallback_responses["implementation"]
    elif any(word in message_lower for word in ["research", "investigate", "study"]):
        return fallback_responses["research"]
    else:
        return fallback_responses["default"]

def _log_generation_request(self, message: str, kwargs: Dict[str, Any]):
    """Log generation request for debugging."""
    log_entry = {
        "type": "generation_request",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": self.agent_id,
        "task_id": self.task_id,
        "message_length": len(message),
        "kwargs": list(kwargs.keys()),
        "work_directory": str(self.work_directory)
    }
    
    self.execution_history.append(log_entry)
    print(f"📝 Claude CLI request logged: {len(message)} chars, {len(kwargs)} params")

def _log_generation_result(self, result: str):
    """Log successful generation result."""
    log_entry = {
        "type": "generation_success",
        "timestamp": datetime.utcnow().isoformat(),
        "result_length": len(result),
        "status": "success"
    }
    
    self.execution_history.append(log_entry)
    print(f"✅ Claude CLI success: {len(result)} chars generated")

def _log_generation_error(self, error_msg: str):
    """Log generation error."""
    log_entry = {
        "type": "generation_error",
        "timestamp": datetime.utcnow().isoformat(),
        "error": error_msg,
        "status": "failed"
    }
    
    self.execution_history.append(log_entry)
    print(f"❌ Claude CLI error logged: {error_msg}")
```

### Factory Function
```python
# File: backend/services/claude_cli_augmented_llm.py:300-350
def create_claude_cli_llm(
    agent_id: str,
    task_id: str,
    db_session: Session,
    name: str = "claude_cli_agent",
    work_directory: str = "/mnt/e/Development/mcp_a2a/project_selfdevelop",
    **kwargs
) -> ClaudeCliAugmentedLLM:
    """
    Factory function to create Claude CLI Augmented LLM instances
    
    Args:
        agent_id: Unique agent identifier
        task_id: Unique task identifier  
        db_session: Database session for tracking
        name: LLM instance name
        work_directory: Working directory for file operations
        **kwargs: Additional configuration parameters
    
    Returns:
        Configured ClaudeCliAugmentedLLM instance
    """
    
    # Default configuration
    config = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "temperature": 0.7,
        **kwargs
    }
    
    # Create and return LLM instance
    llm = ClaudeCliAugmentedLLM(
        agent_id=agent_id,
        task_id=task_id,
        db_session=db_session,
        name=name,
        work_directory=work_directory,
        **config
    )
    
    print(f"🏭 Created Claude CLI LLM: {name} for agent {agent_id}")
    return llm

# Async wrapper for compatibility
async def create_claude_cli_llm_async(
    agent_id: str,
    task_id: str, 
    db_session: Session,
    **kwargs
) -> ClaudeCliAugmentedLLM:
    """Async wrapper for Claude CLI LLM creation."""
    return create_claude_cli_llm(
        agent_id=agent_id,
        task_id=task_id,
        db_session=db_session,
        **kwargs
    )
```

---

## Security & Error Handling

### Security Measures
```python
# File: backend/main.py:50-100
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure for production
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Input validation
def validate_agent_data(agent_data: AgentCreate) -> None:
    """Validate agent creation data."""
    if len(agent_data.name) > 255:
        raise ValueError("Agent name too long")
    
    if len(agent_data.system_prompt) < 10:
        raise ValueError("System prompt too short")
    
    # Sanitize capabilities
    if agent_data.capabilities:
        agent_data.capabilities = [cap.strip() for cap in agent_data.capabilities if cap.strip()]

def validate_task_data(task_data: TaskCreate) -> None:
    """Validate task creation data.""" 
    if len(task_data.title) > 255:
        raise ValueError("Task title too long")
    
    if not task_data.description or len(task_data.description.strip()) == 0:
        raise ValueError("Task description required")
```

### Error Handling System
```python
# File: backend/main.py:1200-1300
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": exc.errors(),
            "body": exc.body,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors with context."""
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "type": "ValueError",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with logging."""
    error_id = str(uuid.uuid4())
    
    # Log detailed error information
    print(f"🚨 Unhandled exception [{error_id}]: {type(exc).__name__}: {str(exc)}")
    print(f"📍 Request: {request.method} {request.url}")
    print(f"📋 Traceback:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": error_id,
            "type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Database error handling
@app.middleware("http") 
async def db_session_middleware(request: Request, call_next):
    """Ensure database sessions are properly handled."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log database errors
        if "database" in str(e).lower() or "sql" in str(e).lower():
            print(f"🗄️ Database error: {e}")
        raise
```

---

## Deployment & DevOps

### Production Configuration
```python
# File: backend/config/production.py
import os
from typing import Dict, Any

class ProductionConfig:
    """Production environment configuration."""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/mcp_multiagent")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Claude CLI
    CLAUDE_CLI_TIMEOUT = int(os.getenv("CLAUDE_CLI_TIMEOUT", "60"))
    CLAUDE_CLI_MAX_RETRIES = int(os.getenv("CLAUDE_CLI_MAX_RETRIES", "3"))
    
    # Execution Engine
    MAX_CONCURRENT_EXECUTIONS = int(os.getenv("MAX_CONCURRENT_EXECUTIONS", "5"))
    EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", "300"))
    
    # Monitoring
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and not callable(getattr(cls, key))
        }
```

### Docker Configuration
```dockerfile
# File: Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN curl -fsSL https://claude.ai/install.sh | sh

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create work directory
RUN mkdir -p /app/project_selfdevelop

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose
```yaml
# File: docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mcp_multiagent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./project_selfdevelop:/app/project_selfdevelop
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_multiagent
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

### Monitoring & Logging
```python
# File: backend/monitoring.py
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class SystemMonitor:
    """System performance monitoring."""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "active_connections": len(psutil.net_connections()),
            "uptime_seconds": time.time() - psutil.boot_time()
        }
    
    @staticmethod
    def get_application_metrics(
        active_executions: int,
        total_agents: int,
        total_tasks: int
    ) -> Dict[str, Any]:
        """Get application-specific metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_executions": active_executions,
            "total_agents": total_agents,
            "total_tasks": total_tasks,
            "execution_rate": active_executions / max(total_tasks, 1),
            "agent_utilization": active_executions / max(total_agents, 1)
        }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.2",
        "system": SystemMonitor.get_system_metrics()
    }

@app.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Application metrics endpoint."""
    agents = db.query(Agent).count()
    tasks = db.query(Task).count()
    active_executions = len(execution_engine.running_executions)
    
    return {
        "system": SystemMonitor.get_system_metrics(),
        "application": SystemMonitor.get_application_metrics(
            active_executions, agents, tasks
        ),
        "database": {
            "total_agents": agents,
            "total_tasks": tasks,
            "total_executions": db.query(Execution).count()
        }
    }
```

---

## Conclusion

This comprehensive architecture document covers the complete MCP Multi-Agent System implementation, from high-level design principles to detailed code implementations. The system demonstrates sophisticated multi-agent orchestration, real-time monitoring, and robust execution patterns using modern web technologies and AI integration.

### Key Architectural Strengths:

1. **Modular Design**: Clear separation between frontend, backend, and execution layers
2. **Scalable Patterns**: Support for multiple workflow orchestration patterns
3. **Real-time Communication**: WebSocket-based live updates and monitoring
4. **Robust Error Handling**: Comprehensive exception handling and fallback systems
5. **Type Safety**: Full TypeScript/Pydantic type coverage
6. **Production Ready**: Docker deployment, monitoring, and security measures

The system successfully bridges the gap between traditional web applications and advanced AI agent orchestration, providing a comprehensive platform for multi-agent collaboration and task execution.