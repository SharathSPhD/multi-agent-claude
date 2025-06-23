"""
Integration tests for new control features
"""

import pytest
import requests
import time
import asyncio
from unittest.mock import patch

BASE_URL = "http://localhost:8000"


class TestControlFeaturesIntegration:
    """Integration tests for control features"""
    
    @pytest.fixture(scope="class")
    def test_agent(self):
        """Create a test agent for integration tests"""
        agent_data = {
            "name": "Integration Test Agent",
            "role": "test_agent",
            "system_prompt": "You are a test agent for integration testing.",
            "capabilities": ["testing", "integration"],
            "tools": ["test-tools"],
            "objectives": ["test system integration"],
            "constraints": ["be fast", "be reliable"]
        }
        
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_data)
        if response.status_code == 200:
            return response.json()
        return None
    
    @pytest.fixture(scope="class")
    def test_task(self, test_agent):
        """Create a test task for integration tests"""
        if not test_agent:
            pytest.skip("Test agent not available")
        
        task_data = {
            "title": "Integration Test Task",
            "description": "A test task for integration testing of control features",
            "expected_output": "Test completion confirmation",
            "resources": ["test-resources"],
            "dependencies": [],
            "priority": "low",
            "estimated_duration": "30 seconds",
            "assigned_agent_ids": [test_agent["id"]]
        }
        
        response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
        if response.status_code == 200:
            return response.json()
        return None

    @pytest.mark.integration
    def test_execution_pause_resume_cycle(self, test_agent, test_task):
        """Test complete pause/resume cycle"""
        if not test_agent or not test_task:
            pytest.skip("Test fixtures not available")
        
        # Start execution
        execution_request = {
            "task_id": test_task["id"],
            "agent_ids": [test_agent["id"]],
            "execution_mode": "collaborative",
            "monitoring_enabled": True
        }
        
        response = requests.post(f"{BASE_URL}/api/execution/start", json=execution_request)
        assert response.status_code == 200
        execution = response.json()
        execution_id = execution["execution_id"]
        
        # Wait for execution to start
        time.sleep(2)
        
        # Verify execution is running
        status_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["status"] in ["running", "starting"]
        
        # Test pause
        pause_response = requests.post(f"{BASE_URL}/api/execution/{execution_id}/pause")
        assert pause_response.status_code == 200
        
        # Verify paused status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["status"] == "paused"
        
        # Test resume
        resume_response = requests.post(f"{BASE_URL}/api/execution/{execution_id}/resume")
        assert resume_response.status_code == 200
        
        # Verify resumed status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["status"] == "running"
        
        # Clean up - abort execution
        abort_response = requests.post(f"{BASE_URL}/api/execution/{execution_id}/abort")
        assert abort_response.status_code == 200

    @pytest.mark.integration
    def test_execution_abort(self, test_agent, test_task):
        """Test execution abort functionality"""
        if not test_agent or not test_task:
            pytest.skip("Test fixtures not available")
        
        # Start execution
        execution_request = {
            "task_id": test_task["id"],
            "agent_ids": [test_agent["id"]],
            "execution_mode": "collaborative"
        }
        
        response = requests.post(f"{BASE_URL}/api/execution/start", json=execution_request)
        assert response.status_code == 200
        execution = response.json()
        execution_id = execution["execution_id"]
        
        # Wait for execution to start
        time.sleep(2)
        
        # Test abort
        abort_response = requests.post(f"{BASE_URL}/api/execution/{execution_id}/abort")
        assert abort_response.status_code == 200
        
        # Verify aborted status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/execution/{execution_id}")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["status"] == "aborted"

    @pytest.mark.integration
    def test_agent_deletion_safe(self, test_agent):
        """Test safe agent deletion (without running executions)"""
        if not test_agent:
            pytest.skip("Test agent not available")
        
        # Ensure no running executions for this agent
        executions_response = requests.get(f"{BASE_URL}/api/execution/status")
        if executions_response.status_code == 200:
            executions = executions_response.json()
            running_executions = [e for e in executions if e["agent_id"] == test_agent["id"] and e["status"] in ["running", "starting", "paused"]]
            
            # Cancel any running executions first
            for execution in running_executions:
                requests.post(f"{BASE_URL}/api/execution/{execution['id']}/abort")
                time.sleep(1)
        
        # Test deletion
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{test_agent['id']}")
        assert delete_response.status_code == 200
        
        result = delete_response.json()
        assert "message" in result
        assert "affected_tasks" in result
        assert result["message"] == "Agent deleted successfully"

    @pytest.mark.integration
    def test_agent_deletion_with_running_execution(self):
        """Test agent deletion when agent has running executions"""
        # Create temporary agent and task for this test
        agent_data = {
            "name": "Temp Agent for Deletion Test",
            "role": "temp_agent",
            "system_prompt": "Temporary agent for testing deletion with running executions.",
            "capabilities": ["testing"],
            "tools": ["test-tools"],
            "objectives": ["test deletion"],
            "constraints": ["temporary"]
        }
        
        agent_response = requests.post(f"{BASE_URL}/api/agents", json=agent_data)
        if agent_response.status_code != 200:
            pytest.skip("Could not create temp agent")
        
        agent = agent_response.json()
        
        task_data = {
            "title": "Temp Task for Deletion Test",
            "description": "Temporary task for testing agent deletion",
            "expected_output": "Test output",
            "assigned_agent_ids": [agent["id"]]
        }
        
        task_response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
        if task_response.status_code != 200:
            pytest.skip("Could not create temp task")
        
        task = task_response.json()
        
        # Start execution
        execution_request = {
            "task_id": task["id"],
            "agent_ids": [agent["id"]]
        }
        
        exec_response = requests.post(f"{BASE_URL}/api/execution/start", json=execution_request)
        if exec_response.status_code != 200:
            pytest.skip("Could not start execution")
        
        execution = exec_response.json()
        time.sleep(1)  # Let execution start
        
        try:
            # Test deletion without force (should fail)
            delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent['id']}")
            
            if delete_response.status_code == 200:
                result = delete_response.json()
                # Should either succeed with cancellation or warn about executions
                assert "message" in result
            
            # Test deletion with force
            delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent['id']}?force=true")
            assert delete_response.status_code == 200
            
            result = delete_response.json()
            assert "cancelled_executions" in result or "message" in result
        
        finally:
            # Clean up - try to abort execution and delete agent if still exists
            try:
                requests.post(f"{BASE_URL}/api/execution/{execution['execution_id']}/abort")
                requests.delete(f"{BASE_URL}/api/agents/{agent['id']}?force=true")
            except:
                pass

    @pytest.mark.integration
    def test_api_endpoints_availability(self):
        """Test that all new API endpoints are available"""
        # Test health endpoint
        health_response = requests.get(f"{BASE_URL}/health")
        assert health_response.status_code == 200
        
        # Test execution status endpoint
        status_response = requests.get(f"{BASE_URL}/api/execution/status")
        assert status_response.status_code == 200
        
        # Test agents endpoint
        agents_response = requests.get(f"{BASE_URL}/api/agents")
        assert agents_response.status_code == 200
        
        # Test tasks endpoint
        tasks_response = requests.get(f"{BASE_URL}/api/tasks")
        assert tasks_response.status_code == 200

    @pytest.mark.integration
    def test_error_handling(self):
        """Test error handling for control operations"""
        # Test pause non-existent execution
        pause_response = requests.post(f"{BASE_URL}/api/execution/nonexistent/pause")
        assert pause_response.status_code == 400
        
        # Test resume non-existent execution
        resume_response = requests.post(f"{BASE_URL}/api/execution/nonexistent/resume")
        assert resume_response.status_code == 400
        
        # Test abort non-existent execution
        abort_response = requests.post(f"{BASE_URL}/api/execution/nonexistent/abort")
        assert abort_response.status_code == 400
        
        # Test delete non-existent agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/nonexistent")
        assert delete_response.status_code in [400, 404]