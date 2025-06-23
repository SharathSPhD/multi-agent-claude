"""
Test configuration and fixtures for MCP Multi-Agent System tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import Base
from database import get_db
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine(
        "sqlite:///:memory:", 
        echo=False,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield engine
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client with test database"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_claude_code_sdk():
    """Mock Claude Code SDK for testing"""
    with patch('claude_code_sdk.query') as mock_query:
        # Mock response messages
        mock_messages = [
            {"type": "text", "content": "Starting task execution..."},
            {"type": "text", "content": "Analyzing requirements..."},
            {"type": "text", "content": "Implementation complete."},
            {"type": "json", "content": {"result": "success", "output": "Task completed successfully"}}
        ]
        
        async def mock_async_generator(*args, **kwargs):
            for message in mock_messages:
                yield message
        
        mock_query.return_value = mock_async_generator()
        yield mock_query


@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        "name": "Test Agent",
        "role": "tester", 
        "system_prompt": "You are a test agent",
        "capabilities": ["testing", "validation"],
        "tools": ["pytest", "unittest"],
        "constraints": ["test environment only"]
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "name": "Test Task",
        "description": "A test task for validation",
        "requirements": ["test requirement 1", "test requirement 2"],
        "expected_output": "Test output",
        "success_criteria": ["criteria 1", "criteria 2"],
        "priority": 1
    }


@pytest.fixture
def sample_execution_data():
    """Sample execution data for testing"""
    return {
        "agent_id": 1,
        "task_id": 1,
        "work_directory": "/tmp/test",
        "status": "pending"
    }


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for launch script testing"""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.pid = 12345
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        yield mock_popen


@pytest.fixture
def mock_webbrowser():
    """Mock webbrowser for launch script testing"""
    with patch('webbrowser.open') as mock_browser:
        yield mock_browser


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system operations"""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.is_file') as mock_is_file, \
         patch('pathlib.Path.is_dir') as mock_is_dir:
        
        # Default behavior - files exist
        mock_exists.return_value = True
        mock_is_file.return_value = True  
        mock_is_dir.return_value = True
        
        yield {
            'exists': mock_exists,
            'is_file': mock_is_file,
            'is_dir': mock_is_dir,
            'temp_dir': temp_dir
        }


@pytest.fixture
def claude_code_options():
    """Sample Claude Code options for testing"""
    return {
        "max_turns": 3,
        "cwd": "/tmp/test",
        "permission_mode": "bypassPermissions",
        "system_prompt": "Test system prompt"
    }


@pytest.fixture
def mock_virtual_env():
    """Mock virtual environment detection"""
    with patch.dict(os.environ, {'VIRTUAL_ENV': '/path/to/venv'}):
        yield True