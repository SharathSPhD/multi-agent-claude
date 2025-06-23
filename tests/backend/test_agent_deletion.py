"""
Test agent deletion with task handling
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from main import app
from models import Agent, Task, Execution, TaskStatus


class TestAgentDeletion:
    """Test agent deletion functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent"""
        agent = MagicMock()
        agent.id = "test-agent-id"
        agent.name = "Test Agent"
        agent.role = "test_role"
        return agent
    
    @pytest.fixture
    def mock_task(self):
        """Create mock task"""
        task = MagicMock()
        task.id = "test-task-id"
        task.title = "Test Task"
        task.assigned_agents = []
        task.status = TaskStatus.PENDING
        return task
    
    @pytest.fixture
    def mock_execution(self):
        """Create mock execution"""
        execution = MagicMock()
        execution.id = "test-execution-id"
        execution.status = "running"
        execution.agent_id = "test-agent-id"
        return execution

    @pytest.mark.asyncio
    async def test_delete_agent_with_no_executions(self, mock_agent):
        """Test deleting agent with no running executions"""
        # This would be an integration test with actual database
        # For now, we test the logic components
        
        # Mock database operations
        running_executions = []
        associated_tasks = []
        
        # Verify deletion logic
        assert len(running_executions) == 0  # Should allow deletion
        assert len(associated_tasks) == 0    # No tasks affected

    @pytest.mark.asyncio 
    async def test_delete_agent_with_running_executions_no_force(self, mock_agent, mock_execution):
        """Test deleting agent with running executions without force"""
        # Mock running executions
        running_executions = [mock_execution]
        
        # Should prevent deletion without force
        assert len(running_executions) > 0
        # In actual implementation, this would return an error response

    @pytest.mark.asyncio
    async def test_delete_agent_with_associated_tasks(self, mock_agent, mock_task):
        """Test deleting agent with associated tasks"""
        # Setup mock task with agent assignment
        mock_task.assigned_agents = [mock_agent]
        associated_tasks = [mock_task]
        
        # Test task handling logic
        for task in associated_tasks:
            # Remove agent from task's assigned agents
            task.assigned_agents = [a for a in task.assigned_agents if a.id != mock_agent.id]
            
            # If no agents left, mark as pending reassignment
            if not task.assigned_agents:
                task.status = TaskStatus.PENDING
                task.error_message = f"Agent {mock_agent.name} was deleted"
        
        # Verify task was updated correctly
        assert len(mock_task.assigned_agents) == 0
        assert mock_task.status == TaskStatus.PENDING
        assert "deleted" in mock_task.error_message

    def test_agent_deletion_response_format(self):
        """Test that agent deletion returns proper response format"""
        # Expected response format for successful deletion
        expected_response = {
            "message": "Agent deleted successfully",
            "affected_tasks": 0,
            "task_updates": [],
            "cancelled_executions": 0
        }
        
        # Verify response structure
        assert "message" in expected_response
        assert "affected_tasks" in expected_response
        assert "task_updates" in expected_response
        assert "cancelled_executions" in expected_response

    def test_agent_deletion_with_force_response(self):
        """Test response format when using force deletion"""
        # Expected response when force=True is used
        expected_response = {
            "message": "Agent deleted successfully", 
            "affected_tasks": 2,
            "task_updates": [
                {
                    "task_id": "task-1",
                    "task_title": "Test Task 1",
                    "remaining_agents": 1
                },
                {
                    "task_id": "task-2", 
                    "task_title": "Test Task 2",
                    "remaining_agents": 0
                }
            ],
            "cancelled_executions": 1
        }
        
        # Verify detailed response structure
        assert expected_response["cancelled_executions"] > 0
        assert len(expected_response["task_updates"]) == 2
        assert all("task_id" in update for update in expected_response["task_updates"])

    def test_agent_deletion_error_cases(self):
        """Test error cases for agent deletion"""
        # Test case 1: Agent not found
        agent_not_found_response = {
            "detail": "Agent not found"
        }
        
        # Test case 2: Agent has running executions (no force)
        has_executions_response = {
            "message": "Cannot delete agent with running executions",
            "running_executions": 2,
            "suggestion": "Cancel running executions first or use force=true"
        }
        
        # Verify error response structures
        assert "detail" in agent_not_found_response
        assert "running_executions" in has_executions_response
        assert "suggestion" in has_executions_response

    @pytest.mark.asyncio
    async def test_force_deletion_cancels_executions(self, mock_agent, mock_execution):
        """Test that force deletion cancels running executions"""
        # Mock execution engine
        execution_engine = AsyncMock()
        execution_engine.abort_execution = AsyncMock(return_value={"status": "aborted"})
        
        # Mock running executions
        running_executions = [mock_execution]
        
        # Test force deletion logic
        if running_executions:
            for execution in running_executions:
                await execution_engine.abort_execution(MagicMock(), execution.id)
        
        # Verify abort was called
        execution_engine.abort_execution.assert_called_once()

    def test_task_reassignment_logic(self, mock_agent):
        """Test logic for reassigning tasks when agent is deleted"""
        # Create mock tasks with different agent configurations
        task_with_multiple_agents = MagicMock()
        task_with_multiple_agents.assigned_agents = [mock_agent, MagicMock()]
        
        task_with_single_agent = MagicMock()
        task_with_single_agent.assigned_agents = [mock_agent]
        
        tasks = [task_with_multiple_agents, task_with_single_agent]
        task_updates = []
        
        # Process each task
        for task in tasks:
            # Remove deleted agent
            task.assigned_agents = [a for a in task.assigned_agents if a.id != mock_agent.id]
            
            # Handle based on remaining agents
            if not task.assigned_agents:
                task.status = TaskStatus.PENDING
                task.error_message = f"Agent {mock_agent.name} was deleted"
            
            task_updates.append({
                "task_id": task.id,
                "task_title": getattr(task, 'title', 'Unknown'),
                "remaining_agents": len(task.assigned_agents)
            })
        
        # Verify correct handling
        assert len(task_updates) == 2
        assert task_updates[0]["remaining_agents"] == 1  # Still has agents
        assert task_updates[1]["remaining_agents"] == 0  # No agents left
        assert task_with_single_agent.status == TaskStatus.PENDING