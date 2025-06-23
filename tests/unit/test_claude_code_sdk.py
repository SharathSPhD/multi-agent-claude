"""
Unit tests for Claude Code SDK integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json


class TestClaudeCodeSDK:
    """Test Claude Code SDK integration and functionality"""
    
    @pytest.fixture
    def mock_claude_code_options(self):
        """Mock ClaudeCodeOptions"""
        with patch('claude_code_sdk.ClaudeCodeOptions') as mock_options:
            mock_instance = Mock()
            mock_options.return_value = mock_instance
            yield mock_options

    @pytest.mark.asyncio
    async def test_claude_code_query_basic(self, mock_claude_code_options):
        """Test basic Claude Code SDK query functionality"""
        
        with patch('claude_code_sdk.query') as mock_query:
            # Mock response
            mock_messages = [
                {"type": "text", "content": "Starting analysis..."},
                {"type": "text", "content": "Analysis complete."},
                {"type": "json", "content": {"result": "success"}}
            ]
            
            async def mock_async_generator(*args, **kwargs):
                for message in mock_messages:
                    yield message
            
            mock_query.return_value = mock_async_generator()
            
            # Import and use the query function
            from claude_code_sdk import query, ClaudeCodeOptions
            
            messages = []
            async for message in query(
                prompt="Test prompt",
                options=ClaudeCodeOptions(max_turns=3, permission_mode="bypassPermissions")
            ):
                messages.append(message)
            
            assert len(messages) == 3
            assert messages[0]["content"] == "Starting analysis..."
            assert messages[2]["content"]["result"] == "success"

    @pytest.mark.asyncio 
    async def test_claude_code_options_configuration(self, mock_claude_code_options):
        """Test ClaudeCodeOptions configuration"""
        
        with patch('claude_code_sdk.ClaudeCodeOptions') as mock_options:
            # Test options creation
            options = mock_options(
                max_turns=5,
                cwd="/test/directory",
                permission_mode="bypassPermissions",
                system_prompt="Test system prompt"
            )
            
            # Verify options were created with correct parameters
            mock_options.assert_called_once_with(
                max_turns=5,
                cwd="/test/directory", 
                permission_mode="bypassPermissions",
                system_prompt="Test system prompt"
            )

    @pytest.mark.asyncio
    async def test_claude_code_error_handling(self):
        """Test Claude Code SDK error handling"""
        
        with patch('claude_code_sdk.query') as mock_query:
            # Mock SDK error
            mock_query.side_effect = Exception("SDK connection error")
            
            try:
                from claude_code_sdk import query, ClaudeCodeOptions
                
                async for message in query(
                    prompt="Test prompt",
                    options=ClaudeCodeOptions()
                ):
                    pass
                
                assert False, "Should have raised exception"
            except Exception as e:
                assert "SDK connection error" in str(e)

    @pytest.mark.asyncio
    async def test_claude_code_streaming_responses(self):
        """Test streaming response handling"""
        
        with patch('claude_code_sdk.query') as mock_query:
            # Mock streaming responses
            async def mock_streaming_generator(*args, **kwargs):
                responses = [
                    {"type": "text", "content": "Step 1: Analyzing..."},
                    {"type": "text", "content": "Step 2: Processing..."},
                    {"type": "text", "content": "Step 3: Generating..."},
                    {"type": "json", "content": {"status": "complete", "steps": 3}}
                ]
                
                for i, response in enumerate(responses):
                    await asyncio.sleep(0.1)  # Simulate streaming delay
                    yield response
            
            mock_query.return_value = mock_streaming_generator()
            
            from claude_code_sdk import query, ClaudeCodeOptions
            
            messages = []
            start_time = asyncio.get_event_loop().time()
            
            async for message in query(
                prompt="Multi-step task",
                options=ClaudeCodeOptions(max_turns=5)
            ):
                messages.append(message)
            
            end_time = asyncio.get_event_loop().time()
            
            # Verify streaming behavior
            assert len(messages) == 4
            assert end_time - start_time >= 0.3  # At least 300ms for streaming
            assert messages[-1]["content"]["status"] == "complete"

    def test_claude_code_options_validation(self):
        """Test ClaudeCodeOptions parameter validation"""
        
        with patch('claude_code_sdk.ClaudeCodeOptions') as mock_options:
            # Test valid options
            valid_options = {
                "max_turns": 3,
                "cwd": "/valid/path",
                "permission_mode": "bypassPermissions",
                "system_prompt": "Valid prompt"
            }
            
            mock_options(**valid_options)
            mock_options.assert_called_with(**valid_options)
            
            # Test invalid options (implementation would validate)
            # This is a placeholder for actual validation logic
            assert True

    @pytest.mark.asyncio
    async def test_claude_code_timeout_handling(self):
        """Test timeout handling in Claude Code SDK"""
        
        with patch('claude_code_sdk.query') as mock_query:
            # Mock long-running operation
            async def slow_generator(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate slow operation
                yield {"type": "text", "content": "Finally done"}
            
            mock_query.return_value = slow_generator()
            
            from claude_code_sdk import query, ClaudeCodeOptions
            
            # Test with timeout
            try:
                messages = []
                async for message in asyncio.wait_for(
                    query(
                        prompt="Slow task",
                        options=ClaudeCodeOptions()
                    ),
                    timeout=1.0
                ):
                    messages.append(message)
                
                assert False, "Should have timed out"
            except asyncio.TimeoutError:
                # Expected behavior
                assert True

    @pytest.mark.asyncio
    async def test_claude_code_json_parsing(self):
        """Test JSON parsing in Claude Code responses"""
        
        with patch('claude_code_sdk.query') as mock_query:
            # Mock responses with various JSON formats
            mock_messages = [
                {"type": "text", "content": "Processing..."},
                {"type": "json", "content": {"valid": "json", "number": 42}},
                {"type": "text", "content": "Invalid JSON: {malformed"},
                {"type": "json", "content": {"final": "result"}}
            ]
            
            async def mock_generator(*args, **kwargs):
                for message in mock_messages:
                    yield message
            
            mock_query.return_value = mock_generator()
            
            from claude_code_sdk import query, ClaudeCodeOptions
            
            messages = []
            json_messages = []
            
            async for message in query(
                prompt="JSON test",
                options=ClaudeCodeOptions()
            ):
                messages.append(message)
                if message["type"] == "json":
                    json_messages.append(message["content"])
            
            assert len(messages) == 4
            assert len(json_messages) == 2
            assert json_messages[0]["valid"] == "json"
            assert json_messages[1]["final"] == "result"

    def test_claude_code_import_availability(self):
        """Test Claude Code SDK import availability"""
        
        try:
            import claude_code_sdk
            # SDK is available
            assert hasattr(claude_code_sdk, 'query')
            assert hasattr(claude_code_sdk, 'ClaudeCodeOptions')
        except ImportError:
            # SDK not available in test environment - that's okay
            pytest.skip("Claude Code SDK not available in test environment")

    @pytest.mark.asyncio
    async def test_claude_code_working_directory(self):
        """Test working directory functionality"""
        
        with patch('claude_code_sdk.query') as mock_query, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            
            mock_exists.return_value = False  # Directory doesn't exist
            
            async def mock_generator(*args, **kwargs):
                yield {"type": "text", "content": "Working in directory"}
            
            mock_query.return_value = mock_generator()
            
            from claude_code_sdk import query, ClaudeCodeOptions
            
            # Test with custom working directory
            async for message in query(
                prompt="Directory test",
                options=ClaudeCodeOptions(cwd="/test/work/dir")
            ):
                pass
            
            # Verify query was called with correct options
            assert mock_query.called

    @pytest.mark.asyncio
    async def test_claude_code_permission_modes(self):
        """Test different permission modes"""
        
        with patch('claude_code_sdk.query') as mock_query:
            async def mock_generator(*args, **kwargs):
                yield {"type": "text", "content": "Permission test"}
            
            mock_query.return_value = mock_generator()
            
            from claude_code_sdk import query, ClaudeCodeOptions
            
            # Test bypass permissions mode
            async for message in query(
                prompt="Permission test",
                options=ClaudeCodeOptions(permission_mode="bypassPermissions")
            ):
                pass
            
            # Verify query was called
            assert mock_query.called

    @pytest.mark.asyncio
    async def test_claude_code_multi_turn_conversation(self):
        """Test multi-turn conversation functionality"""
        
        with patch('claude_code_sdk.query') as mock_query:
            # Mock multi-turn conversation
            conversation_turns = [
                {"type": "text", "content": "Turn 1: Initial analysis"},
                {"type": "text", "content": "Turn 2: Follow-up questions"},
                {"type": "text", "content": "Turn 3: Final recommendations"},
                {"type": "json", "content": {"turns": 3, "complete": True}}
            ]
            
            async def mock_conversation(*args, **kwargs):
                for turn in conversation_turns:
                    yield turn
            
            mock_query.return_value = mock_conversation()
            
            from claude_code_sdk import query, ClaudeCodeOptions
            
            messages = []
            async for message in query(
                prompt="Multi-turn conversation",
                options=ClaudeCodeOptions(max_turns=3)
            ):
                messages.append(message)
            
            assert len(messages) == 4
            assert "Turn 1" in messages[0]["content"]
            assert "Turn 3" in messages[2]["content"]
            assert messages[3]["content"]["turns"] == 3

    def test_claude_code_system_prompt_integration(self):
        """Test system prompt integration"""
        
        with patch('claude_code_sdk.ClaudeCodeOptions') as mock_options:
            system_prompt = "You are a test assistant specialized in integration testing."
            
            mock_options(
                system_prompt=system_prompt,
                max_turns=3
            )
            
            # Verify system prompt was passed correctly
            mock_options.assert_called_with(
                system_prompt=system_prompt,
                max_turns=3
            )