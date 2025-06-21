"""
Configuration management for the multi-agent system.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pathlib import Path
import yaml
import os


class MCPServerConfig(BaseModel):
    """Configuration for MCP server connections."""
    name: str
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    name: str
    type: str  # e.g., "domain_expert", "software_dev", "orchestrator"
    description: str
    capabilities: List[str] = Field(default_factory=list)
    mcp_servers: List[str] = Field(default_factory=list)
    memory_store: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-3-5-sonnet-20241022"
    system_prompt: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    tools: List[str] = Field(default_factory=list)
    enabled: bool = True


class SystemConfig(BaseModel):
    """Main system configuration."""
    name: str = "MCP Multi-Agent System"
    version: str = "0.1.0"
    
    # Core settings
    base_path: Path = Field(default_factory=lambda: Path("/mnt/e/Development/mcp_a2a"))
    memory_path: Path = Field(default_factory=lambda: Path("/mnt/e/Development/mcp_a2a/memory"))
    
    # MCP servers configuration
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    
    # Agents configuration
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    
    # Orchestration settings
    orchestrator_agent: str = "orchestrator"
    max_concurrent_tasks: int = 10
    task_timeout: int = 3600  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def load_from_file(cls, config_path: Path) -> "SystemConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        return cls(**data)
    
    def save_to_file(self, config_path: Path):
        """Save configuration to YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, indent=2)
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent."""
        return self.agents.get(agent_name)
    
    def add_agent(self, agent_config: AgentConfig):
        """Add agent configuration."""
        self.agents[agent_config.name] = agent_config
    
    def get_mcp_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get MCP server configuration."""
        return self.mcp_servers.get(server_name)


def create_default_config() -> SystemConfig:
    """Create default system configuration with predefined agents."""
    
    # Default MCP servers
    mcp_servers = {
        "memory": MCPServerConfig(
            name="memory",
            command="python",
            args=["-m", "mcp_memory"],
            env={"MEMORY_PATH": "/mnt/e/Development/mcp_a2a/memory"}
        ),
        "filesystem": MCPServerConfig(
            name="filesystem", 
            command="python",
            args=["-m", "mcp_filesystem"],
            env={"ALLOWED_DIRS": "/mnt/e/Development"}
        ),
        "web": MCPServerConfig(
            name="web",
            command="python", 
            args=["-m", "mcp_web"],
            env={}
        )
    }
    
    # Default agents
    agents = {
        "orchestrator": AgentConfig(
            name="orchestrator",
            type="orchestrator",
            description="Central orchestrator for task coordination and planning",
            capabilities=["task_planning", "agent_coordination", "workflow_management"],
            mcp_servers=["memory", "filesystem"],
            memory_store="orchestrator_memory",
            system_prompt="""You are the central orchestrator agent responsible for:
- Breaking down complex tasks into subtasks
- Assigning tasks to appropriate specialized agents
- Coordinating multi-agent workflows
- Managing task dependencies and execution order
- Monitoring progress and handling failures
- Synthesizing results from multiple agents""",
            tools=["task_planning", "agent_communication", "workflow_execution"]
        ),
        
        "active_inference_expert": AgentConfig(
            name="active_inference_expert", 
            type="domain_expert",
            description="Expert in active inference theory and implementation",
            capabilities=["active_inference", "bayesian_inference", "predictive_processing"],
            mcp_servers=["memory", "filesystem", "web"],
            memory_store="active_inference_memory",
            system_prompt="""You are an expert in active inference, focusing on:
- Active inference theory and mathematical foundations
- Bayesian brain hypothesis and predictive processing
- Implementation of active inference models
- Research in computational neuroscience
- Free energy principle applications""",
            tools=["research", "mathematical_modeling", "code_analysis"]
        ),
        
        "mechanistic_interpretability_expert": AgentConfig(
            name="mechanistic_interpretability_expert",
            type="domain_expert", 
            description="Expert in mechanistic interpretability of ML models",
            capabilities=["interpretability", "neural_analysis", "feature_visualization"],
            mcp_servers=["memory", "filesystem", "web"],
            memory_store="interpretability_memory",
            system_prompt="""You are an expert in mechanistic interpretability, specializing in:
- Understanding how neural networks work internally
- Feature visualization and activation analysis
- Circuit analysis in transformer models
- Mechanistic interpretability research and tools
- Model behavior analysis and explanation""",
            tools=["model_analysis", "visualization", "research"]
        ),
        
        "tech_lead": AgentConfig(
            name="tech_lead",
            type="software_dev",
            description="Technical lead for software development coordination",
            capabilities=["code_review", "architecture_design", "team_coordination"],
            mcp_servers=["memory", "filesystem"],
            memory_store="tech_lead_memory", 
            system_prompt="""You are a technical lead responsible for:
- Code review and quality assurance
- Architecture decisions and technical guidance
- Coordinating development tasks across agents
- Ensuring best practices and coding standards
- Managing technical debt and refactoring efforts""",
            tools=["code_review", "testing", "deployment"]
        ),
        
        "software_architect": AgentConfig(
            name="software_architect",
            type="software_dev",
            description="Software architect for system design and planning",
            capabilities=["system_design", "architecture_planning", "scalability"],
            mcp_servers=["memory", "filesystem"],
            memory_store="architect_memory",
            system_prompt="""You are a software architect focused on:
- High-level system design and architecture
- Scalability and performance considerations
- Technology stack selection and integration
- Design patterns and architectural principles
- Long-term technical strategy and planning""",
            tools=["design", "documentation", "analysis"]
        ),
        
        "python_expert": AgentConfig(
            name="python_expert",
            type="software_dev", 
            description="Python development expert and specialist",
            capabilities=["python_dev", "async_programming", "performance_optimization"],
            mcp_servers=["memory", "filesystem"],
            memory_store="python_memory",
            system_prompt="""You are a Python expert specializing in:
- Advanced Python programming and best practices
- Asynchronous programming with asyncio
- Performance optimization and profiling
- Python ecosystem and library selection
- Code quality, testing, and debugging""",
            tools=["coding", "testing", "debugging", "optimization"]
        )
    }
    
    return SystemConfig(
        mcp_servers=mcp_servers,
        agents=agents
    )