"""
Custom AugmentedLLM implementation that bridges mcp-agent workflows with Claude CLI execution engine.
This allows mcp-agent workflow patterns to work with our existing execution infrastructure.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel

from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_anthropic import (
    RequestParams, 
    MCPMessageParam, 
    MCPMessageResult,
    RequestCompletionRequest,
    AnthropicSettings
)

# Import our execution engine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Agent, Task, TaskStatus
from services.execution_engine import ExecutionEngine
from schemas import TaskExecutionRequest


class ClaudeCliAugmentedLLM(AugmentedLLM):
    """
    Custom AugmentedLLM that delegates execution to our Claude CLI execution engine
    instead of calling LLM APIs directly. This bridges mcp-agent workflows with
    our existing execution infrastructure.
    """
    
    def __init__(self, name: str = "claude_cli_llm", config: AnthropicSettings = None, agent_id: str = None, task_id: str = None, db_session=None, work_directory: str = None):
        super().__init__(name=name)
        self.config = config or AnthropicSettings(api_key="dummy", default_model="claude-3-sonnet-20240229")
        self.agent_id = agent_id
        self.task_id = task_id
        self.db_session = db_session
        self.work_directory = work_directory
        self.execution_engine = ExecutionEngine()
        
    async def generate(
        self,
        messages: List[MCPMessageParam],
        request_params: Optional[RequestParams] = None,
        **kwargs
    ) -> List[MCPMessageResult]:
        """
        Generate response using Claude CLI execution engine instead of direct LLM calls.
        """
        try:
            # Extract the main prompt/message from mcp-agent format
            prompt = self._extract_prompt_from_messages(messages)
            
            # If we have agent_id and task_id, execute via our execution engine
            if self.agent_id and self.task_id and self.db_session:
                result = await self._execute_via_engine(prompt)
            else:
                # For router/orchestrator use: return simple response
                result = self._generate_router_response(prompt)
            
            # Return in mcp-agent expected format
            return [MCPMessageResult(
                role="assistant",
                content=result,
                tool_calls=[]
            )]
            
        except Exception as e:
            error_msg = f"Claude CLI execution failed: {str(e)}"
            return [MCPMessageResult(
                role="assistant", 
                content=error_msg,
                tool_calls=[]
            )]
    
    async def generate_str(
        self,
        message: str,
        request_params: Optional[RequestParams] = None,
        **kwargs
    ) -> str:
        """
        Generate string response using Claude CLI execution engine.
        """
        try:
            if self.agent_id and self.task_id and self.db_session:
                result = await self._execute_via_engine(message)
                return result
            else:
                # For router/orchestrator use: return simple routing decision
                return self._generate_router_response(message)
                
        except Exception as e:
            return f"Execution failed: {str(e)}"
    
    async def generate_structured(
        self,
        message: str,
        response_model: type[BaseModel],
        request_params: Optional[RequestParams] = None,
        **kwargs
    ) -> BaseModel:
        """
        Generate structured response using Claude CLI execution engine.
        """
        try:
            result_str = await self.generate_str(message, request_params, **kwargs)
            
            # For router responses, create proper structured output
            if hasattr(response_model, 'model_fields') and 'agent_id' in str(response_model.model_fields):
                # This is likely a router response model
                return self._create_router_structured_response(result_str, response_model)
            
            # Try to parse as JSON and create the response model
            try:
                result_dict = json.loads(result_str) if result_str.startswith('{') else {"result": result_str}
                return response_model(**result_dict)
            except:
                # Fallback: create model with result string
                return response_model(result=result_str)
                
        except Exception as e:
            # Return error in structured format using our robust method
            return self._create_router_structured_response(f"Error: {str(e)}", response_model)
    
    def _extract_prompt_from_messages(self, messages: List[MCPMessageParam]) -> str:
        """Extract the main prompt/content from mcp-agent message format."""
        prompt_parts = []
        
        for message in messages:
            if hasattr(message, 'content'):
                if isinstance(message.content, str):
                    prompt_parts.append(message.content)
                elif isinstance(message.content, list):
                    for content_part in message.content:
                        if hasattr(content_part, 'text'):
                            prompt_parts.append(content_part.text)
                        elif isinstance(content_part, str):
                            prompt_parts.append(content_part)
        
        return "\n".join(prompt_parts) if prompt_parts else "No content found"
    
    def _generate_router_response(self, prompt: str) -> str:
        """Generate a simple router response without calling actual LLM APIs."""
        # For routing decisions, provide a simple response
        if "route" in prompt.lower() or "routing" in prompt.lower():
            return f"Routing decision for: {prompt[:100]}... -> Selected primary agent"
        
        # For general orchestration
        return f"Processed orchestration request: {prompt[:100]}..."
    
    def _create_router_structured_response(self, result_str: str, response_model: type[BaseModel]) -> BaseModel:
        """Create structured router response."""
        try:
            # For router models, we need to match the expected structure
            if hasattr(response_model, 'model_fields'):
                fields = response_model.model_fields
                field_names = list(fields.keys())
                
                # Check for common router response patterns
                if 'categories' in field_names:
                    # This is likely a StructuredResponse with categories
                    return response_model(
                        categories=[{
                            "category": "primary_agent",
                            "confidence": 0.8,
                            "reasoning": result_str[:100]
                        }]
                    )
                elif 'agent_id' in field_names:
                    # Return the first available agent ID (simple routing)
                    return response_model(
                        agent_id=self.agent_id or "default_agent",
                        confidence=0.8,
                        reasoning=result_str
                    )
                elif 'selected_agent' in field_names:
                    return response_model(
                        selected_agent=self.agent_id or "default_agent",
                        confidence=0.8
                    )
                elif 'result' in field_names:
                    return response_model(result=result_str)
                else:
                    # Try to populate all required fields with reasonable defaults
                    init_data = {}
                    for field_name, field_info in fields.items():
                        if field_info.is_required():
                            if 'list' in str(field_info.annotation):
                                init_data[field_name] = []
                            elif 'str' in str(field_info.annotation):
                                init_data[field_name] = result_str[:100]
                            elif 'float' in str(field_info.annotation):
                                init_data[field_name] = 0.8
                            elif 'int' in str(field_info.annotation):
                                init_data[field_name] = 1
                            else:
                                init_data[field_name] = None
                    
                    return response_model(**init_data)
            
            # Fallback to basic structure
            return response_model(result=result_str)
            
        except Exception as e:
            # Last resort: try to create minimal valid response
            try:
                if hasattr(response_model, 'model_fields'):
                    fields = response_model.model_fields
                    init_data = {}
                    for field_name, field_info in fields.items():
                        if field_info.is_required():
                            if field_name == 'categories':
                                init_data[field_name] = []
                            elif 'str' in str(field_info.annotation):
                                init_data[field_name] = f"Error: {str(e)}"
                            else:
                                init_data[field_name] = None
                    return response_model(**init_data)
                else:
                    return response_model()
            except:
                # Ultimate fallback - this shouldn't happen but just in case
                raise ValueError(f"Could not create response model {response_model}: {str(e)}")
    
    async def _execute_via_engine(self, prompt: str) -> str:
        """Execute the prompt using our Claude CLI execution engine."""
        try:
            # Get agent and task
            agent = self.db_session.query(Agent).filter(Agent.id == self.agent_id).first()
            task = self.db_session.query(Task).filter(Task.id == self.task_id).first()
            
            if not agent or not task:
                return f"Agent or task not found. Agent: {self.agent_id}, Task: {self.task_id}"
            
            # Create execution request
            execution_request = TaskExecutionRequest(
                task_id=self.task_id,
                agent_ids=[self.agent_id],
                work_directory=self.work_directory
            )
            
            # Execute via our execution engine
            response = await self.execution_engine.start_task_execution(self.db_session, execution_request)
            
            # Wait for execution to complete and get results
            execution_id = response.execution_id
            max_wait = 300  # 5 minutes max
            wait_time = 0
            
            while wait_time < max_wait:
                from models import Execution as ExecutionModel
                execution = self.db_session.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
                if execution and execution.status in ["completed", "failed", "cancelled"]:
                    if execution.status == "completed":
                        # Return the execution output/results
                        if execution.output:
                            return json.dumps(execution.output) if isinstance(execution.output, dict) else str(execution.output)
                        else:
                            return "Task completed successfully"
                    else:
                        return f"Task execution {execution.status}: {execution.logs[-1].get('message', '') if execution.logs else 'No details'}"
                
                await asyncio.sleep(5)
                wait_time += 5
            
            return "Task execution timed out after 5 minutes"
            
        except Exception as e:
            return f"Execution engine error: {str(e)}"


def create_claude_cli_llm(agent_id: str = None, task_id: str = None, db_session=None, name: str = None, work_directory: str = None) -> ClaudeCliAugmentedLLM:
    """Factory function to create Claude CLI LLM instances."""
    llm_name = name or f"claude_cli_{agent_id[:8] if agent_id else 'default'}"
    
    # Create basic config
    config = AnthropicSettings(
        api_key="dummy-key-for-claude-cli",
        default_model="claude-3-sonnet-20240229"
    )
    
    return ClaudeCliAugmentedLLM(
        name=llm_name, 
        config=config,
        agent_id=agent_id, 
        task_id=task_id, 
        db_session=db_session,
        work_directory=work_directory
    )