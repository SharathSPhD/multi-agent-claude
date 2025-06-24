#!/usr/bin/env python3
"""
MCP Multi-Agent System Launcher v2.1.1 - Complete Test Workflow
Enhanced launcher that starts the system and executes a full test workflow
"""

import os
import sys
import subprocess
import time
import signal
import platform
import json
import requests
from pathlib import Path
from threading import Thread
import webbrowser

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m' 
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_banner():
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════╗
║        MCP Multi-Agent System v2.1.1 - Full Test        ║
║                                                          ║
║  🤖 Load Agents & Tasks from Files                       ║
║  🔄 Execute Complete Workflow                            ║
║  🧪 Test Backend → Frontend → Testing Agents            ║
║  ⚡ Monitor Execution & Handle Stuck Agents              ║
║  📊 Real-time Progress Tracking                          ║
║  🎯 End-to-End System Validation                         ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}
""")

def check_environment():
    """Check basic environment requirements"""
    print(f"{Colors.YELLOW}🔍 Checking environment...{Colors.END}")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print(f"{Colors.RED}❌ Python 3.10+ required (found {sys.version.split()[0]}){Colors.END}")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check virtual environment
    venv_path = Path('.venv')
    if not venv_path.exists():
        print(f"{Colors.RED}❌ Virtual environment not found - run: python -m venv .venv{Colors.END}")
        return False
    print("✅ Virtual environment detected")
    
    # Check for Claude Code SDK
    try:
        from claude_code_sdk import query
        print("✅ Claude Code SDK available")
    except ImportError:
        print(f"{Colors.YELLOW}⚠️  Claude Code SDK not found - install with: uv pip install claude-code-sdk{Colors.END}")
    
    print(f"{Colors.GREEN}✅ Environment ready!{Colors.END}")
    return True

def start_backend():
    """Start FastAPI backend server"""
    print(f"\n{Colors.GREEN}🚀 Starting backend server...{Colors.END}")
    
    # Check if already running
    try:
        response = requests.get('http://localhost:8000/health', timeout=2)
        if response.status_code == 200:
            print("✅ Backend already running on http://localhost:8000")
            return None
    except:
        pass
    
    # Start uvicorn
    cmd = [sys.executable, '-m', 'uvicorn', 'main:app', 
           '--reload', '--host', '0.0.0.0', '--port', '8000']
    
    process = subprocess.Popen(cmd, cwd='backend', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("⏳ Waiting for backend to start...")
    for i in range(15):
        time.sleep(1)
        try:
            response = requests.get('http://localhost:8000/health', timeout=1)
            if response.status_code == 200:
                print("✅ Backend started successfully")
                return process
        except:
            continue
    
    print(f"{Colors.YELLOW}⚠️  Backend may still be starting...{Colors.END}")
    return process

def start_frontend():
    """Start React frontend server"""
    print(f"\n{Colors.GREEN}🚀 Starting frontend server...{Colors.END}")
    
    # Check if already running
    try:
        response = requests.get('http://localhost:3000', timeout=2)
        if response.status_code == 200:
            print("✅ Frontend already running on http://localhost:3000")
            return None
    except:
        pass
    
    # Check node_modules
    if not Path('frontend/node_modules').exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd='frontend', check=True, timeout=120)
        except Exception as e:
            print(f"{Colors.RED}❌ Frontend installation failed: {e}{Colors.END}")
            return None
    
    # Start dev server
    cmd = ['npm', 'run', 'dev']
    process = subprocess.Popen(cmd, cwd='frontend', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print("⏳ Frontend starting...")
    time.sleep(5)
    print("✅ Frontend should be available on http://localhost:3000")
    return process

def clear_existing_data():
    """Clear existing agents and tasks to ensure clean test"""
    print(f"\n{Colors.YELLOW}🧹 Clearing existing data for clean test...{Colors.END}")
    
    try:
        # Get and delete all agents
        agents_response = requests.get('http://localhost:8000/api/agents', timeout=10)
        if agents_response.status_code == 200:
            agents = agents_response.json()
            for agent in agents:
                try:
                    delete_response = requests.delete(f'http://localhost:8000/api/agents/{agent["id"]}?force=true')
                    if delete_response.status_code == 200:
                        print(f"✅ Deleted agent: {agent['name']}")
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️  Failed to delete agent {agent['name']}: {e}{Colors.END}")
        
        # Get and delete all tasks
        tasks_response = requests.get('http://localhost:8000/api/tasks', timeout=10)
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            for task in tasks:
                try:
                    delete_response = requests.delete(f'http://localhost:8000/api/tasks/{task["id"]}')
                    if delete_response.status_code == 200:
                        print(f"✅ Deleted task: {task['title']}")
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️  Failed to delete task {task['title']}: {e}{Colors.END}")
        
        print(f"✅ Database cleared for clean test")
        return True
        
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Error clearing data: {e}{Colors.END}")
        return True  # Continue anyway

def load_agents_and_tasks():
    """Load agents and tasks from project directory"""
    print(f"\n{Colors.PURPLE}📂 Loading agents and tasks from files...{Colors.END}")
    
    project_dir = "/mnt/e/Development/mcp_a2a/project_selfdevelop"
    
    try:
        # Load from directory
        response = requests.post('http://localhost:8000/api/project/load-from-directory', 
                               json={"directory": project_dir, "force_reload": True},
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Loaded {result['agents_loaded']} agents and {result['tasks_loaded']} tasks")
            if result['errors']:
                print(f"{Colors.YELLOW}⚠️  {len(result['errors'])} errors occurred{Colors.END}")
                for error in result['errors'][:3]:  # Show first 3 errors
                    print(f"   - {error}")
            return True
        else:
            print(f"{Colors.RED}❌ Failed to load files: {response.status_code}{Colors.END}")
            print(f"Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Error loading files: {e}{Colors.END}")
        return False

def get_system_status():
    """Get current system status"""
    try:
        # Get agents
        agents_response = requests.get('http://localhost:8000/api/agents', timeout=5)
        agents = agents_response.json() if agents_response.status_code == 200 else []
        
        # Get tasks
        tasks_response = requests.get('http://localhost:8000/api/tasks', timeout=5)
        tasks = tasks_response.json() if tasks_response.status_code == 200 else []
        
        # Get executions
        exec_response = requests.get('http://localhost:8000/api/execution/status', timeout=5)
        executions = exec_response.json() if exec_response.status_code == 200 else []
        
        # Get workflow patterns
        patterns_response = requests.get('http://localhost:8000/api/workflows/patterns', timeout=5)
        patterns = patterns_response.json() if patterns_response.status_code == 200 else []
        
        return {
            'agents': agents,
            'tasks': tasks,
            'executions': executions,
            'patterns': patterns
        }
    except Exception as e:
        print(f"{Colors.RED}❌ Error getting system status: {e}{Colors.END}")
        return None

def create_and_execute_tasks():
    """Create a workflow pattern for testing"""
    print(f"\n{Colors.CYAN}🔄 Creating test workflow pattern...{Colors.END}")
    
    try:
        # Get current agents and tasks
        status = get_system_status()
        if not status:
            return None
        
        agents = status['agents']
        tasks = status['tasks']
        
        if len(agents) < 3 or len(tasks) < 3:
            print(f"{Colors.RED}❌ Need at least 3 agents and 3 tasks (found {len(agents)} agents, {len(tasks)} tasks){Colors.END}")
            return None
        
        # Analyze workflow requirements
        analyze_data = {
            "agents_ids": [agent['id'] for agent in agents],
            "task_ids": [task['id'] for task in tasks],
            "user_objective": "Test complete multi-agent workflow: Backend metrics endpoint → Frontend dashboard → Comprehensive testing"
        }
        
        analyze_response = requests.post('http://localhost:8000/api/workflows/analyze', 
                                       json=analyze_data, timeout=30)
        
        if analyze_response.status_code != 200:
            print(f"{Colors.RED}❌ Workflow analysis failed: {analyze_response.status_code}{Colors.END}")
            return None
        
        analysis = analyze_response.json()
        print(f"✅ Workflow analysis complete - recommended: {analysis['recommended_workflow']}")
        
        # Create workflow pattern
        pattern_data = {
            "name": "Complete System Test Workflow",
            "description": "End-to-end test: Backend API → Frontend Component → Testing Suite",
            "workflow_type": analysis['recommended_workflow'],
            "agent_ids": [agent['id'] for agent in agents],
            "task_ids": [task['id'] for task in tasks],
            "user_objective": analyze_data['user_objective']
        }
        
        pattern_response = requests.post('http://localhost:8000/api/workflows/patterns',
                                       json=pattern_data, timeout=30)
        
        if pattern_response.status_code == 200:
            pattern = pattern_response.json()
            print(f"✅ Workflow pattern created: {pattern['name']}")
            return pattern
        else:
            print(f"{Colors.RED}❌ Pattern creation failed: {pattern_response.status_code}{Colors.END}")
            return None
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error creating workflow: {e}{Colors.END}")
        return None

def execute_workflow_pattern(pattern):
    """Execute the workflow pattern"""
    print(f"\n{Colors.GREEN}⚡ Executing workflow pattern...{Colors.END}")
    
    try:
        # Execute workflow
        execute_response = requests.post(f'http://localhost:8000/api/workflows/execute/{pattern["id"]}',
                                       json={"context": {"test_mode": True}}, timeout=30)
        
        if execute_response.status_code == 200:
            execution = execute_response.json()
            print(f"✅ Workflow execution started: {execution['id']}")
            return execution['id']
        else:
            print(f"{Colors.RED}❌ Workflow execution failed: {execute_response.status_code}{Colors.END}")
            return None
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error executing workflow: {e}{Colors.END}")
        return None

def monitor_execution(execution_id, max_duration=600):
    """Monitor workflow execution with stuck agent detection"""
    print(f"\n{Colors.YELLOW}📊 Monitoring execution (max {max_duration}s)...{Colors.END}")
    
    start_time = time.time()
    last_status_check = {}
    stuck_detection_threshold = 120  # 2 minutes without status change
    
    while time.time() - start_time < max_duration:
        try:
            # Get execution status
            status = get_system_status()
            if not status:
                print(f"{Colors.RED}❌ Failed to get system status{Colors.END}")
                time.sleep(10)
                continue
            
            executions = status['executions']
            agents = status['agents']
            
            # Find our execution
            current_execution = None
            for exec in executions:
                if exec.get('id') == execution_id:
                    current_execution = exec
                    break
            
            if not current_execution:
                print(f"{Colors.GREEN}✅ Execution completed or not found{Colors.END}")
                break
            
            # Check agent statuses
            executing_agents = [agent for agent in agents if agent['status'] == 'executing']
            idle_agents = [agent for agent in agents if agent['status'] == 'idle']
            
            print(f"📊 Status: {len(executing_agents)} executing, {len(idle_agents)} idle agents")
            
            # Detect stuck agents
            current_time = time.time()
            for agent in executing_agents:
                agent_id = agent['id']
                agent_name = agent['name']
                
                if agent_id not in last_status_check:
                    last_status_check[agent_id] = current_time
                    print(f"🔄 {agent_name} started executing")
                else:
                    time_stuck = current_time - last_status_check[agent_id]
                    if time_stuck > stuck_detection_threshold:
                        print(f"{Colors.RED}⚠️  {agent_name} appears stuck ({time_stuck:.1f}s) - attempting recovery{Colors.END}")
                        
                        # Try to abort stuck agent execution
                        try:
                            # Find executions for this agent and cancel them
                            for exec in executions:
                                if exec.get('agent_id') == agent_id and exec.get('status') == 'running':
                                    cancel_response = requests.post(f'http://localhost:8000/api/execution/{exec["id"]}/abort')
                                    if cancel_response.status_code == 200:
                                        print(f"✅ Aborted stuck execution for {agent_name}")
                                    else:
                                        print(f"{Colors.YELLOW}⚠️  Failed to abort execution for {agent_name}{Colors.END}")
                        except Exception as e:
                            print(f"{Colors.YELLOW}⚠️  Recovery attempt failed for {agent_name}: {e}{Colors.END}")
                        
                        # Reset the timer
                        last_status_check[agent_id] = current_time
            
            # Update timers for agents that changed status
            for agent in agents:
                agent_id = agent['id']
                if agent['status'] != 'executing' and agent_id in last_status_check:
                    del last_status_check[agent_id]
                elif agent['status'] == 'executing' and agent_id not in last_status_check:
                    last_status_check[agent_id] = current_time
            
            # Show progress
            if executing_agents:
                for agent in executing_agents:
                    print(f"  🔄 {agent['name']}: {agent['status']}")
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Monitoring error: {e}{Colors.END}")
            time.sleep(10)
    
    # Final status check
    print(f"\n{Colors.BLUE}📋 Final system status:{Colors.END}")
    final_status = get_system_status()
    if final_status:
        executing_agents = [agent for agent in final_status['agents'] if agent['status'] == 'executing']
        if executing_agents:
            print(f"{Colors.YELLOW}⚠️  {len(executing_agents)} agents still executing{Colors.END}")
            for agent in executing_agents:
                print(f"  - {agent['name']}: {agent['status']}")
        else:
            print(f"{Colors.GREEN}✅ All agents completed execution{Colors.END}")

def cleanup_and_exit(backend_process, frontend_process):
    """Clean shutdown of services"""
    print(f"\n{Colors.YELLOW}🛑 Shutting down services...{Colors.END}")
    
    # Kill backend processes
    try:
        if backend_process:
            backend_process.terminate()
            backend_process.wait(timeout=5)
        else:
            subprocess.run(['pkill', '-f', 'uvicorn'], stderr=subprocess.DEVNULL)
        print("✅ Backend stopped")
    except:
        print("⚠️  Backend process cleanup")
    
    # Kill frontend processes  
    try:
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        else:
            subprocess.run(['pkill', '-f', 'npm.*dev'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'vite'], stderr=subprocess.DEVNULL)
        print("✅ Frontend stopped")
    except:
        print("⚠️  Frontend process cleanup")
    
    print(f"{Colors.GREEN}👋 Test completed!{Colors.END}")

def main():
    """Main test workflow function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start services
        backend_process = start_backend()
        time.sleep(3)
        frontend_process = start_frontend()
        time.sleep(5)
        
        # Wait for services to be ready
        print(f"\n{Colors.BLUE}⏳ Waiting for services to be fully ready...{Colors.END}")
        time.sleep(10)
        
        # Clear existing data for clean test
        clear_existing_data()
        time.sleep(2)
        
        # Load agents and tasks
        if not load_agents_and_tasks():
            print(f"{Colors.RED}❌ Failed to load agents and tasks - exiting{Colors.END}")
            sys.exit(1)
        
        time.sleep(3)
        
        # Create workflow pattern
        pattern = create_and_execute_tasks()
        if not pattern:
            print(f"{Colors.RED}❌ Failed to create workflow pattern - exiting{Colors.END}")
            sys.exit(1)
        
        # Execute workflow
        execution_id = execute_workflow_pattern(pattern)
        if execution_id:
            monitor_execution(execution_id)
        
        # Show final results
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Multi-Agent System Test Completed!{Colors.END}")
        print(f"{Colors.BLUE}📱 Frontend: http://localhost:3000{Colors.END}")
        print(f"{Colors.BLUE}🔧 Backend: http://localhost:8000{Colors.END}")
        print(f"{Colors.BLUE}📚 API Docs: http://localhost:8000/docs{Colors.END}")
        
        # Check project_selfdevelop for generated files
        output_dir = Path("project_selfdevelop")
        if output_dir.exists():
            generated_files = list(output_dir.glob("*.py")) + list(output_dir.glob("*.tsx")) + list(output_dir.glob("*.test.*"))
            if generated_files:
                print(f"\n{Colors.GREEN}📄 Generated files in project_selfdevelop:{Colors.END}")
                for file in generated_files[:10]:  # Show first 10 files
                    print(f"  - {file.name}")
                if len(generated_files) > 10:
                    print(f"  ... and {len(generated_files) - 10} more files")
        
        print(f"\n{Colors.YELLOW}Press Ctrl+C to stop services{Colors.END}")
        
        # Keep running for inspection
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        cleanup_and_exit(backend_process, frontend_process)
    except Exception as e:
        print(f"{Colors.RED}❌ Test failed: {e}{Colors.END}")
        cleanup_and_exit(backend_process, frontend_process)
        sys.exit(1)

if __name__ == "__main__":
    main()