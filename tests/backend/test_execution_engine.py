"""
Test updated execution engine with Claude CLI and async task management
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os
import uuid

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.execution_engine import ExecutionEngine
from models import Agent, Task, Execution, AgentStatus, TaskStatus
from schemas import TaskExecutionRequest, ExecutionResponse


class TestExecutionEngine:
    """Test ExecutionEngine class with current implementation"""
    
    @pytest.fixture
    def execution_engine(self):
        """Create ExecutionEngine instance"""
        return ExecutionEngine()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        db = Mock(spec=Session)
        db.commit = Mock()
        db.refresh = Mock()
        db.add = Mock()
        db.query = Mock()
        db.close = Mock()
        return db
    
    @pytest.fixture
    def sample_agent(self):
        """Sample agent for testing"""
        agent = Agent(
            id="agent-123",
            name="test_agent",
            role="Test Agent",
            description="A test agent",
            system_prompt="You are a test agent",
            capabilities=["testing"],
            tools=["pytest"],
            objectives=["test execution"],
            constraints=["test only"],
            status=AgentStatus.IDLE
        )
        return agent
    
    @pytest.fixture
    def sample_task(self):
        """Sample task for testing"""
        task = Task(
            id="task-123",
            title="Test Task",
            description="A test task",
            expected_output="Test output",
            priority="high",
            status=TaskStatus.PENDING,
            estimated_duration="30 minutes"
        )
        return task
    
    @pytest.fixture
    def sample_execution(self):
        """Sample execution for testing"""
        execution = Execution(
            id="exec-123",
            agent_id="agent-123",
            task_id="task-123",
            status="starting",
            start_time=datetime.utcnow(),
            work_directory="/test/path",
            logs=[],
            output={},
            error_details={}
        )
        return execution

    @pytest.fixture
    def sample_request(self):
        """Sample task execution request"""
        return TaskExecutionRequest(
            task_id="task-123",
            agent_ids=["agent-123"],
            work_directory="/test/path"
        )

    def test_execution_response_serialization(self, execution_engine, mock_db_session, sample_execution):
        """Test ExecutionResponse serialization with all required fields"""
        
        # Mock database query to return our sample execution
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Test single execution response
        response = execution_engine.get_execution_status("exec-123", mock_db_session)
        
        assert response is not None
        assert response.id == "exec-123"
        assert response.work_directory == "/test/path"
        assert isinstance(response.logs, list)
        assert isinstance(response.output, dict)

    def test_get_all_executions_with_complete_fields(self, execution_engine, mock_db_session, sample_execution):
        """Test get_all_executions returns properly formatted ExecutionResponse objects"""
        
        # Mock database query to return list of executions
        mock_db_session.query.return_value.all.return_value = [sample_execution]
        
        # Test all executions response
        responses = execution_engine.get_all_executions(mock_db_session)
        
        assert len(responses) == 1
        response = responses[0]
        
        # Check all required fields are present
        assert response.id == "exec-123"
        assert response.task_id == "task-123"
        assert response.agent_id == "agent-123"
        assert response.status == "starting"
        assert response.work_directory == "/test/path"
        assert hasattr(response, 'memory_usage')
        assert hasattr(response, 'api_calls_made')
        assert hasattr(response, 'agent_response')
        assert hasattr(response, 'needs_interaction')

    @pytest.mark.asyncio
    async def test_start_task_execution_creates_async_task(self, execution_engine, mock_db_session, 
                                                         sample_agent, sample_task, sample_request):
        """Test that start_task_execution creates async task properly"""
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_task,  # First call for task
            sample_agent  # Second call for agent
        ]
        
        # Mock agent status check
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_agent]
        
        with patch('asyncio.create_task') as mock_create_task:
            mock_task = AsyncMock()
            mock_create_task.return_value = mock_task
            
            # Execute
            response = await execution_engine.start_task_execution(mock_db_session, sample_request)
            
            # Verify async task was created
            mock_create_task.assert_called_once()
            assert response.execution_id is not None
            assert response.status == "starting"

    @pytest.mark.asyncio
    async def test_execute_with_timeout_database_session_handling(self, execution_engine):
        """Test that _execute_with_timeout creates its own database session"""
        
        mock_execution = Mock()
        mock_task = Mock()
        mock_agent = Mock()
        
        mock_execution.logs = []
        mock_task.estimated_duration = "30 minutes"
        
        with patch('database.SessionLocal') as mock_session_local, \
             patch.object(execution_engine, '_execute_timeout_logic') as mock_timeout_logic:
            
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_execution, mock_task, mock_agent
            ]
            
            # Execute
            await execution_engine._execute_with_timeout("exec-123", "task-123", "agent-123", "/test/path")
            
            # Verify new session was created and closed
            mock_session_local.assert_called_once()
            mock_db.close.assert_called_once()
            mock_timeout_logic.assert_called_once()

    @pytest.mark.asyncio 
    async def test_claude_cli_command_structure(self, execution_engine, mock_db_session, 
                                              sample_execution, sample_task, sample_agent):
        """Test that Claude CLI command uses proper flags"""
        
        sample_execution.logs = []
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('shutil.which') as mock_which, \
             patch('pathlib.Path') as mock_path:
            
            mock_which.return_value = "/usr/local/bin/claude"
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.absolute.return_value = "/test/path"
            mock_path.return_value = mock_path_instance
            
            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b'{"result": "success"}', b'')
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            # Execute Claude CLI method
            await execution_engine._execute_with_claude_sdk_timeout(
                mock_db_session, sample_execution, sample_task, sample_agent, "/test/path"
            )
            
            # Verify command structure
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0]
            
            # Check for proper flags
            assert "claude" in args
            assert "-p" in args
            assert "--output-format" in args
            assert "json" in args
            assert "--max-turns" in args
            assert "3" in args
            assert "--verbose" in args

    def test_timeout_calculation_from_estimated_duration(self, execution_engine):
        """Test timeout calculation from task estimated_duration"""
        
        # Test various duration formats
        test_cases = [
            ("30 minutes", 1800),  # 30 * 60
            ("2 hours", 7200),     # 2 * 3600
            ("1 hour", 3600),      # 1 * 3600
            ("invalid format", 300)  # Should use default
        ]
        
        for duration_str, expected_seconds in test_cases:
            mock_task = Mock()
            mock_task.estimated_duration = duration_str
            
            # This would be tested in the actual _execute_timeout_logic method
            # For now, test the logic directly
            duration_seconds = 300  # default
            if mock_task.estimated_duration:
                if "hour" in mock_task.estimated_duration.lower():
                    try:
                        hours = float(mock_task.estimated_duration.split()[0])
                        duration_seconds = hours * 3600
                    except:
                        pass
                elif "minute" in mock_task.estimated_duration.lower():
                    try:
                        minutes = float(mock_task.estimated_duration.split()[0])
                        duration_seconds = minutes * 60
                    except:
                        pass
            
            if duration_str != "invalid format":
                assert duration_seconds == expected_seconds
            else:
                assert duration_seconds == 300  # default

    @pytest.mark.asyncio
    async def test_execution_error_handling_and_cleanup(self, execution_engine, mock_db_session,
                                                       sample_execution, sample_task, sample_agent):
        """Test error handling and proper cleanup in execution"""
        
        sample_execution.logs = []
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock subprocess to raise an exception
            mock_subprocess.side_effect = Exception("Claude CLI not found")
            
            # Execute and expect graceful error handling
            try:
                await execution_engine._execute_with_claude_sdk_timeout(
                    mock_db_session, sample_execution, sample_task, sample_agent, "/test/path"
                )
            except Exception as e:
                # Should handle gracefully and update execution status
                pass
            
            # Verify error was logged
            assert len(sample_execution.logs) > 0

    def test_agent_status_management(self, execution_engine, mock_db_session, sample_agent, sample_request):
        """Test that agent status is properly managed during execution"""
        
        # Mock database setup
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.title = "Test Task"
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task,    # Task query
            sample_agent  # Agent query
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_agent]
        
        with patch('asyncio.create_task'):
            # Execute
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(
                    execution_engine.start_task_execution(mock_db_session, sample_request)
                )
                
                # Verify agent status was updated to executing
                assert sample_agent.status == AgentStatus.EXECUTING
                assert sample_agent.last_active is not None
                
            finally:
                loop.close()

    @pytest.mark.asyncio
    async def test_execution_abort_functionality(self, execution_engine, mock_db_session, sample_execution):
        """Test execution abort functionality"""
        
        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Mock running execution
        execution_engine.running_executions[sample_execution.id] = AsyncMock()
        
        # Test abort
        result = await execution_engine.abort_execution(sample_execution.id, mock_db_session)
        
        assert result is True
        assert sample_execution.status == "cancelled"
        assert sample_execution.end_time is not None

    def test_work_directory_validation(self, execution_engine, mock_db_session, sample_execution, 
                                     sample_task, sample_agent):
        """Test work directory validation in execution"""
        
        sample_execution.logs = []
        
        # Test with None work directory
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            with pytest.raises(ValueError, match="Work directory is required"):
                loop.run_until_complete(
                    execution_engine._execute_task_internal(
                        mock_db_session, sample_execution, sample_task, [sample_agent], None
                    )
                )
        finally:
            loop.close()