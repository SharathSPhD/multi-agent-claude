#!/bin/bash
# Launch script for mechanistic_interpretability_expert agent

export AGENT_NAME="mechanistic_interpretability_expert"
export AGENT_ROLE="domain_expert"
export AGENT_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/mechanistic_interpretability_expert_claude_config.json"

echo "🚀 Starting mechanistic_interpretability_expert agent..."
echo "📋 Description: Expert in mechanistic interpretability of ML models"
echo "🔧 MCP Servers: memory, filesystem, fetch"
echo "⚙️  Config: /mnt/e/Development/mcp_a2a/config/agents/mechanistic_interpretability_expert_claude_config.json"
echo ""

# Set working directory
cd /mnt/e/Development/mcp_a2a

# Launch Claude Code with autonomous startup and MCP configuration
echo "Launching Claude Code autonomously..."
claude --dangerously-skip-permissions \
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/mechanistic_interpretability_expert_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the mechanistic_interpretability_expert agent. Your role is Expert in mechanistic interpretability of ML models. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
echo "Starting Claude Code session..."
echo "Note: You will need to authenticate with your Anthropic account"
echo ""

# Set up MCP configuration for this session
export CLAUDE_MCP_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/mechanistic_interpretability_expert_claude_config.json"
echo "✅ MCP configuration set: $CLAUDE_MCP_CONFIG"
    echo "✅ Configuration copied to Claude Code"
else
    echo "⚠️  Claude Code config directory not found. Run 'claude' first to set up."
fi

# Instructions for user
echo ""
echo "==================== AGENT INSTRUCTIONS ===================="
echo "Agent: mechanistic_interpretability_expert"
echo "Role: domain_expert"
echo ""
echo "You are Expert in mechanistic interpretability of ML models.

Your role: domain_expert

You are part of a multi-agent system. Your responsibilities:
- Focus on your domain expertise: Expert in mechanistic interpretability of ML models
- Collaborate with other agents when needed
- Use your MCP tools for memory management and file operations
- Communicate progress and results clearly

Available tools: memory, filesystem, fetch
"
echo "=============================================================="
echo ""

# Launch Claude Code with autonomous startup and MCP configuration
echo "Launching Claude Code autonomously..."
claude --dangerously-skip-permissions \
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/mechanistic_interpretability_expert_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the mechanistic_interpretability_expert agent. Your role is Expert in mechanistic interpretability of ML models. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
