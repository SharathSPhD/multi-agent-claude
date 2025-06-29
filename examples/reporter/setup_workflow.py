#!/usr/bin/env python3
"""
Setup script to create agents and tasks for the Claude Code research & reporting workflow.
Run this script to automatically create the agents and tasks in the system.
"""

import json
import requests
import sys
import os

# API Configuration
API_BASE = "http://localhost:8000"

def load_json_file(filepath):
    """Load and return JSON data from file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def create_agent(agent_data):
    """Create an agent via API."""
    try:
        # Convert JSON data to API format
        api_data = {
            "name": agent_data["name"],
            "role": agent_data["role"], 
            "description": agent_data["description"],
            "capabilities": agent_data["capabilities"],
            "tools": agent_data["tools"],
            "system_prompt": agent_data["system_prompt"],
            "objectives": agent_data["objectives"],
            "constraints": agent_data["constraints"],
            "status": "idle"
        }
        
        response = requests.post(f"{API_BASE}/api/agents", json=api_data)
        if response.status_code in [200, 201]:
            result = response.json()
            agent_id = result["id"]
            print(f"✅ Created agent: {agent_data['name']} (ID: {agent_id[:8]})")
            return agent_id
        else:
            print(f"❌ Failed to create agent {agent_data['name']}: Status {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating agent {agent_data['name']}: {e}")
        return None

def create_task(task_data):
    """Create a task via API."""
    try:
        # Convert JSON data to API format
        api_data = {
            "title": task_data["title"],
            "description": task_data["description"],
            "priority": task_data["priority"],
            "requirements": task_data["requirements"],
            "expected_output": task_data["expected_output"],
            "dependencies": task_data.get("dependencies", []),
            "estimated_duration": task_data.get("estimated_duration", "15 minutes"),
            "status": "pending"
        }
        
        response = requests.post(f"{API_BASE}/api/tasks", json=api_data)
        if response.status_code in [200, 201]:
            result = response.json()
            task_id = result["id"]
            print(f"✅ Created task: {task_data['title']} (ID: {task_id[:8]})")
            return task_id
        else:
            print(f"❌ Failed to create task {task_data['title']}: Status {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating task {task_data['title']}: {e}")
        return None

def main():
    """Main setup function."""
    print("🚀 Setting up Claude Code Research & Reporting Workflow")
    print("=" * 60)
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load agent data
    print("\n📋 Loading agent definitions...")
    agent1_data = load_json_file(os.path.join(current_dir, "agent1_info_gatherer.json"))
    agent2_data = load_json_file(os.path.join(current_dir, "agent2_report_writer.json"))
    
    if not agent1_data or not agent2_data:
        print("❌ Failed to load agent definitions")
        return False
    
    # Load task data  
    print("\n📋 Loading task definitions...")
    task1_data = load_json_file(os.path.join(current_dir, "task1_gather_claude_info.json"))
    task2_data = load_json_file(os.path.join(current_dir, "task2_create_claude_report.json"))
    
    if not task1_data or not task2_data:
        print("❌ Failed to load task definitions")
        return False
    
    # Create agents
    print("\n🤖 Creating agents...")
    agent1_id = create_agent(agent1_data)
    agent2_id = create_agent(agent2_data)
    
    if not agent1_id or not agent2_id:
        print("❌ Failed to create agents")
        return False
    
    # Create tasks
    print("\n📝 Creating tasks...")
    task1_id = create_task(task1_data)
    task2_id = create_task(task2_data)
    
    if not task1_id or not task2_id:
        print("❌ Failed to create tasks")
        return False
    
    print("\n🎉 Setup Complete!")
    print("=" * 60)
    print(f"Agent 1 (InfoGatherer): {agent1_id[:8]}")
    print(f"Agent 2 (ReportWriter): {agent2_id[:8]}")
    print(f"Task 1 (Gather Info): {task1_id[:8]}")
    print(f"Task 2 (Create Report): {task2_id[:8]}")
    print("\nNext steps:")
    print("1. Go to the Frontend (http://localhost:3000)")
    print("2. Navigate to Advanced Orchestrator")
    print("3. Create a new workflow pattern:")
    print("   - Name: Claude Code Research & Reporting")
    print("   - Type: Sequential")
    print("   - Agents: Select InfoGatherer, then ReportWriter (in order)")
    print("   - Tasks: Select 'Gather Claude Code Information', then 'Create Professional Claude Code Report' (in order)")
    print("   - Objective: Research Claude Code and create professional report")
    print("   - Project Directory: /mnt/e/Development/mcp_a2a/examples/reporter")
    print("4. Execute the workflow")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)