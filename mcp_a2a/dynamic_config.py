"""
Dynamic configuration system for flexible multi-agent scenarios.
Allows user to configure number of agents, tasks, and objectives at runtime.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
import json
import uuid
from pathlib import Path

from .config import AgentConfig, SystemConfig, MCPServerConfig


@dataclass
class ConversationRound:
    """Single round in multi-agent conversation."""
    round_number: int
    initiating_agent: str
    target_agent: str
    message: str
    response: Optional[str] = None
    task_data: Optional[Dict[str, Any]] = None


@dataclass
class MultiAgentScenario:
    """Configuration for a multi-agent test scenario."""
    scenario_id: str
    name: str
    description: str
    objective: str
    agents: List[str]  # Agent names to use
    conversation_rounds: int
    initial_task: Dict[str, Any]
    conversation_plan: List[ConversationRound]


class DynamicConfigBuilder:
    """Builder for creating dynamic multi-agent configurations."""
    
    def __init__(self, base_config: SystemConfig):
        self.base_config = base_config
        self.scenarios: Dict[str, MultiAgentScenario] = {}
        
    def create_scenario(self, 
                       name: str,
                       description: str, 
                       objective: str,
                       agent_types: List[str],
                       conversation_rounds: int = 3) -> str:
        """Create a new multi-agent scenario."""
        
        scenario_id = str(uuid.uuid4())
        
        # Validate agent types exist in base config
        available_agents = list(self.base_config.agents.keys())
        for agent_type in agent_types:
            if agent_type not in available_agents:
                raise ValueError(f"Agent type '{agent_type}' not found in configuration. Available: {available_agents}")
        
        # Create initial task
        initial_task = {
            "id": f"scenario_{scenario_id}_init",
            "type": "coordination",
            "description": f"Initialize multi-agent scenario: {objective}",
            "objective": objective,
            "participating_agents": agent_types,
            "rounds_planned": conversation_rounds
        }
        
        # Plan conversation rounds
        conversation_plan = self._plan_conversation_rounds(
            agent_types, conversation_rounds, objective
        )
        
        scenario = MultiAgentScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            objective=objective,
            agents=agent_types,
            conversation_rounds=conversation_rounds,
            initial_task=initial_task,
            conversation_plan=conversation_plan
        )
        
        self.scenarios[scenario_id] = scenario
        return scenario_id
    
    def _plan_conversation_rounds(self, 
                                 agents: List[str], 
                                 rounds: int,
                                 objective: str) -> List[ConversationRound]:
        """Plan the conversation flow between agents."""
        
        conversation_plan = []
        
        for round_num in range(1, rounds + 1):
            # Rotate between agents for dynamic conversation
            initiating_idx = (round_num - 1) % len(agents)
            target_idx = (round_num) % len(agents)
            
            initiating_agent = agents[initiating_idx] 
            target_agent = agents[target_idx]
            
            # Create round-specific messages based on objective
            if round_num == 1:
                message = f"Round {round_num}: Let's discuss the objective '{objective}'. What are your initial thoughts and approach?"
            elif round_num == rounds:
                message = f"Round {round_num}: Based on our previous discussion, let's finalize our approach to '{objective}'. What are your conclusions?"
            else:
                message = f"Round {round_num}: Building on our discussion about '{objective}', what additional insights or refinements do you propose?"
            
            conversation_round = ConversationRound(
                round_number=round_num,
                initiating_agent=initiating_agent,
                target_agent=target_agent,
                message=message,
                task_data={
                    "type": "discussion",
                    "round": round_num,
                    "objective": objective,
                    "context": f"Multi-agent conversation round {round_num} of {rounds}"
                }
            )
            
            conversation_plan.append(conversation_round)
        
        return conversation_plan
    
    def get_scenario(self, scenario_id: str) -> Optional[MultiAgentScenario]:
        """Get scenario by ID."""
        return self.scenarios.get(scenario_id)
    
    def list_scenarios(self) -> List[MultiAgentScenario]:
        """List all configured scenarios."""
        return list(self.scenarios.values())
    
    def create_runtime_config(self, scenario_id: str) -> SystemConfig:
        """Create runtime configuration for specific scenario."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Create filtered config with only needed agents
        runtime_agents = {}
        for agent_name in scenario.agents:
            if agent_name in self.base_config.agents:
                runtime_agents[agent_name] = self.base_config.agents[agent_name]
        
        # Always include orchestrator
        if "orchestrator" not in runtime_agents and "orchestrator" in self.base_config.agents:
            runtime_agents["orchestrator"] = self.base_config.agents["orchestrator"]
        
        runtime_config = SystemConfig(
            name=f"Runtime Config - {scenario.name}",
            base_path=self.base_config.base_path,
            memory_path=self.base_config.memory_path,
            mcp_servers=self.base_config.mcp_servers,
            agents=runtime_agents,
            orchestrator_agent=self.base_config.orchestrator_agent,
            max_concurrent_tasks=len(scenario.agents) + 2,  # +2 for orchestrator and buffer
            task_timeout=self.base_config.task_timeout
        )
        
        return runtime_config
    
    def save_scenario(self, scenario_id: str, file_path: Path) -> None:
        """Save scenario to JSON file."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario_data = {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "description": scenario.description,
            "objective": scenario.objective,
            "agents": scenario.agents,
            "conversation_rounds": scenario.conversation_rounds,
            "initial_task": scenario.initial_task,
            "conversation_plan": [
                {
                    "round_number": round.round_number,
                    "initiating_agent": round.initiating_agent,
                    "target_agent": round.target_agent,
                    "message": round.message,
                    "task_data": round.task_data
                }
                for round in scenario.conversation_plan
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(scenario_data, f, indent=2)
    
    def load_scenario(self, file_path: Path) -> str:
        """Load scenario from JSON file."""
        with open(file_path, 'r') as f:
            scenario_data = json.load(f)
        
        conversation_plan = [
            ConversationRound(
                round_number=round_data["round_number"],
                initiating_agent=round_data["initiating_agent"],
                target_agent=round_data["target_agent"],
                message=round_data["message"],
                task_data=round_data.get("task_data")
            )
            for round_data in scenario_data["conversation_plan"]
        ]
        
        scenario = MultiAgentScenario(
            scenario_id=scenario_data["scenario_id"],
            name=scenario_data["name"],
            description=scenario_data["description"],
            objective=scenario_data["objective"],
            agents=scenario_data["agents"],
            conversation_rounds=scenario_data["conversation_rounds"],
            initial_task=scenario_data["initial_task"],
            conversation_plan=conversation_plan
        )
        
        self.scenarios[scenario.scenario_id] = scenario
        return scenario.scenario_id


# Predefined scenario templates
def create_two_agent_research_scenario(config_builder: DynamicConfigBuilder) -> str:
    """Create a 2-agent research collaboration scenario."""
    return config_builder.create_scenario(
        name="Two-Agent Research Collaboration",
        description="Active inference expert and mechanistic interpretability expert collaborate on research",
        objective="Develop a research proposal combining active inference and mechanistic interpretability for understanding LLM behavior",
        agent_types=["active_inference_expert", "mechanistic_interpretability_expert"],
        conversation_rounds=3
    )


def create_two_agent_development_scenario(config_builder: DynamicConfigBuilder) -> str:
    """Create a 2-agent software development scenario."""
    return config_builder.create_scenario(
        name="Two-Agent Development Collaboration", 
        description="Software architect and python expert collaborate on system design",
        objective="Design and plan implementation of a distributed task processing system with async capabilities",
        agent_types=["software_architect", "python_expert"],
        conversation_rounds=3
    )


def create_custom_scenario(config_builder: DynamicConfigBuilder,
                          name: str,
                          description: str,
                          objective: str,
                          agent_types: List[str],
                          rounds: int = 3) -> str:
    """Create a custom user-defined scenario."""
    return config_builder.create_scenario(
        name=name,
        description=description,
        objective=objective,
        agent_types=agent_types,
        conversation_rounds=rounds
    )