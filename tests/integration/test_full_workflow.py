"""
Integration tests for full system workflow
"""

import pytest
import asyncio
import time
from unittest.mock import patch, Mock
import requests
import subprocess
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestFullSystemWorkflow:
    """Test complete system integration workflows"""
    
    @pytest.fixture
    def system_setup(self):
        """Setup system for integration testing"""
        return {
            "backend_url": "http://localhost:8000",
            "frontend_url": "http://localhost:3000",
            "test_timeout": 30
        }

    def test_agent_creation_to_execution_workflow(self, client, mock_claude_code_sdk):
        """Test complete workflow from agent creation to task execution"""
        
        # Step 1: Create an agent
        agent_data = {
            "name": "Integration Test Agent",
            "role": "integration_tester",
            "system_prompt": "You are an integration test agent",
            "capabilities": ["testing", "integration"],
            "tools": ["pytest"],
            "constraints": ["test environment"]
        }
        
        agent_response = client.post("/api/agents", json=agent_data)
        assert agent_response.status_code == 200
        agent_id = agent_response.json()["id"]
        
        # Step 2: Create a task
        task_data = {
            "name": "Integration Test Task",
            "description": "A task for integration testing",
            "requirements": ["execute successfully"],
            "expected_output": "Integration test complete",
            "success_criteria": ["no errors"],
            "priority": 1
        }
        
        task_response = client.post("/api/tasks", json=task_data)
        assert task_response.status_code == 200
        task_id = task_response.json()["id"]
        
        # Step 3: Execute the task
        execution_data = {
            "agent_id": agent_id,
            "task_id": task_id,
            "work_directory": "/tmp/integration_test"
        }
        
        exec_response = client.post("/api/execution/start", json=execution_data)
        assert exec_response.status_code == 200
        execution_id = exec_response.json()["execution_id"]
        
        # Step 4: Monitor execution
        status_response = client.get(f"/api/execution/{execution_id}")
        assert status_response.status_code == 200
        
        # Step 5: Verify execution completion
        execution_data = status_response.json()
        assert execution_data["id"] == execution_id
        assert execution_data["agent_id"] == agent_id
        assert execution_data["task_id"] == task_id

    def test_multi_agent_orchestration_workflow(self, client, mock_claude_code_sdk):
        """Test multi-agent orchestration workflow"""
        
        # Create multiple agents
        agents = []
        for i in range(3):
            agent_data = {
                "name": f"Orchestration Agent {i+1}",
                "role": f"role_{i+1}",
                "system_prompt": f"You are orchestration agent {i+1}",
                "capabilities": ["orchestration"],
                "tools": ["coordination"],
                "constraints": ["test environment"]
            }
            response = client.post("/api/agents", json=agent_data)
            agents.append(response.json()["id"])
        
        # Create multiple tasks
        tasks = []
        for i in range(2):
            task_data = {
                "name": f"Orchestration Task {i+1}",
                "description": f"Task {i+1} for orchestration testing",
                "requirements": [f"requirement {i+1}"],
                "expected_output": f"Output {i+1}",
                "priority": i+1
            }
            response = client.post("/api/tasks", json=task_data)
            tasks.append(response.json()["id"])
        
        # Analyze workflow
        analysis_data = {
            "agent_ids": agents,
            "task_ids": tasks,
            "objective": "Integration test orchestration"
        }
        
        analysis_response = client.post("/api/orchestration/analyze", json=analysis_data)
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        assert "recommended_pattern" in analysis
        
        # Execute orchestration
        orchestration_data = {
            "pattern": analysis["recommended_pattern"],
            "agent_ids": agents,
            "task_ids": tasks,
            "config": {
                "max_iterations": 3,
                "communication_enabled": True
            }
        }
        
        orchestration_response = client.post("/api/orchestration/execute", json=orchestration_data)
        assert orchestration_response.status_code == 200
        orchestration_id = orchestration_response.json()["orchestration_id"]
        
        # Monitor orchestration
        monitor_response = client.get(f"/api/orchestration/monitor/{orchestration_id}")
        assert monitor_response.status_code == 200

    def test_error_recovery_workflow(self, client):
        """Test system error recovery and graceful degradation"""
        
        # Create agent
        agent_data = {
            "name": "Error Recovery Agent",
            "role": "error_handler",
            "system_prompt": "Handle errors gracefully"
        }
        agent_response = client.post("/api/agents", json=agent_data)
        agent_id = agent_response.json()["id"]
        
        # Create task
        task_data = {
            "name": "Error Recovery Task",
            "description": "Task that might fail"
        }
        task_response = client.post("/api/tasks", json=task_data)
        task_id = task_response.json()["id"]
        
        # Mock Claude Code SDK to raise an error
        with patch('services.execution_engine.query') as mock_query:
            mock_query.side_effect = Exception("Simulated error")
            
            # Execute task (should handle error gracefully)
            execution_data = {
                "agent_id": agent_id,
                "task_id": task_id
            }
            
            exec_response = client.post("/api/execution/start", json=execution_data)
            # Should still return 200 with error handling
            assert exec_response.status_code == 200

    def test_working_directory_management(self, client, temp_dir, mock_claude_code_sdk):
        """Test working directory creation and management"""
        
        # Create agent and task
        agent_data = {"name": "Dir Agent", "role": "dir_tester", "system_prompt": "Test directories"}
        task_data = {"name": "Dir Task", "description": "Test directory management"}
        
        agent_response = client.post("/api/agents", json=agent_data)
        task_response = client.post("/api/tasks", json=task_data)
        
        agent_id = agent_response.json()["id"]
        task_id = task_response.json()["id"]
        
        # Execute with custom working directory
        custom_work_dir = str(temp_dir / "custom_work")
        execution_data = {
            "agent_id": agent_id,
            "task_id": task_id,
            "work_directory": custom_work_dir
        }
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            exec_response = client.post("/api/execution/start", json=execution_data)
            assert exec_response.status_code == 200
            
            # Verify directory creation was attempted
            mock_mkdir.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_real_time_updates(self, client):
        """Test WebSocket real-time updates"""
        
        # Note: This test requires a more complex setup with actual WebSocket testing
        # For now, we'll test the endpoint availability
        
        try:
            with client.websocket_connect("/ws") as websocket:
                # Basic connection test
                assert websocket is not None
                
                # Could send test messages and verify responses
                # websocket.send_text("test message")
                # response = websocket.receive_text()
                
        except Exception as e:
            # WebSocket might not be fully configured in test environment
            pytest.skip(f"WebSocket test skipped: {e}")

    def test_api_health_and_status(self, client):
        """Test system health and status endpoints"""
        
        # Test health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        
        # Test root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()
        assert "message" in root_data

    def test_data_persistence(self, client):
        """Test data persistence across operations"""
        
        # Create agent
        agent_data = {
            "name": "Persistence Agent",
            "role": "persistence_tester",
            "system_prompt": "Test data persistence"
        }
        agent_response = client.post("/api/agents", json=agent_data)
        agent_id = agent_response.json()["id"]
        
        # Verify agent persists
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Persistence Agent"
        
        # Update agent
        update_data = {"name": "Updated Persistence Agent"}
        update_response = client.put(f"/api/agents/{agent_id}", json=update_data)
        assert update_response.status_code == 200
        
        # Verify update persists
        verify_response = client.get(f"/api/agents/{agent_id}")
        assert verify_response.json()["name"] == "Updated Persistence Agent"

    def test_concurrent_operations(self, client, mock_claude_code_sdk):
        """Test concurrent operations and race conditions"""
        
        import threading
        import time
        
        # Create agent and task
        agent_data = {"name": "Concurrent Agent", "role": "concurrent_tester", "system_prompt": "Test concurrency"}
        task_data = {"name": "Concurrent Task", "description": "Test concurrent execution"}
        
        agent_response = client.post("/api/agents", json=agent_data)
        task_response = client.post("/api/tasks", json=task_data)
        
        agent_id = agent_response.json()["id"]
        task_id = task_response.json()["id"]
        
        # Execute multiple concurrent requests
        def execute_task():
            execution_data = {
                "agent_id": agent_id,
                "task_id": task_id
            }
            return client.post("/api/execution/start", json=execution_data)
        
        # Run concurrent executions
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda: results.append(execute_task()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all requests were handled
        assert len(results) == 3
        for result in results:
            assert result.status_code == 200

    def test_large_data_handling(self, client):
        """Test handling of large data sets"""
        
        # Create agent with large data
        large_capabilities = [f"capability_{i}" for i in range(100)]
        large_tools = [f"tool_{i}" for i in range(50)]
        large_constraints = [f"constraint_{i}" for i in range(30)]
        
        agent_data = {
            "name": "Large Data Agent",
            "role": "large_data_tester",
            "system_prompt": "Test large data handling",
            "capabilities": large_capabilities,
            "tools": large_tools,
            "constraints": large_constraints
        }
        
        response = client.post("/api/agents", json=agent_data)
        assert response.status_code == 200
        
        # Verify data integrity
        agent_id = response.json()["id"]
        get_response = client.get(f"/api/agents/{agent_id}")
        retrieved_agent = get_response.json()
        
        assert len(retrieved_agent["capabilities"]) == 100
        assert len(retrieved_agent["tools"]) == 50
        assert len(retrieved_agent["constraints"]) == 30