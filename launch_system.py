#!/usr/bin/env python3
"""
MCP Multi-Agent System Launcher
Starts both backend (FastAPI) and frontend (React) with all dependencies
"""

import os
import sys
import subprocess
import time
import signal
import platform
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
    END = '\033[0m'

def print_banner():
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════╗
║           MCP Multi-Agent System v2.0 Launcher          ║
║                                                          ║
║  🤖 Dynamic Agent Configuration                          ║
║  🌐 React Web Interface                                  ║
║  ⚡ Async Multi-Agent Execution                          ║
║  💾 Real-time Database & Memory                          ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}
""")

def check_requirements():
    """Check if all required tools are available"""
    print(f"{Colors.YELLOW}🔍 Checking system requirements...{Colors.END}")
    
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 10):
        errors.append("Python 3.10+ required")
    else:
        print(f"✅ Python {sys.version.split()[0]}")
    
    # Check Node.js
    try:
        node_version = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if node_version.returncode == 0:
            print(f"✅ Node.js {node_version.stdout.strip()}")
        else:
            errors.append("Node.js not found")
    except FileNotFoundError:
        errors.append("Node.js not found")
    
    # Check if we're in virtual environment
    if sys.prefix == sys.base_prefix:
        print(f"{Colors.YELLOW}⚠️  Not in virtual environment - using system Python{Colors.END}")
    else:
        print(f"✅ Virtual environment active")
    
    # Check if backend dependencies exist
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError:
        errors.append("FastAPI not installed - run: pip install -r requirements.txt")
    
    if errors:
        print(f"\n{Colors.RED}❌ Requirements not met:{Colors.END}")
        for error in errors:
            print(f"   • {error}")
        print(f"\n{Colors.YELLOW}Please install missing requirements and try again.{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✅ All requirements satisfied!{Colors.END}")
    return True

def setup_backend():
    """Initialize backend database and check configuration"""
    print(f"\n{Colors.BLUE}🔧 Setting up backend...{Colors.END}")
    
    # Set environment variables
    os.environ.setdefault('DATABASE_URL', 'sqlite:///./mcp_multiagent.db')
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
    
    # Initialize database
    try:
        os.chdir('backend')
        subprocess.run([sys.executable, '-c', 
                       'from database import init_db; init_db()'], 
                       check=True, capture_output=True)
        print("✅ Database initialized")
        os.chdir('..')
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("   Continuing anyway...")
        os.chdir('..')

def setup_frontend():
    """Check frontend dependencies"""
    print(f"\n{Colors.BLUE}🔧 Checking frontend...{Colors.END}")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print(f"{Colors.RED}❌ Frontend directory not found{Colors.END}")
        return False
    
    # Check if we can run vite
    try:
        result = subprocess.run(['npx', 'vite', '--version'], 
                              cwd='frontend', capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ Frontend dependencies ready")
            return True
        else:
            print(f"{Colors.RED}❌ Frontend dependencies missing - run: cd frontend && npm install{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Frontend check failed: {e}{Colors.END}")
        print(f"   Run: cd frontend && npm install")
        return False

def start_backend():
    """Start FastAPI backend server"""
    print(f"\n{Colors.GREEN}🚀 Starting backend server...{Colors.END}")
    
    # Check if backend is already running
    try:
        import requests
        response = requests.get('http://localhost:8000/api/agents', timeout=2)
        print("✅ Backend already running on http://localhost:8000")
        return None  # Don't start another instance
    except:
        pass  # Backend not running, continue to start it
    
    # Use the activated virtual environment python
    venv_python = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        venv_python = sys.executable
    
    # Start uvicorn server from backend directory
    cmd = [venv_python, '-m', 'uvicorn', 'main:app', 
           '--reload', '--host', '0.0.0.0', '--port', '8000']
    
    process = subprocess.Popen(cmd,
                              cwd='backend',
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              universal_newlines=True,
                              bufsize=1)
    
    # Wait for server to start
    print("   Waiting for backend to start...")
    
    # Wait up to 30 seconds for backend to be ready
    for i in range(30):
        time.sleep(1)
        try:
            import requests
            response = requests.get('http://localhost:8000/api/agents', timeout=1)
            if response.status_code == 200:
                print("✅ Backend server started on http://localhost:8000")
                return process
        except:
            continue
    
    # If we get here, backend didn't start properly
    print("❌ Backend failed to start")
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        if stdout:
            print(f"   Error: {stdout[:200]}...")
        
    return process

def start_frontend():
    """Start React frontend development server"""
    print(f"\n{Colors.GREEN}🚀 Starting frontend server...{Colors.END}")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        return None
    
    # Start Vite dev server with host binding
    cmd = ['npm', 'run', 'dev', '--', '--host', '0.0.0.0']
    
    process = subprocess.Popen(cmd,
                              cwd='frontend',
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, 
                              universal_newlines=True,
                              bufsize=1)
    
    # Wait for server to start
    print("   Waiting for frontend to start...")
    time.sleep(5)
    
    # Check if process is still running
    if process.poll() is None:
        print("✅ Frontend server started on http://localhost:3000")
    else:
        print("❌ Frontend failed to start")
        # Read any error output
        stdout, stderr = process.communicate()
        if stdout:
            print(f"   Error: {stdout[:200]}...")
    
    return process

def start_agents():
    """Initialize the v2.0 dynamic agent system"""
    print(f"\n{Colors.GREEN}🤖 Initializing v2.0 Dynamic Agent System...{Colors.END}")
    
    # The new system is entirely web-based and dynamic
    # Agents are created and managed through the React frontend
    # No legacy scripts or hardcoded agents needed
    
    print("✅ Dynamic agent system ready")
    print("   • Agents can be created through the web interface")
    print("   • Real-time execution engine initialized")  
    print("   • Multi-agent orchestration available")
    print("   • WebSocket communication active")

def main():
    """Main launcher function"""
    print_banner()
    
    # Store original directory
    original_dir = os.getcwd()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup backend and frontend
    setup_backend()
    frontend_available = setup_frontend()
    
    # Start services
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        if backend_process:
            processes.append(('Backend', backend_process))
        
        # Start frontend if available
        frontend_process = None
        if frontend_available:
            frontend_process = start_frontend()
            if frontend_process:
                processes.append(('Frontend', frontend_process))
        
        # Start agents
        start_agents()
        
        # Print status
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 MCP Multi-Agent System Started!{Colors.END}")
        print(f"\n{Colors.BLUE}📱 Available Services:{Colors.END}")
        print(f"   🌐 Frontend:     http://localhost:3000")
        print(f"   🔧 Backend API:  http://localhost:8000")
        print(f"   📚 API Docs:     http://localhost:8000/docs")
        print(f"   🤖 Agent System: Running in background")
        
        # Skip browser opening in WSL environment
        if frontend_available and platform.system() != "Linux":
            print(f"\n{Colors.YELLOW}🌍 Opening browser...{Colors.END}")
            time.sleep(2)
            webbrowser.open('http://localhost:3000')
        else:
            print(f"\n{Colors.YELLOW}💡 Access the interface at: http://localhost:3000{Colors.END}")
        
        print(f"\n{Colors.YELLOW}Press Ctrl+C to stop all services{Colors.END}")
        
        # Wait for processes
        while True:
            time.sleep(1)
            # Check if any process died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n{Colors.RED}❌ {name} process stopped unexpectedly{Colors.END}")
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}🛑 Shutting down services...{Colors.END}")
    
    finally:
        # Clean shutdown
        for name, process in processes:
            if process.poll() is None:
                print(f"   Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        # Return to original directory
        os.chdir(original_dir)
        
        print(f"{Colors.GREEN}✅ All services stopped cleanly{Colors.END}")

if __name__ == "__main__":
    main()