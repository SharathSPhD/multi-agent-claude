#!/bin/bash
# Launch script for tech_lead agent

export AGENT_NAME="tech_lead"
export AGENT_ROLE="software_dev"
export AGENT_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/tech_lead_claude_config.json"

echo "🚀 Starting tech_lead agent..."
echo "📋 Description: Technical lead for software development coordination"
echo "🔧 MCP Servers: memory, filesystem"
echo "⚙️  Config: /mnt/e/Development/mcp_a2a/config/agents/tech_lead_claude_config.json"
echo ""

# Set working directory
cd /mnt/e/Development/mcp_a2a

# Launch Claude Code with autonomous startup and MCP configuration
echo "Launching Claude Code autonomously..."
claude --dangerously-skip-permissions \
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/tech_lead_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the tech_lead agent. Your role is Technical lead for software development coordination. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
echo "Starting Claude Code session..."
echo "Note: You will need to authenticate with your Anthropic account"
echo ""

# Set up MCP configuration for this session
export CLAUDE_MCP_CONFIG="/mnt/e/Development/mcp_a2a/config/agents/tech_lead_claude_config.json"
echo "✅ MCP configuration set: $CLAUDE_MCP_CONFIG"
    echo "✅ Configuration copied to Claude Code"
else
    echo "⚠️  Claude Code config directory not found. Run 'claude' first to set up."
fi

# Instructions for user
echo ""
echo "==================== AGENT INSTRUCTIONS ===================="
echo "Agent: tech_lead"
echo "Role: software_dev"
echo ""
echo "You are Technical lead for software development coordination.

Your role: software_dev

You are part of a multi-agent system. Your responsibilities:
- Focus on your domain expertise: Technical lead for software development coordination
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
    --mcp-config "/mnt/e/Development/mcp_a2a/config/agents/tech_lead_claude_config.json" \
    --add-dir "/mnt/e/Development/mcp_a2a" \
    "You are the tech_lead agent. Your role is Technical lead for software development coordination. You are part of a multi-agent system. Use your MCP tools for memory management and file operations. Available tools: memory, filesystem"
