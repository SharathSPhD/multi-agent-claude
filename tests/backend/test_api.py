"""
Test FastAPI endpoints for MCP Multi-Agent System
"""

import pytest
import json
from fastapi.testclient import TestClient


class TestAgentAPI:
    """Test agent CRUD operations"""
    
    def test_create_agent(self, client, sample_agent_data):
        """Test agent creation"""
        response = client.post("/api/agents", json=sample_agent_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_agent_data["name"]
        assert data["role"] == sample_agent_data["role"]
        assert "id" in data
    
    def test_get_agents(self, client, sample_agent_data):
        """Test getting all agents"""
        # Create an agent first
        client.post("/api/agents", json=sample_agent_data)
        
        response = client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_agent_by_id(self, client, sample_agent_data):
        """Test getting agent by ID"""
        # Create an agent
        create_response = client.post("/api/agents", json=sample_agent_data)
        agent_id = create_response.json()["id"]
        
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
    
    def test_update_agent(self, client, sample_agent_data):
        """Test agent update"""
        # Create an agent
        create_response = client.post("/api/agents", json=sample_agent_data)
        agent_id = create_response.json()["id"]
        
        # Update the agent
        update_data = {"name": "Updated Test Agent"}
        response = client.put(f"/api/agents/{agent_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Test Agent"
    
    def test_delete_agent(self, client, sample_agent_data):
        """Test agent deletion"""
        # Create an agent
        create_response = client.post("/api/agents", json=sample_agent_data)
        agent_id = create_response.json()["id"]
        
        # Delete the agent
        response = client.delete(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 404


class TestTaskAPI:
    """Test task CRUD operations"""
    
    def test_create_task(self, client, sample_task_data):
        """Test task creation"""
        response = client.post("/api/tasks", json=sample_task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_task_data["name"]
        assert data["description"] == sample_task_data["description"]
        assert "id" in data
    
    def test_get_tasks(self, client, sample_task_data):
        """Test getting all tasks"""
        # Create a task first
        client.post("/api/tasks", json=sample_task_data)
        
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_task_by_id(self, client, sample_task_data):
        """Test getting task by ID"""
        # Create a task
        create_response = client.post("/api/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id


class TestExecutionAPI:
    """Test execution endpoints"""
    
    def test_start_execution(self, client, sample_agent_data, sample_task_data, mock_claude_code_sdk):
        """Test starting task execution"""
        # Create agent and task
        agent_response = client.post("/api/agents", json=sample_agent_data)
        task_response = client.post("/api/tasks", json=sample_task_data)
        
        agent_id = agent_response.json()["id"]
        task_id = task_response.json()["id"]
        
        # Start execution
        execution_data = {
            "agent_id": agent_id,
            "task_id": task_id,
            "work_directory": "/tmp/test"
        }
        
        response = client.post("/api/execution/start", json=execution_data)
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert data["status"] == "started"
    
    def test_get_execution_status(self, client, sample_agent_data, sample_task_data, mock_claude_code_sdk):
        """Test getting execution status"""
        # Create agent and task
        agent_response = client.post("/api/agents", json=sample_agent_data)
        task_response = client.post("/api/tasks", json=sample_task_data)
        
        agent_id = agent_response.json()["id"]
        task_id = task_response.json()["id"]
        
        # Start execution
        execution_data = {
            "agent_id": agent_id,
            "task_id": task_id
        }
        exec_response = client.post("/api/execution/start", json=execution_data)
        execution_id = exec_response.json()["execution_id"]
        
        # Get status
        response = client.get(f"/api/execution/{execution_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "system" in data


class TestOrchestrationAPI:
    """Test orchestration endpoints"""
    
    def test_get_patterns(self, client):
        """Test getting workflow patterns"""
        response = client.get("/api/orchestration/patterns")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_analyze_workflow(self, client, sample_agent_data, sample_task_data):
        """Test workflow analysis"""
        # Create agents and tasks
        agent_response = client.post("/api/agents", json=sample_agent_data)
        task_response = client.post("/api/tasks", json=sample_task_data)
        
        analysis_data = {
            "agent_ids": [agent_response.json()["id"]],
            "task_ids": [task_response.json()["id"]],
            "objective": "Test objective"
        }
        
        response = client.post("/api/orchestration/analyze", json=analysis_data)
        assert response.status_code == 200
        data = response.json()
        assert "recommended_pattern" in data
        assert "analysis" in data


class TestWebSocketEndpoints:
    """Test WebSocket connections"""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment"""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None
    
    def test_websocket_agent_updates(self, client, sample_agent_data):
        """Test WebSocket agent update notifications"""
        with client.websocket_connect("/ws") as websocket:
            # Create an agent to trigger notification
            response = client.post("/api/agents", json=sample_agent_data)
            assert response.status_code == 200
            
            # Should receive WebSocket notification
            # Note: This test may need adjustment based on actual WebSocket implementation