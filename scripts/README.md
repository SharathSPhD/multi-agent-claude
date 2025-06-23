# Scripts Directory

This directory contains various utility and testing scripts for the MCP Multi-Agent System.

## Available Scripts

### 🎮 Demo & Testing Scripts
- **`demo_frontend_controls.py`** - Demonstrates frontend control features with interactive examples
- **`test_full_frontend_functionality.py`** - Comprehensive frontend functionality testing
- **`test_real_workflow.py`** - End-to-end workflow testing with real agent execution

### ⚡ Execution Scripts  
- **`execute_with_available_agent.py`** - Execute tasks using available agents
- **`execute_workflow.py`** - Multi-agent workflow execution
- **`final_monitoring_report.py`** - Generate comprehensive system monitoring reports

### 📊 Legacy & Reference
- **`launch_system_old.py`** - Previous version of launcher with extensive testing (reference only)

## Usage

All scripts should be run from the project root directory with the virtual environment activated:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run any script
python scripts/demo_frontend_controls.py
```

## Requirements

- All scripts require the virtual environment to be activated
- Backend should be running on http://localhost:8000 for most scripts
- Claude Code SDK should be installed: `uv pip install claude-code-sdk`

## Notes

- These scripts are for development, testing, and demonstration purposes
- For production use, use the main launcher: `python launch_system.py`
- Comprehensive tests are in the `tests/` directory