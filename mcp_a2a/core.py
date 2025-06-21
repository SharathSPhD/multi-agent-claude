"""
Core agent implementations using mcp-agent framework.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import structlog
from dataclasses import dataclass

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

from .config import AgentConfig, SystemConfig, MCPServerConfig
from .memory import AgentMemory
from .sdk_agent import SDKAgentWrapper, SDKTaskResult

logger = structlog.get_logger(__name__)


@dataclass
class TaskResult:
    """Result of an agent task execution."""
    task_id: str
    agent_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class MCPAgent:
    """
    Enhanced MCP Agent with memory and simplified coordination.
    """
    
    def __init__(self, config: AgentConfig, system_config: SystemConfig):
        self.config = config
        self.system_config = system_config
        self.agent_id = str(uuid.uuid4())
        self.memory = AgentMemory(config.memory_store)
        self.mcp_app: Optional[MCPApp] = None
        self.agent: Optional[Agent] = None
        self.sdk_wrapper: Optional[SDKAgentWrapper] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logger.bind(agent=config.name)
        
    async def initialize(self):
        """Initialize the agent with MCP servers and memory."""
        try:
            # Initialize memory store
            await self.memory.initialize()
            
            # Initialize MCP app
            self.mcp_app = MCPApp(name=f"{self.config.name}_app")
            
            # Create agent with proper server names from config
            self.agent = Agent(
                name=self.config.name,
                instruction=self.config.system_prompt,
                server_names=self.config.mcp_servers
            )
            
            # Initialize SDK wrapper for autonomous execution
            work_dir = Path(self.system_config.base_path)
            self.sdk_wrapper = SDKAgentWrapper(self.config, work_dir)
            await self.sdk_wrapper.initialize()
            
            # Agent initialization complete
            
            self.logger.info("Agent initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize agent", error=str(e))
            raise
    
    async def _add_mcp_server(self, server_config: MCPServerConfig):
        """Add MCP server to the agent."""
        if not self.mcp_app:
            return
            
        # This would use mcp-agent's server connection mechanism
        # Implementation depends on mcp-agent API
        self.logger.info(f"Adding MCP server: {server_config.name}")
    
    def _create_llm(self):
        """Create LLM instance for the agent."""
        # Create LLM based on provider configuration
        if self.config.llm_provider == "openai":
            return OpenAIAugmentedLLM(
                model=self.config.llm_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
        elif self.config.llm_provider == "anthropic":
            return AnthropicAugmentedLLM(
                model=self.config.llm_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a task asynchronously."""
        task_id = task.get("id", str(uuid.uuid4()))
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info("Starting task execution", task_id=task_id)
            
            # Store task in memory
            await self.memory.store_task(task_id, task)
            
            # Execute via SDK wrapper with seamless mcp-agent integration
            if self.sdk_wrapper:
                sdk_result = await self.sdk_wrapper.execute_autonomous_task(task)
                result = sdk_result.output
                
                if not sdk_result.success:
                    raise Exception(sdk_result.error or "SDK execution failed")
            else:
                raise Exception("SDK wrapper not initialized - seamless integration required")
            
            # Store result in memory
            await self.memory.store_result(task_id, result)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            self.logger.info("Task completed successfully", 
                           task_id=task_id, 
                           execution_time=execution_time)
            
            return TaskResult(
                task_id=task_id,
                agent_name=self.config.name,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = str(e)
            
            self.logger.error("Task execution failed", 
                            task_id=task_id, 
                            error=error_msg,
                            execution_time=execution_time)
            
            return TaskResult(
                task_id=task_id,
                agent_name=self.config.name,
                success=False,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _execute_code_task(self, task: Dict[str, Any]) -> Any:
        """Execute coding-related tasks."""
        async with self.mcp_app.run() as mcp_agent_app:
            async with self.agent:
                llm = await self.agent.attach_llm(self._create_llm())
                prompt = f"Execute this coding task: {task['description']}\nCode: {task.get('code', '')}"
                response = await llm.generate_str(message=prompt)
                return response
    
    async def _execute_research_task(self, task: Dict[str, Any]) -> Any:
        """Execute research-related tasks."""
        async with self.mcp_app.run() as mcp_agent_app:
            async with self.agent:
                llm = await self.agent.attach_llm(self._create_llm())
                prompt = f"Research task: {task['description']}\nQuery: {task.get('query', '')}"
                response = await llm.generate_str(message=prompt)
                return response
    
    async def _execute_analysis_task(self, task: Dict[str, Any]) -> Any:
        """Execute analysis-related tasks."""
        async with self.mcp_app.run() as mcp_agent_app:
            async with self.agent:
                llm = await self.agent.attach_llm(self._create_llm())
                prompt = f"Analysis task: {task['description']}\nData: {task.get('data', '')}"
                response = await llm.generate_str(message=prompt)
                return response
    
    async def _execute_general_task(self, task: Dict[str, Any]) -> Any:
        """Execute general tasks."""
        async with self.mcp_app.run() as mcp_agent_app:
            async with self.agent:
                llm = await self.agent.attach_llm(self._create_llm())
                prompt = f"General task: {task['description']}"
                response = await llm.generate_str(message=prompt)
                return response
    
    async def communicate_with_agent(self, target_agent: str, message: str) -> str:
        """Communicate with another agent via memory store."""
        # Store message in memory for target agent to retrieve
        message_data = {
            "from": self.config.name,
            "to": target_agent,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.memory.store_conversation(f"message_to_{target_agent}", message_data)
        self.logger.info(f"Message stored for {target_agent}")
        return f"Message sent to {target_agent}: {message}"
    
    async def shutdown(self):
        """Shutdown the agent and cleanup resources."""
        try:
            # Cancel running tasks
            for task_id, task in self.running_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Cleanup communication resources
            # No A2A client to disconnect
            
            # Cleanup MCP app
            if self.mcp_app:
                # MCP app cleanup would go here
                pass
                
            self.logger.info("Agent shutdown completed")
            
        except Exception as e:
            self.logger.error("Error during agent shutdown", error=str(e))


# A2AAgent removed - using simplified coordination instead


class Orchestrator:
    """
    Central orchestrator for managing multiple agents and workflows.
    """
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.agents: Dict[str, MCPAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[str, TaskResult] = {}
        self.logger = logger.bind(component="orchestrator")
        self.mcp_app: Optional[MCPApp] = None
        
    async def initialize(self):
        """Initialize orchestrator and all agents."""
        try:
            # Initialize MCP app for orchestrator
            self.mcp_app = MCPApp(name="orchestrator_app")
            
            # Initialize all agents
            for agent_name, agent_config in self.config.agents.items():
                if agent_config.enabled:
                    agent = MCPAgent(agent_config, self.config)
                    await agent.initialize()
                    self.agents[agent_name] = agent
                    
            self.logger.info(f"Orchestrator initialized with {len(self.agents)} agents")
            
        except Exception as e:
            self.logger.error("Failed to initialize orchestrator", error=str(e))
            raise
    
    def _create_planning_llm(self):
        """Create LLM for planning tasks."""
        return AnthropicAugmentedLLM(
            model="claude-3-5-sonnet-20241022"
        )
    
    async def submit_task(self, task: Dict[str, Any]) -> str:
        """Submit a task for execution."""
        task_id = task.get("id", str(uuid.uuid4()))
        task["id"] = task_id
        
        await self.task_queue.put(task)
        self.logger.info("Task submitted", task_id=task_id)
        
        return task_id
    
    async def execute_workflow(self, workflow: Dict[str, Any]) -> Dict[str, TaskResult]:
        """Execute a complete workflow with multiple tasks."""
        workflow_id = workflow.get("id", str(uuid.uuid4()))
        tasks = workflow.get("tasks", [])
        
        self.logger.info("Starting workflow execution", 
                        workflow_id=workflow_id, 
                        task_count=len(tasks))
        
        results = {}
        
        try:
            # Execute tasks sequentially based on dependencies
            for task in tasks:
                agent_name = task.get("agent", "orchestrator")
                agent = self.agents.get(agent_name)
                
                if agent:
                    result = await agent.execute_task(task)
                    results[task["id"]] = result
                else:
                    self.logger.warning(f"Agent not found: {agent_name}")
                        
        except Exception as e:
            self.logger.error("Workflow execution failed", 
                            workflow_id=workflow_id, 
                            error=str(e))
        
        return results
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a specific task."""
        return self.results.get(task_id)
    
    async def shutdown(self):
        """Shutdown orchestrator and all agents."""
        try:
            for agent in self.agents.values():
                await agent.shutdown()
                
            self.logger.info("Orchestrator shutdown completed")
            
        except Exception as e:
            self.logger.error("Error during orchestrator shutdown", error=str(e))