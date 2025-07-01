# MCP Multi-Agent Orchestration Platform v2.2.0

A sophisticated multi-agent orchestration platform featuring **Complete Workflow Execution System** with **Claude CLI integration** for autonomous agent execution, real-time monitoring, dynamic web-based coordination, and comprehensive workflow control.

## 🎯 Overview

This platform has evolved from v1.0 (static CLI) to v2.2.0 (production-ready workflow execution system) enabling real-time multi-agent orchestration with Claude CLI non-interactive execution, advanced workflow patterns, web-based management interface, intelligent task delegation, and **full user control over execution workflows**.

### Key Features v2.2.0

- **Claude CLI Integration**: Complete migration from Claude Code SDK to Claude CLI with robust background execution and timeout handling
- **Complete Workflow Execution Pipeline**: End-to-end workflow execution with full API validation and real-time monitoring
- **Agent-Task Mapping Fixes**: Resolved critical orchestration issues ensuring proper task-agent relationships throughout execution
- **Advanced Orchestration Engine**: 7 workflow patterns (Orchestrator, Parallel, Router, Evaluator-Optimizer, Swarm, Sequential, Adaptive) with proper parameter passing
- **Dynamic Web Platform**: FastAPI backend + React frontend with real-time monitoring and comprehensive execution controls
- **🎮 Workflow Controls**: Pause/Resume/Abort individual executions with state preservation and proper cleanup
- **🗑️ Safe Agent Management**: Agent deletion with automatic task reassignment and comprehensive safety checks
- **Work Directory Management**: Custom project directory support for each workflow with proper isolation
- **Background Execution**: Claude CLI task execution with proper isolation and timeout handling
- **Real-time Monitoring**: WebSocket-based execution tracking with comprehensive logging and progress updates
- **Web-based Agent Management**: Complete CRUD interface for agent creation, configuration, and management
- **Database-Backed Persistence**: All workflow data stored and retrievable with comprehensive error handling
- **Cross-Platform Compatibility**: Validated WSL/Windows execution with proper path handling
- **Production Ready**: Full-stack application with comprehensive testing and error recovery

## 🚀 Quick Start v2.2.0

### Prerequisites

- Python 3.10+
- Node.js 18+ (for React frontend)
- Claude CLI (installed separately via npm or binary)
- Anthropic API key
- Modern web browser

### Installation & Launch

```bash
# Clone and setup virtual environment
git clone <repository-url>
cd mcp_a2a
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install backend dependencies
uv pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Set up API keys (create if needed)
# Ensure Claude CLI is properly configured with your API key

# Launch the complete system (backend + frontend)
python launch_system.py
```

### Access the Platform

```bash
# Web Interface
http://localhost:3000                    # Main dashboard with execution monitoring
http://localhost:3000/agents            # Agent management and configuration
http://localhost:3000/orchestration     # Advanced workflow orchestration
http://localhost:3000/tasks             # Task management and creation

# API Endpoints
http://localhost:8000/api/agents         # Agent CRUD operations
http://localhost:8000/api/tasks          # Task management
http://localhost:8000/api/workflows      # Workflow execution and pattern management
http://localhost:8000/api/execution      # Real-time execution monitoring
http://localhost:8000/docs               # Interactive API documentation
```

## 🏗️ Architecture v2.2.0

```
Frontend (React + Chakra UI)
    ↓ HTTP/WebSocket
FastAPI Backend (SQLAlchemy + WebSocket)
    ↓ Background processes
Claude CLI Agents (Isolated execution)
    ↓ Work directories
File-based coordination + Database persistence
```

### Core Components

- **FastAPI Backend**: High-performance async API with SQLAlchemy ORM and comprehensive error handling
- **React Frontend**: Modern web interface with real-time updates and comprehensive workflow controls
- **Claude CLI Integration**: Background agent execution with proper isolation and timeout handling
- **SQLite Database**: Persistent storage for agents, tasks, workflows, and execution history
- **WebSocket Manager**: Real-time communication for execution monitoring and status updates
- **Execution Engine**: Advanced task execution with timeout controls and error recovery
- **Advanced Orchestrator**: Multi-pattern workflow execution with proper agent-task coordination

## 📚 Complete Usage Guide

### Workflow Creation and Execution

```bash
# Create agents and tasks through web interface or API
# Access orchestration page to create workflow patterns
# Execute workflows with real-time monitoring

# Monitor workflow execution
curl http://localhost:8000/api/workflows/executions

# Check individual execution status
curl http://localhost:8000/api/execution/{execution_id}
```

### API Endpoints v2.2.0

**Core Management**:
- **Agents**: `/api/agents` (GET, POST, PUT, DELETE)
- **Tasks**: `/api/tasks` (GET, POST, PUT, DELETE)
- **Execution**: `/api/execution/start`, `/api/execution/status`, `/api/execution/{id}`

**Workflow Execution** (New v2.2.0):
- **Execute Patterns**: `POST /api/workflows/execute/{pattern_id}` - ✅ Full end-to-end tested
- **Monitor Executions**: `GET /api/workflows/executions` - ✅ Real-time status tracking
- **Individual Task Tracking**: `GET /api/execution/{id}` - ✅ Detailed progress monitoring

**Pattern Management** (New v2.2.0):
- **Create Patterns**: `POST /api/workflows/patterns` - ✅ Tested with work directories
- **List Patterns**: `GET /api/workflows/patterns` - ✅ Comprehensive pattern listing
- **Pattern Analysis**: `POST /api/workflows/analyze` - ✅ AI-powered workflow optimization

**Real-time Monitoring**:
- **WebSocket**: `/ws/updates` - Real-time system updates and execution progress

### Configuration Examples

**Create Custom Agent**:
```python
agent_data = {
    "name": "data_scientist",
    "role": "Data Analysis Expert", 
    "description": "Specialist in data analysis and machine learning",
    "capabilities": ["data_analysis", "visualization", "ml_modeling"],
    "tools": ["python", "pandas", "matplotlib", "scikit-learn"],
    "objectives": ["analyze data", "create insights", "build models"],
    "constraints": ["verify data quality", "document assumptions"]
}
response = requests.post("http://localhost:8000/api/agents", json=agent_data)
```

**Advanced Workflow Pattern Creation**:
```python
# Create workflow pattern with custom work directory
pattern_data = {
    "name": "Research and Report Workflow",
    "description": "Sequential research and documentation workflow",
    "workflow_type": "sequential",
    "agent_ids": ["agent1_id", "agent2_id"],
    "task_ids": ["research_task_id", "report_task_id"],
    "project_directory": "/path/to/work/directory",
    "configuration": {
        "timeout_minutes": 60,
        "retry_attempts": 3
    }
}
response = requests.post("http://localhost:8000/api/workflows/patterns", json=pattern_data)

# Execute workflow pattern
execution = requests.post(f"http://localhost:8000/api/workflows/execute/{pattern_id}")
```

## 🧪 Example Workflows

### 1. Research and Documentation Workflow

Located in `examples/reporter/`:
- **InfoGatherer Agent**: Web research and markdown file creation
- **ReportWriter Agent**: Professional HTML report generation
- **Sequential Execution**: Research → Documentation → Final Report

```bash
cd examples/reporter
python setup_workflow.py
# Access web interface to execute the workflow
```

### 2. Topology Visualization Workflow

Located in `examples/topology_visualization_workflow/`:
- **Topology Mathematician**: Mathematical concept analysis
- **Visualization Architect**: 3D visualization design
- **Python Developer**: Implementation and code development
- **Documentation Specialist**: Educational materials creation

### Multi-Agent Coordination Example

```python
# The system now properly handles agent-task relationships
# Tasks maintain their assigned agents throughout execution
# Workflow patterns control execution order and coordination
# Real-time monitoring tracks progress across all agents
```

## ✅ Status v2.2.0

**Production Ready** - Complete workflow execution system with:

### Core System ✅
- ✅ **Complete End-to-End Workflow Execution** - Comprehensive API test passed
- ✅ **Multi-Agent Task Distribution** - Confirmed proper round-robin assignment  
- ✅ **Work Directory Management** - Validated custom directory usage
- ✅ **Claude CLI Integration** - Background task execution confirmed
- ✅ **Result Serialization** - Complex object storage validated
- ✅ **Real-Time Monitoring** - Execution progress tracking working
- ✅ **Database Persistence** - Workflow patterns and executions stored correctly
- ✅ **Cross-Platform Compatibility** - WSL/Windows execution confirmed
- ✅ **Error Handling** - Comprehensive error recovery throughout pipeline

### Agent-Task Coordination ✅
- ✅ **Agent-Task Mapping Fixes** - Resolved critical orchestration issues
- ✅ **Task Assignment Preservation** - Agent assignments maintained throughout execution
- ✅ **Sequential Workflow Validation** - Proper task-agent relationship execution
- ✅ **Workflow Pattern Support** - All 7 patterns validated with correct coordination

### API and Integration ✅
- ✅ **Comprehensive API Test Suite** - Full integration testing completed
- ✅ **Frontend-Backend Integration** - React interface with real-time updates
- ✅ **WebSocket Communication** - Real-time execution monitoring
- ✅ **Error Recovery** - Graceful failure handling and cleanup

## 🛠️ Development

### Adding New Workflow Patterns

1. Extend `AdvancedOrchestrator` in `backend/services/advanced_orchestrator.py`
2. Add pattern to workflow type enumeration
3. Implement pattern logic with proper agent-task coordination
4. Update frontend pattern selection in `AdvancedOrchestrator.tsx`
5. Add comprehensive error handling and timeout management

### Custom Frontend Integration

```javascript
// React integration with real-time monitoring
const WorkflowAPI = {
  // Pattern management
  createPattern: (data) => fetch('/api/workflows/patterns', {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  }),
  
  // Workflow execution
  executePattern: (patternId) => fetch(`/api/workflows/execute/${patternId}`, {
    method: 'POST'
  }),
  
  // Real-time monitoring
  monitorExecution: (executionId) => {
    const ws = new WebSocket('ws://localhost:8000/ws/updates');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle real-time updates
    };
  }
};
```

### Project Structure v2.2.0

```
mcp_a2a/
├── backend/                    # FastAPI backend with SQLAlchemy
│   ├── main.py                # API endpoints and application setup
│   ├── models.py              # Database models (agents, tasks, workflows)
│   ├── schemas.py             # Pydantic models for API validation
│   ├── database.py            # Database configuration and setup
│   └── services/              # Business logic services
│       ├── execution_engine.py    # Task execution with Claude CLI
│       ├── advanced_orchestrator.py # Workflow pattern execution
│       └── claude_cli_augmented_llm.py # Claude CLI integration
├── frontend/                  # React frontend with Chakra UI
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Dashboard/     # Main dashboard with monitoring
│   │   │   ├── Orchestration/ # Workflow creation and management
│   │   │   ├── Agents/        # Agent management interface
│   │   │   └── Tasks/         # Task management interface
│   │   ├── services/          # API client services
│   │   └── types/             # TypeScript type definitions
│   └── package.json           # Frontend dependencies
├── examples/                  # Example workflows and demonstrations
│   ├── reporter/              # Research and documentation workflow
│   └── topology_visualization_workflow/ # Mathematical visualization workflow
├── tests/                     # Comprehensive test suite
│   ├── test_workflow_execution_api.py # Complete API integration tests
│   ├── backend/               # Backend unit tests
│   ├── frontend/              # Frontend component tests
│   └── integration/           # End-to-end integration tests
├── docs/                      # Comprehensive documentation
├── config/                    # Agent and system configurations
├── requirements.txt           # Python dependencies
├── launch_system.py          # System launcher with health checks
└── mcp_multiagent.db         # SQLite database
```

## 🔧 Troubleshooting v2.2.0

### Common Issues

1. **System won't start**: 
   - Check Python 3.10+ and dependencies: `python --version`
   - Verify virtual environment activation: `which python`
   - Install dependencies: `uv pip install -r requirements.txt`

2. **Claude CLI issues**:
   - Verify Claude CLI installation: `claude --version`
   - Check API key configuration
   - Test CLI functionality: `claude --help`

3. **Frontend connection issues**: 
   - Verify CORS settings for your IP address in `backend/main.py`
   - Check firewall settings for ports 3000 and 8000

4. **Database errors**: 
   - Check SQLite file permissions: `ls -la mcp_multiagent.db`
   - Verify database location: Should be in project root

5. **Workflow execution failures**:
   - Check work directory permissions
   - Verify agent-task assignments
   - Monitor execution logs through web interface

### Debug Commands v2.2.0

```bash
# Check system health
curl http://localhost:8000/health

# Test agent creation
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"test","role":"Test Agent","description":"Test agent"}'

# Monitor workflow executions
curl http://localhost:8000/api/workflows/executions

# Check execution details
curl http://localhost:8000/api/execution/{execution_id}

# View system logs
tail -f backend.log

# Check processes
ps aux | grep uvicorn
ps aux | grep claude
lsof -i :8000  # Check if port is in use
lsof -i :3000  # Check frontend port
```

### WSL Access Issues
If using WSL, the launcher automatically detects WSL and provides proper URLs:
```bash
# The launcher will automatically:
# 1. Detect WSL environment
# 2. Get WSL IP address
# 3. Open Windows browser with correct URL
# 4. Provide both Windows and WSL URLs
```

### Performance Optimization

- **Database**: Consider PostgreSQL for production workloads
- **Caching**: Add Redis for session management and caching
- **Scaling**: Use multiple worker processes with Gunicorn
- **Monitoring**: Enable structured logging with monitoring tools

## 📄 License

This project is part of the MCP Multi-Agent ecosystem.

## 🤝 Contributing

The advanced orchestration platform is production-ready with complete workflow execution capabilities. Key areas for contribution:

- **New Workflow Patterns**: Extend the 7 existing patterns with domain-specific coordination strategies
- **Frontend Enhancements**: Advanced visualization, workflow designer, execution analytics
- **Performance Optimization**: Caching, connection pooling, distributed execution
- **Integration Extensions**: External APIs, databases, monitoring services, CI/CD pipelines
- **Agent Templates**: Pre-built agent configurations for common use cases
- **Workflow Libraries**: Reusable workflow patterns for specific domains

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Follow the code style guidelines (Black, isort, mypy for Python; ESLint, Prettier for TypeScript)
4. Add comprehensive tests for new features
5. Update documentation as needed
6. Submit a pull request with detailed description

## 🔍 Advanced Features

### Workflow Pattern Types

1. **Sequential**: Tasks execute in order, each waiting for previous completion
2. **Parallel**: All tasks execute simultaneously
3. **Router**: Dynamic task routing based on conditions
4. **Orchestrator**: Central coordination with feedback loops
5. **Evaluator-Optimizer**: Iterative improvement cycles
6. **Swarm**: Distributed consensus-based execution
7. **Adaptive**: Dynamic strategy switching based on progress

### Real-time Monitoring Capabilities

- **Live Execution Tracking**: Real-time progress updates via WebSocket
- **Agent Status Monitoring**: Current activity and availability status
- **Task Progress Visualization**: Execution timeline and dependencies
- **Error Detection and Recovery**: Automatic retry and failure handling
- **Performance Metrics**: Execution time, success rates, resource usage

### Work Directory Isolation

- **Custom Project Directories**: Each workflow can specify its own work directory
- **File Isolation**: Agents work in isolated environments
- **Result Persistence**: All outputs preserved and accessible
- **Cross-platform Paths**: Proper handling of Windows/Linux path differences

---

**For detailed API documentation and development guides, see the `/docs` directory and [API Documentation](http://localhost:8000/docs) when running.**