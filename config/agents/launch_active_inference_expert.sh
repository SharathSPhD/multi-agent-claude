#!/bin/bash
# Launch script for active_inference_expert agent

export AGENT_NAME="active_inference_expert"
export AGENT_ROLE="domain_expert"
export AGENT_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/active_inference_expert_claude_config.json"

echo "🚀 Starting active_inference_expert agent..."
echo "📋 Description: Expert in active inference theory and implementation"
echo "🔧 MCP Servers: memory, filesystem, fetch"
echo "⚙️  Config: /mnt/e/Development/mcp_a2a/config/agents/active_inference_expert_claude_config.json"
echo ""

# Set working directory
cd /mnt/e/Development/mcp_a2a

# Launch Claude Code with autonomous startup and MCP configuration
echo "Launching Claude Code autonomously..."
claude --dangerously-skip-permissions \
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/active_inference_expert_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the active_inference_expert agent. Your role is Expert in active inference theory and implementation. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
echo "Starting Claude Code session..."
echo "Note: You will need to authenticate with your Anthropic account"
echo ""

# Set up MCP configuration for this session
export CLAUDE_MCP_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/active_inference_expert_claude_config.json"
echo "✅ MCP configuration set: $CLAUDE_MCP_CONFIG"
    echo "✅ Configuration copied to Claude Code"
else
    echo "⚠️  Claude Code config directory not found. Run 'claude' first to set up."
fi

# Instructions for user
echo ""
echo "==================== AGENT INSTRUCTIONS ===================="
echo "Agent: active_inference_expert"
echo "Role: domain_expert"
echo ""
echo "You are Expert in active inference theory and implementation.

Your role: domain_expert

You are part of a multi-agent system. Your responsibilities:
- Focus on your domain expertise: Expert in active inference theory and implementation
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
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/active_inference_expert_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the active_inference_expert agent. Your role is Expert in active inference theory and implementation. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
