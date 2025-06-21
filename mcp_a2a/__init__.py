"""
Multi-Agent System with mcp-agent, A2A protocol, and MCP integration.

This package provides a sophisticated multi-agent system that combines:
- LastMile mcp-agent framework for orchestration
- Google A2A protocol for agent-to-agent communication
- MCP (Model Context Protocol) for tool integration
- Asynchronous execution for long-running tasks
"""

__version__ = "0.1.0"
__author__ = "MCP A2A Project"

from .core import MCPAgent, Orchestrator
from .config import AgentConfig, SystemConfig
from .memory import AgentMemory

__all__ = [
    "MCPAgent",
    "Orchestrator",
    "AgentConfig",
    "SystemConfig",
    "AgentMemory",
]