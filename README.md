# MCP Multi-Agent Orchestration Platform v2.1

A sophisticated multi-agent orchestration platform that combines the **LastMile mcp-agent framework** with **Claude Code SDK integration** for autonomous agent execution, real-time monitoring, dynamic web-based coordination, and comprehensive workflow control.

## 🎯 Overview

This platform evolved from v1.0 (static CLI) to v2.1 (production-ready web platform) enabling real-time multi-agent orchestration with Claude Code non-interactive execution, advanced workflow patterns, web-based management interface, intelligent task delegation, and **full user control over execution workflows**.

### Key Features v2.1

- **Claude Code SDK Integration**: Non-interactive execution with robust error handling and multi-turn conversation support
- **Advanced Orchestration Engine**: 7 workflow patterns (Orchestrator, Parallel, Router, Evaluator-Optimizer, Swarm, Sequential, Adaptive)
- **Dynamic Web Platform**: FastAPI backend + React frontend with real-time monitoring and agent observation windows
- **🎮 Workflow Controls**: Pause/Resume/Abort individual executions with state preservation
- **🗑️ Safe Agent Management**: Agent deletion with automatic task reassignment and safety checks
- **Intelligent Agent Execution**: Claude Code spawning with working directories, response mirroring, and interaction detection
- **Real-time Monitoring**: WebSocket-based agent communication tracking and execution monitoring with individual agent windows
- **Web-based Agent Management**: Complete CRUD interface for agent creation, configuration, and management
- **Asynchronous Execution**: Advanced async/await patterns with parallel and sequential coordination
- **Production Ready**: Full-stack application with database persistence, error handling, and comprehensive testing

## 🚀 Quick Start v2.0

### Prerequisites

- Python 3.10+
- Node.js 18+ (for React frontend)
- FastAPI dependencies
- Anthropic API key
- Modern web browser

### Installation & Launch

```bash
# Install all dependencies (backend + frontend)
pip install -e .
npm install --prefix frontend

# Set up API keys in mcp_agent.secrets.yaml
anthropic_api_key: "your-api-key-here"

# Launch the complete system (backend + frontend)
python launch_system.py
```

### Access the Platform

```bash
# Web Interface
http://localhost:3000           # Main dashboard
http://localhost:3000/agents    # Agent management
http://localhost:3000/orchestration  # Advanced orchestration

# API Endpoints
http://localhost:8000/api/agents     # Agent CRUD
http://localhost:8000/api/tasks      # Task management
http://localhost:8000/api/orchestration  # Workflow execution
http://localhost:8000/docs       # API documentation
```

## 🏗️ Architecture

```
Orchestrator (mcp-agent framework)
    ↓ JSON task files + MCP memory
Specialized Agents (Claude Code CLI + MCP)
    ↓ Results via memory stores
Memory-based coordination
```

### Agent Types

- **orchestrator** - Central coordination and task planning
- **active_inference_expert** - Active inference theory and implementation  
- **mechanistic_interpretability_expert** - ML model interpretability
- **tech_lead** - Code review and technical coordination
- **software_architect** - System design and architecture
- **python_expert** - Python development specialist

## 📚 Complete Usage Guide

### Quick Start Demo
```bash
# Create and test agents immediately
python quick_start.py

# Monitor system status
curl http://localhost:8000/api/dashboard/status
```

### API Endpoints

**Agents**: `/api/agents` (GET, POST, PUT, DELETE)
**Tasks**: `/api/tasks` (GET, POST), `/api/tasks/execute` (POST)
**Orchestration**: `/api/orchestration/analyze`, `/api/orchestration/execute`, `/api/orchestration/monitor/{id}`
**Monitoring**: `/api/dashboard/status`, `/api/dashboard/agents`
**WebSocket**: `/ws/updates` (real-time system updates)

### Configuration Examples

**Create Custom Agent**:
```python
agent_data = {
    "name": "data_scientist",
    "role": "Data Analysis Expert", 
    "capabilities": ["data_analysis", "visualization", "ml_modeling"],
    "tools": ["python", "pandas", "matplotlib", "scikit-learn"],
    "objectives": ["analyze data", "create insights", "build models"],
    "constraints": ["verify data quality", "document assumptions"]
}
response = requests.post("http://localhost:8000/api/agents", json=agent_data)
```

**Advanced Orchestration**:
```python
# Create workflow with AI analysis
analysis = await orchestrator.analyze_workflow_requirements(
    agents=selected_agents,
    tasks=task_list,
    user_objective="Develop AI safety framework with expert review"
)

# Execute with recommended pattern
execution = await orchestrator.execute_workflow(
    workflow_type=analysis.recommended_workflow,
    agents=selected_agents,
    tasks=task_list
)
```

## 🧪 Example Usage

### Multi-Agent Conversation

```python
from mcp_a2a.dynamic_config import DynamicConfigBuilder
from mcp_a2a.conversation_engine import ConversationEngine

# Create research collaboration scenario
config_builder = DynamicConfigBuilder(base_config)
scenario_id = config_builder.create_scenario(
    name="AI Research Discussion",
    objective="Develop novel approach to transformer interpretability",
    agent_types=["active_inference_expert", "mechanistic_interpretability_expert"],
    conversation_rounds=3
)

# Execute multi-turn conversation
engine = ConversationEngine(runtime_config)
await engine.initialize()
session_id = await engine.start_conversation(scenario)
completed_session = await engine.complete_conversation(session_id)
```

### Agent Management

```bash
# Deploy specific agent
bash config/agents/launch_orchestrator.sh

# Stop all agents  
bash scripts/stop_agents.sh

# Check agent memory
ls -la memory/orchestrator_memory/
```

## ✅ Status

**Production Ready** - Fully functional multi-agent system with:

- ✅ 6 specialized agents operational
- ✅ Memory-based coordination working
- ✅ Multi-turn conversations tested
- ✅ Claude Code integration successful
- ✅ Autonomous deployment verified

### Test Results

```bash
✅ mcp-agent imports successful
✅ Agent initialization (6 agents)
✅ Task submission and tracking
✅ Memory system operational
✅ Multi-agent conversation system working
✅ Claude Code deployment successful
```

## 🛠️ Development

### Adding New Workflow Patterns

1. Extend `AdvancedOrchestrator` in `backend/services/advanced_orchestrator.py`
2. Add pattern to `WorkflowType` enum
3. Implement pattern logic in `execute_workflow` method
4. Update frontend pattern selection in `AdvancedOrchestrator.tsx`

### Custom Frontend Integration

```javascript
// React integration example
const AgentAPI = {
  create: (data) => fetch('/api/agents', {method: 'POST', body: JSON.stringify(data)}),
  list: () => fetch('/api/agents').then(r => r.json()),
  execute: (taskId, agentIds) => fetch('/api/tasks/execute', {
    method: 'POST', 
    body: JSON.stringify({task_id: taskId, agent_ids: agentIds})
  })
};
```

### Project Structure

```
mcp_a2a/
├── mcp_a2a/           # Core package
│   ├── core.py        # Agent implementations
│   ├── config.py      # Configuration management
│   ├── memory.py      # Memory management
│   └── cli.py         # Command interface
├── config/            # Agent configurations
├── memory/            # Agent memory stores
├── scripts/           # Deployment scripts
└── examples/          # Example workflows
```

## 🔧 Troubleshooting

### Common Issues

1. **System won't start**: Check Python 3.10+ and dependencies installed
2. **Frontend connection issues**: Verify CORS settings for your IP address
3. **Database errors**: Check SQLite permissions or PostgreSQL connection
4. **WebSocket failures**: Ensure no firewall blocking WebSocket connections

### Debug Commands

```bash
# Check system health
curl http://localhost:8000/api/dashboard/status

# Test agent creation
curl -X POST http://localhost:8000/api/agents -H "Content-Type: application/json" -d '{"name":"test","role":"Test Agent"}'

# View logs
tail -f backend.log

# Check processes
ps aux | grep uvicorn
lsof -i :8000  # Check if port is in use
```

### WSL Access Issues
If using WSL, add your WSL IP to CORS origins in `backend/main.py`:
```python
allow_origins=["http://localhost:3000", "http://YOUR_WSL_IP:3000"]
```

## 📄 License

This project is part of the MCP Multi-Agent ecosystem.

## 🤝 Contributing

The advanced orchestration platform is production-ready. Key areas for contribution:

- **New Workflow Patterns**: Extend the 7 existing patterns with domain-specific coordination
- **Frontend Enhancements**: Improve the React interface with advanced visualization
- **Performance Optimization**: Add caching, connection pooling, and scaling features
- **Integration Extensions**: Connect to external APIs, databases, and services

See `HOW_TO_RUN.md` for detailed development setup and API usage examples.

---

**For detailed documentation, configuration, and development guide, see [GUIDE.md](GUIDE.md)**