#!/usr/bin/env python3
"""
Execute workflow using available agent
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def execute_with_available_agent():
    """Execute workflow with available agent"""
    print("🎯 Executing Workflow with Available Agent")
    print("=" * 50)
    
    # Get agents
    response = requests.get(f"{BASE_URL}/agents")
    agents = response.json()
    
    # Find available agent (not busy)
    available_agent = None
    for agent in agents:
        if agent['status'] != 'executing':
            available_agent = agent
            print(f"✅ Found available agent: {agent['name']} (status: {agent['status']})")
            break
    
    if not available_agent:
        print("❌ No available agents")
        return
    
    # Get existing tasks
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()
    
    if not tasks:
        print("❌ No tasks available")
        return
    
    # Use first task
    task = tasks[0]
    print(f"📋 Using task: {task['title']}")
    
    # Execute with available agent
    execution_request = {
        "task_id": task["id"],
        "agent_ids": [available_agent["id"]],
        "execution_mode": "collaborative",
        "monitoring_enabled": True
    }
    
    print(f"\n🚀 Starting execution...")
    print(f"   Agent: {available_agent['name']}")
    print(f"   Task: {task['title']}")
    
    response = requests.post(f"{BASE_URL}/execution/start", json=execution_request, timeout=30)
    
    if response.status_code == 200:
        execution = response.json()
        execution_id = execution["execution_id"]
        print(f"✅ Execution started: {execution_id}")
        
        # Monitor for 2 minutes
        print("\n⏳ Monitoring real-time execution...")
        for i in range(12):
            time.sleep(10)
            try:
                status_response = requests.get(f"{BASE_URL}/execution/{execution_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_status = status.get('status', 'unknown')
                    print(f"   [{i*10:3d}s] Status: {current_status}")
                    
                    # Show agent response if available
                    if status.get('agent_response'):
                        agent_resp = status['agent_response']
                        if agent_resp.get('summary'):
                            print(f"          Summary: {agent_resp['summary'][:80]}...")
                    
                    if current_status in ["completed", "failed", "cancelled"]:
                        print(f"\n🏁 Execution finished: {current_status}")
                        
                        # Show final results
                        if status.get('results'):
                            print(f"\n📊 Results:")
                            print(f"   Output: {str(status['results'])[:200]}...")
                        
                        if status.get('agent_response'):
                            print(f"\n🤖 Agent Response:")
                            agent_resp = status['agent_response']
                            if agent_resp.get('summary'):
                                print(f"   Summary: {agent_resp['summary']}")
                            if agent_resp.get('files_created'):
                                print(f"   Files Created: {len(agent_resp['files_created'])}")
                        
                        return status
                else:
                    print(f"   ⚠️ Status check failed: {status_response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        
        print("⏰ Monitoring complete")
        return {"execution_id": execution_id, "status": "monitored"}
    else:
        print(f"❌ Failed to start execution: {response.text}")
        return None

if __name__ == "__main__":
    result = execute_with_available_agent()
    if result:
        print(f"\n✅ Workflow execution completed successfully!")
        print(f"📋 Final status: {result.get('status', 'unknown')}")
    else:
        print("\n❌ Workflow execution failed")