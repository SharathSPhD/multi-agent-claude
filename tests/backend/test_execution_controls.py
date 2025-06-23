"""
Test execution control features (pause/resume/abort)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.execution_engine import ExecutionEngine
from models import Agent, Task, Execution, AgentStatus, TaskStatus


class TestExecutionControls:
    """Test execution control functionality"""
    
    @pytest.fixture
    def execution_engine(self):
        """Create execution engine instance for testing"""
        return ExecutionEngine()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def sample_agent(self):
        """Create sample agent for testing"""
        agent = MagicMock()
        agent.id = "test-agent-id"
        agent.name = "Test Agent"
        agent.status = AgentStatus.EXECUTING
        return agent
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing"""
        task = MagicMock()
        task.id = "test-task-id"
        task.title = "Test Task"
        task.status = TaskStatus.IN_PROGRESS
        return task
    
    @pytest.fixture
    def sample_execution(self):
        """Create sample execution for testing"""
        execution = MagicMock()
        execution.id = "test-execution-id"
        execution.status = "running"
        execution.logs = []
        execution.output = {}
        execution.agent_response = {}
        execution.task_id = "test-task-id"
        execution.agent_id = "test-agent-id"
        return execution

    @pytest.mark.asyncio
    async def test_pause_execution(self, execution_engine, mock_db, sample_execution, sample_agent):
        """Test pausing a running execution"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_execution
        mock_task = AsyncMock()
        execution_engine.running_executions = {"test-execution-id": mock_task}
        
        # Test pause
        result = await execution_engine.pause_execution(mock_db, "test-execution-id")
        
        # Verify
        assert result["status"] == "paused"
        assert "test-execution-id" in execution_engine.paused_executions
        assert sample_execution.status == "paused"
        assert mock_task.cancel.called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_invalid_status(self, execution_engine, mock_db, sample_execution):
        """Test pausing execution with invalid status"""
        # Setup
        sample_execution.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Test and verify exception
        with pytest.raises(ValueError, match="Cannot pause execution with status"):
            await execution_engine.pause_execution(mock_db, "test-execution-id")

    @pytest.mark.asyncio
    async def test_resume_execution(self, execution_engine, mock_db, sample_execution, sample_agent, sample_task):
        """Test resuming a paused execution"""
        # Setup
        sample_execution.status = "paused"
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_execution, sample_task, sample_agent]
        execution_engine.paused_executions = {
            "test-execution-id": {
                "task_id": "test-task-id",
                "agent_id": "test-agent-id",
                "logs": [],
                "output": {},
                "agent_response": {},
                "pause_time": datetime.utcnow()
            }
        }
        
        with patch.object(execution_engine, '_execute_task') as mock_execute:
            mock_execute.return_value = AsyncMock()
            with patch('asyncio.create_task') as mock_create_task:
                mock_create_task.return_value = AsyncMock()
                
                # Test resume
                result = await execution_engine.resume_execution(mock_db, "test-execution-id")
                
                # Verify
                assert result["status"] == "resumed"
                assert "test-execution-id" not in execution_engine.paused_executions
                assert sample_execution.status == "running"
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_invalid_status(self, execution_engine, mock_db, sample_execution):
        """Test resuming execution with invalid status"""
        # Setup
        sample_execution.status = "running"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Test and verify exception
        with pytest.raises(ValueError, match="Cannot resume execution with status"):
            await execution_engine.resume_execution(mock_db, "test-execution-id")

    @pytest.mark.asyncio
    async def test_abort_execution(self, execution_engine, mock_db, sample_execution, sample_task, sample_agent):
        """Test aborting an execution"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_execution, sample_task, sample_agent]
        mock_async_task = AsyncMock()
        execution_engine.running_executions = {"test-execution-id": mock_async_task}
        execution_engine.paused_executions = {"test-execution-id": {}}
        
        # Test abort
        result = await execution_engine.abort_execution(mock_db, "test-execution-id")
        
        # Verify
        assert result["status"] == "aborted"
        assert sample_execution.status == "aborted"
        assert sample_execution.end_time is not None
        assert sample_task.status == TaskStatus.FAILED
        assert sample_agent.status == AgentStatus.IDLE
        assert "test-execution-id" not in execution_engine.running_executions
        assert "test-execution-id" not in execution_engine.paused_executions
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_abort_nonexistent_execution(self, execution_engine, mock_db):
        """Test aborting non-existent execution"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test and verify exception
        with pytest.raises(ValueError, match="Execution test-execution-id not found"):
            await execution_engine.abort_execution(mock_db, "test-execution-id")

    @pytest.mark.asyncio
    async def test_state_preservation(self, execution_engine, mock_db, sample_execution):
        """Test that execution state is properly preserved during pause"""
        # Setup
        sample_execution.logs = [{"message": "test log"}]
        sample_execution.output = {"key": "value"}
        sample_execution.agent_response = {"analysis": "test analysis"}
        mock_db.query.return_value.filter.return_value.first.return_value = sample_execution
        execution_engine.running_executions = {"test-execution-id": AsyncMock()}
        
        # Test pause
        await execution_engine.pause_execution(mock_db, "test-execution-id")
        
        # Verify state preservation
        paused_state = execution_engine.paused_executions["test-execution-id"]
        assert paused_state["logs"] == [{"message": "test log"}]
        assert paused_state["output"] == {"key": "value"}
        assert paused_state["agent_response"] == {"analysis": "test analysis"}
        assert "pause_time" in paused_state

    @pytest.mark.asyncio
    async def test_websocket_notifications(self, execution_engine, mock_db, sample_execution):
        """Test that websocket notifications are sent for control actions"""
        # Setup
        mock_websocket_manager = AsyncMock()
        execution_engine.set_websocket_manager(mock_websocket_manager)
        mock_db.query.return_value.filter.return_value.first.return_value = sample_execution
        execution_engine.running_executions = {"test-execution-id": AsyncMock()}
        
        # Test pause with websocket notification
        await execution_engine.pause_execution(mock_db, "test-execution-id")
        
        # Verify websocket broadcast was called
        mock_websocket_manager.broadcast.assert_called_once()
        call_args = mock_websocket_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "execution_paused"
        assert call_args["execution_id"] == "test-execution-id"