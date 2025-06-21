"""
Multi-turn conversation engine for coordinated agent interactions.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
import json

from .core import MCPAgent, Orchestrator, TaskResult
from .config import SystemConfig
from .dynamic_config import MultiAgentScenario, ConversationRound, DynamicConfigBuilder

logger = structlog.get_logger(__name__)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    turn_id: str
    round_number: int
    initiating_agent: str
    target_agent: str
    message: str
    response: str
    task_result: Optional[TaskResult] = None
    timestamp: float = 0.0


@dataclass
class ConversationSession:
    """Complete conversation session between agents."""
    session_id: str
    scenario: MultiAgentScenario
    turns: List[ConversationTurn]
    orchestrator_summary: Optional[str] = None
    status: str = "active"  # active, completed, failed


class ConversationEngine:
    """Engine for managing multi-turn conversations between agents."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.orchestrator: Optional[Orchestrator] = None
        self.active_agents: Dict[str, MCPAgent] = {}
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.logger = logger.bind(component="conversation_engine")
        
    async def initialize(self) -> None:
        """Initialize conversation engine."""
        try:
            # Initialize orchestrator
            self.orchestrator = Orchestrator(self.config)
            await self.orchestrator.initialize()
            
            # Initialize configured agents
            for agent_name, agent_config in self.config.agents.items():
                if agent_config.enabled and agent_name != "orchestrator":
                    agent = MCPAgent(agent_config, self.config)
                    await agent.initialize()
                    self.active_agents[agent_name] = agent
                    
            self.logger.info("Conversation engine initialized", 
                           orchestrator=bool(self.orchestrator),
                           active_agents=len(self.active_agents))
                           
        except Exception as e:
            self.logger.error("Failed to initialize conversation engine", error=str(e))
            raise
    
    async def start_conversation(self, scenario: MultiAgentScenario) -> str:
        """Start a new multi-agent conversation."""
        session_id = str(uuid.uuid4())
        
        # Validate scenario agents are available
        missing_agents = []
        for agent_name in scenario.agents:
            if agent_name not in self.active_agents:
                missing_agents.append(agent_name)
        
        if missing_agents:
            raise ValueError(f"Missing agents for scenario: {missing_agents}")
        
        # Create conversation session
        session = ConversationSession(
            session_id=session_id,
            scenario=scenario,
            turns=[],
            status="active"
        )
        
        self.active_sessions[session_id] = session
        
        self.logger.info("Started conversation session", 
                        session_id=session_id,
                        scenario=scenario.name,
                        agents=scenario.agents,
                        rounds=scenario.conversation_rounds)
        
        return session_id
    
    async def execute_conversation_round(self, session_id: str, round_number: int) -> ConversationTurn:
        """Execute a single conversation round."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get conversation round plan
        round_plan = None
        for plan_round in session.scenario.conversation_plan:
            if plan_round.round_number == round_number:
                round_plan = plan_round
                break
        
        if not round_plan:
            raise ValueError(f"Round {round_number} not found in conversation plan")
        
        self.logger.info("Executing conversation round",
                        session_id=session_id,
                        round_number=round_number,
                        initiating_agent=round_plan.initiating_agent,
                        target_agent=round_plan.target_agent)
        
        # Execute the conversation turn
        turn = await self._execute_conversation_turn(session, round_plan)
        
        # Add turn to session
        session.turns.append(turn)
        
        return turn
    
    async def _execute_conversation_turn(self, session: ConversationSession, round_plan: ConversationRound) -> ConversationTurn:
        """Execute a single conversation turn."""
        turn_id = str(uuid.uuid4())
        start_time = asyncio.get_event_loop().time()
        
        # Get initiating agent
        initiating_agent = self.active_agents.get(round_plan.initiating_agent)
        if not initiating_agent:
            raise ValueError(f"Initiating agent {round_plan.initiating_agent} not found")
        
        # Get target agent  
        target_agent = self.active_agents.get(round_plan.target_agent)
        if not target_agent:
            raise ValueError(f"Target agent {round_plan.target_agent} not found")
        
        # Create task for target agent
        conversation_task = {
            "id": f"conversation_{turn_id}",
            "type": "conversation",
            "description": round_plan.message,
            "context": f"Conversation round {round_plan.round_number} of {session.scenario.conversation_rounds}",
            "objective": session.scenario.objective,
            "initiating_agent": round_plan.initiating_agent,
            "conversation_history": self._get_conversation_history(session),
            "round": round_plan.round_number
        }
        
        # Add task data if available
        if round_plan.task_data:
            conversation_task.update(round_plan.task_data)
        
        # Execute task on target agent
        self.logger.info("Executing conversation task",
                        turn_id=turn_id,
                        target_agent=round_plan.target_agent,
                        task_type=conversation_task["type"])
        
        task_result = await target_agent.execute_task(conversation_task)
        
        # Store conversation turn in agent memories
        await self._store_conversation_turn(initiating_agent, target_agent, round_plan, task_result)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        turn = ConversationTurn(
            turn_id=turn_id,
            round_number=round_plan.round_number,
            initiating_agent=round_plan.initiating_agent,
            target_agent=round_plan.target_agent,
            message=round_plan.message,
            response=str(task_result.result) if task_result.result else "No response",
            task_result=task_result,
            timestamp=execution_time
        )
        
        self.logger.info("Conversation turn completed",
                        turn_id=turn_id,
                        success=task_result.success,
                        execution_time=execution_time)
        
        return turn
    
    async def _store_conversation_turn(self, initiating_agent: MCPAgent, target_agent: MCPAgent, 
                                     round_plan: ConversationRound, task_result: TaskResult) -> None:
        """Store conversation turn in agent memories."""
        conversation_data = {
            "round": round_plan.round_number,
            "initiating_agent": round_plan.initiating_agent,
            "target_agent": round_plan.target_agent,
            "message": round_plan.message,
            "response": str(task_result.result) if task_result.result else "",
            "success": task_result.success,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store in both agents' memories
        await initiating_agent.memory.store_conversation(
            f"conversation_round_{round_plan.round_number}_initiated", 
            conversation_data
        )
        
        await target_agent.memory.store_conversation(
            f"conversation_round_{round_plan.round_number}_received",
            conversation_data
        )
    
    def _get_conversation_history(self, session: ConversationSession) -> List[Dict[str, Any]]:
        """Get conversation history for context."""
        history = []
        for turn in session.turns:
            history.append({
                "round": turn.round_number,
                "initiating_agent": turn.initiating_agent,
                "target_agent": turn.target_agent,
                "message": turn.message,
                "response": turn.response
            })
        return history
    
    async def complete_conversation(self, session_id: str) -> ConversationSession:
        """Complete a conversation session."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Execute all planned conversation rounds
        for round_num in range(1, session.scenario.conversation_rounds + 1):
            if not any(turn.round_number == round_num for turn in session.turns):
                await self.execute_conversation_round(session_id, round_num)
        
        # Generate orchestrator summary
        if self.orchestrator:
            summary_task = {
                "id": f"summary_{session_id}",
                "type": "summary",
                "description": f"Summarize the conversation between {', '.join(session.scenario.agents)} about: {session.scenario.objective}",
                "conversation_turns": [asdict(turn) for turn in session.turns],
                "objective": session.scenario.objective
            }
            
            summary_result = await self.orchestrator.submit_task(summary_task)
            # Note: In real implementation, would wait for and retrieve result
            session.orchestrator_summary = f"Summary task submitted: {summary_result}"
        
        session.status = "completed"
        
        self.logger.info("Conversation completed",
                        session_id=session_id,
                        total_turns=len(session.turns),
                        scenario=session.scenario.name)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID."""
        return self.active_sessions.get(session_id)
    
    async def save_session(self, session_id: str, file_path: Path) -> None:
        """Save conversation session to file."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = {
            "session_id": session.session_id,
            "scenario": asdict(session.scenario),
            "turns": [asdict(turn) for turn in session.turns],
            "orchestrator_summary": session.orchestrator_summary,
            "status": session.status
        }
        
        with open(file_path, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
    
    async def shutdown(self) -> None:
        """Shutdown conversation engine."""
        try:
            # Shutdown all active agents
            for agent in self.active_agents.values():
                await agent.shutdown()
            
            # Shutdown orchestrator
            if self.orchestrator:
                await self.orchestrator.shutdown()
                
            self.logger.info("Conversation engine shutdown completed")
            
        except Exception as e:
            self.logger.error("Error during conversation engine shutdown", error=str(e))