"""
Test Claude Code SDK execution engine
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.execution_engine import ExecutionEngine
from models import Agent, Task, Execution


class TestExecutionEngine:
    """Test ExecutionEngine class"""
    
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
        return db
    
    @pytest.fixture
    def sample_agent(self):
        """Sample agent for testing"""
        agent = Agent(
            id=1,
            name="Test Agent",
            role="tester",
            system_prompt="You are a test agent",
            capabilities=["testing"],
            tools=["pytest"],
            constraints=["test only"]
        )
        return agent
    
    @pytest.fixture
    def sample_task(self):
        """Sample task for testing"""
        task = Task(
            id=1,
            name="Test Task",
            description="A test task",
            requirements=["requirement 1"],
            expected_output="Test output",
            success_criteria=["criteria 1"],
            priority=1
        )
        return task
    
    @pytest.fixture
    def sample_execution(self):
        """Sample execution for testing"""
        execution = Execution(
            id=1,
            agent_id=1,
            task_id=1,
            status="pending",
            work_directory="/tmp/test"
        )
        return execution

    @pytest.mark.asyncio
    async def test_spawn_claude_code_agent_success(self, execution_engine, mock_db_session, 
                                                 sample_agent, sample_task, sample_execution, 
                                                 mock_claude_code_sdk):
        """Test successful Claude Code agent spawning"""
        
        # Mock the claude_code_sdk
        with patch('services.execution_engine.query') as mock_query:
            # Setup mock response
            mock_messages = [
                {"type": "text", "content": "Starting execution..."},
                {"type": "json", "content": {"result": "success", "analysis": "Task completed"}}
            ]
            
            async def mock_async_generator(*args, **kwargs):
                for message in mock_messages:
                    yield message
            
            mock_query.return_value = mock_async_generator()
            
            # Execute the method
            result = await execution_engine._spawn_claude_code_agent(
                sample_agent, sample_task, sample_execution, mock_db_session
            )
            
            # Assertions
            assert result is not None
            assert isinstance(result, dict)
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_spawn_claude_code_agent_with_working_directory(self, execution_engine, 
                                                                mock_db_session, sample_agent, 
                                                                sample_task, sample_execution):
        """Test Claude Code agent with custom working directory"""
        
        with patch('services.execution_engine.query') as mock_query, \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.exists') as mock_exists:
            
            mock_exists.return_value = False  # Directory doesn't exist
            
            async def mock_async_generator(*args, **kwargs):
                yield {"type": "text", "content": "Task complete"}
            
            mock_query.return_value = mock_async_generator()
            
            # Test with custom work directory
            result = await execution_engine._spawn_claude_code_agent(
                sample_agent, sample_task, sample_execution, mock_db_session, 
                work_dir="/custom/path"
            )
            
            # Verify directory creation was attempted
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @pytest.mark.asyncio 
    async def test_spawn_claude_code_agent_json_error_handling(self, execution_engine, 
                                                             mock_db_session, sample_agent, 
                                                             sample_task, sample_execution):
        """Test JSON parsing error handling"""
        
        with patch('services.execution_engine.query') as mock_query:
            # Mock response with malformed JSON
            async def mock_async_generator(*args, **kwargs):
                yield {"type": "text", "content": "Invalid JSON: {malformed"}
                yield {"type": "text", "content": "Recovery message"}
            
            mock_query.return_value = mock_async_generator()
            
            # Should handle the error gracefully
            result = await execution_engine._spawn_claude_code_agent(
                sample_agent, sample_task, sample_execution, mock_db_session
            )
            
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_spawn_claude_code_agent_exception_handling(self, execution_engine, 
                                                            mock_db_session, sample_agent, 
                                                            sample_task, sample_execution):
        """Test exception handling in agent spawning"""
        
        with patch('services.execution_engine.query') as mock_query:
            # Mock query to raise an exception
            mock_query.side_effect = Exception("SDK Error")
            
            # Should handle the exception gracefully
            result = await execution_engine._spawn_claude_code_agent(
                sample_agent, sample_task, sample_execution, mock_db_session
            )
            
            assert result is not None
            assert "error" in result

    def test_claude_code_options_creation(self, execution_engine, sample_agent, sample_task):
        """Test ClaudeCodeOptions creation"""
        
        with patch('services.execution_engine.ClaudeCodeOptions') as mock_options:
            
            # Test options creation
            execution_engine._create_claude_code_options(
                agent=sample_agent,
                task=sample_task,
                work_dir="/test/path"
            )
            
            # Verify options were created with correct parameters
            mock_options.assert_called_once()
            call_kwargs = mock_options.call_args[1]
            assert call_kwargs["max_turns"] == 3
            assert call_kwargs["cwd"] == "/test/path"
            assert call_kwargs["permission_mode"] == "bypassPermissions"
            assert "Test Agent" in call_kwargs["system_prompt"]

    @pytest.mark.asyncio
    async def test_execute_task_end_to_end(self, execution_engine, mock_db_session, 
                                         sample_agent, sample_task, mock_claude_code_sdk):
        """Test end-to-end task execution"""
        
        with patch.object(execution_engine, '_spawn_claude_code_agent') as mock_spawn:
            mock_spawn.return_value = {
                "status": "completed",
                "result": "Task executed successfully",
                "agent_response": {"analysis": "Complete"}
            }
            
            # Execute task
            result = await execution_engine.execute_task(
                agent_id=1,
                task_id=1,
                db=mock_db_session,
                work_directory="/tmp/test"
            )
            
            assert result is not None
            assert result["status"] == "completed"
            mock_spawn.assert_called_once()

    def test_parse_claude_response_valid_json(self, execution_engine):
        """Test parsing valid JSON response"""
        
        response = '{"result": "success", "data": {"key": "value"}}'
        parsed = execution_engine._parse_claude_response(response)
        
        assert parsed is not None
        assert parsed["result"] == "success"
        assert parsed["data"]["key"] == "value"

    def test_parse_claude_response_invalid_json(self, execution_engine):
        """Test parsing invalid JSON response"""
        
        response = '{"invalid": json}'
        parsed = execution_engine._parse_claude_response(response)
        
        # Should return None or handle gracefully
        assert parsed is None or isinstance(parsed, dict)

    def test_format_task_prompt(self, execution_engine, sample_agent, sample_task):
        """Test task prompt formatting"""
        
        prompt = execution_engine._format_task_prompt(sample_agent, sample_task)
        
        assert isinstance(prompt, str)
        assert sample_task.name in prompt
        assert sample_task.description in prompt
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_execution_timeout_handling(self, execution_engine, mock_db_session, 
                                            sample_agent, sample_task, sample_execution):
        """Test execution timeout handling"""
        
        with patch('services.execution_engine.query') as mock_query:
            # Mock a long-running operation that times out
            async def slow_generator(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate slow operation
                yield {"type": "text", "content": "Should not reach here"}
            
            mock_query.return_value = slow_generator()
            
            # Execute with timeout
            with patch('asyncio.wait_for') as mock_wait_for:
                mock_wait_for.side_effect = asyncio.TimeoutError()
                
                result = await execution_engine._spawn_claude_code_agent(
                    sample_agent, sample_task, sample_execution, mock_db_session
                )
                
                # Should handle timeout gracefully
                assert result is not None
                assert "error" in result or "timeout" in str(result).lower()

    def test_database_update_on_completion(self, execution_engine, mock_db_session, sample_execution):
        """Test database updates on execution completion"""
        
        result_data = {
            "status": "completed",
            "agent_response": {"result": "success"},
            "needs_interaction": False
        }
        
        execution_engine._update_execution_in_db(sample_execution, result_data, mock_db_session)
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_execution)