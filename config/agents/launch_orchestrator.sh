#!/bin/bash
# Launch script for orchestrator agent

export AGENT_NAME="orchestrator"
export AGENT_ROLE="orchestrator"
export AGENT_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/orchestrator_claude_config.json"

echo "🚀 Starting orchestrator agent..."
echo "📋 Description: Central orchestrator for task coordination and planning"
echo "🔧 MCP Servers: memory, filesystem"
echo "⚙️  Config: /mnt/e/Development/mcp_a2a/config/agents/orchestrator_claude_config.json"
echo ""

# Set working directory
cd /mnt/e/Development/mcp_a2a

# Launch Claude Code with autonomous startup and MCP configuration
echo "Launching Claude Code autonomously..."
claude --dangerously-skip-permissions \
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/orchestrator_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the orchestrator agent. Your role is Central orchestrator for task coordination and planning. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
echo "Starting Claude Code session..."
echo "Note: You will need to authenticate with your Anthropic account"
echo ""

# Set up MCP configuration for this session
export CLAUDE_MCP_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/orchestrator_claude_config.json"
echo "✅ MCP configuration set: $CLAUDE_MCP_CONFIG"

# Instructions for user
echo ""
echo "==================== AGENT INSTRUCTIONS ===================="
echo "Agent: orchestrator"
echo "Role: orchestrator"
echo ""
echo "You are Central orchestrator for task coordination and planning.

Your role: orchestrator

You are part of a multi-agent system. Your responsibilities:
- Focus on your domain expertise: Central orchestrator for task coordination and planning
- Collaborate with other agents when needed
- Use your MCP tools for memory management and file operations
- Communicate progress and results clearly

Available tools: memory, filesystem
"
echo "=============================================================="
echo ""

# Launch Claude Code with autonomous startup and MCP configuration
echo "Launching Claude Code autonomously..."
claude --dangerously-skip-permissions \
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/orchestrator_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the orchestrator agent. Your role is Central orchestrator for task coordination and planning. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
