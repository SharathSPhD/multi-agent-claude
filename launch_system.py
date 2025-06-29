#!/usr/bin/env python3
"""
MCP Multi-Agent System Launcher v2.2
Enhanced launcher with database cleanup and system health checks
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
║           MCP Multi-Agent System v2.2 Launcher          ║
║                                                          ║
║  🤖 End-to-End Workflow Execution System                ║
║  🌐 React Web Interface with Full Controls               ║
║  ⚡ Multi-Agent Coordination & Task Distribution         ║
║  💾 Database Persistence & State Management              ║
║  🧹 Automatic Cleanup & Health Monitoring               ║
║  🗑️ Proper Workflow Deletion vs Abort/Cancel            ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}
""")

def cleanup_database():
    """Clean up stale workflow executions on startup"""
    print(f"{Colors.YELLOW}🧹 Cleaning up stale workflow executions...{Colors.END}")
    
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        db_path = 'mcp_multiagent.db'
        if not Path(db_path).exists():
            print("✅ No database found - will be created on first use")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if workflow_executions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_executions'")
        if not cursor.fetchone():
            print("✅ No workflow executions table - clean state")
            conn.close()
            return
        
        # Clean up stale executions (older than 1 hour or stuck in running state)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        # Delete old completed/failed/cancelled executions
        cursor.execute('DELETE FROM workflow_executions WHERE status IN ("completed", "failed") AND start_time < ?', (one_hour_ago,))
        old_deleted = cursor.rowcount
        
        # Abort stuck executions (running/pending for > 1 hour)
        cursor.execute('UPDATE workflow_executions SET status = "aborted", end_time = ?, error_details = ? WHERE status IN ("running", "pending", "in_progress") AND start_time < ?',
                      (datetime.now().isoformat(), "Auto-aborted: System restart cleanup", one_hour_ago))
        stuck_aborted = cursor.rowcount
        
        # Clean up regular tasks table as well
        tasks_cleaned = 0
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if cursor.fetchone():
            # Cancel any stuck tasks (IN_PROGRESS, PENDING, RUNNING)
            cursor.execute('UPDATE tasks SET status = "CANCELLED" WHERE status IN ("IN_PROGRESS", "PENDING", "RUNNING")')
            tasks_cleaned = cursor.rowcount
        
        conn.commit()
        
        # Report cleanup
        cursor.execute('SELECT COUNT(*) FROM workflow_executions')
        remaining = cursor.fetchone()[0]
        
        print(f"✅ Database cleanup complete:")
        print(f"   - Deleted {old_deleted} old completed/failed workflow executions")
        print(f"   - Aborted {stuck_aborted} stuck workflow executions")
        print(f"   - Cancelled {tasks_cleaned} stuck tasks")  
        print(f"   - Remaining workflow executions: {remaining}")
        
        conn.close()
        
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Database cleanup error: {e}{Colors.END}")

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
    
    # Check if we're in activated venv
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"{Colors.YELLOW}⚠️  Virtual environment not activated - run: source .venv/bin/activate{Colors.END}")
    
    # Check for Claude Code SDK
    try:
        from claude_code_sdk import query
        print("✅ Claude Code SDK available")
    except ImportError:
        print(f"{Colors.YELLOW}⚠️  Claude Code SDK not found - install with: uv pip install claude-code-sdk{Colors.END}")
    
    # Check database and clean up
    cleanup_database()
    
    print(f"{Colors.GREEN}✅ Environment ready!{Colors.END}")
    return True

def start_backend():
    """Start FastAPI backend server"""
    print(f"\n{Colors.GREEN}🚀 Starting backend server...{Colors.END}")
    
    # Check if already running
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=2)
        if response.status_code == 200:
            print("✅ Backend already running on http://localhost:8000")
            return None
    except:
        pass
    
    # Start uvicorn
    cmd = [sys.executable, '-m', 'uvicorn', 'main:app', 
           '--reload', '--host', '0.0.0.0', '--port', '8000']
    
    process = subprocess.Popen(cmd, cwd='backend')
    
    # Wait for startup
    print("⏳ Waiting for backend to start...")
    for i in range(10):
        time.sleep(1)
        try:
            import requests
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
        import requests
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
    process = subprocess.Popen(cmd, cwd='frontend')
    
    print("⏳ Frontend starting...")
    time.sleep(3)
    print("✅ Frontend should be available on http://localhost:3000")
    return process

def quick_health_check():
    """Quick health check of services"""
    print(f"\n{Colors.BLUE}🔍 Quick health check...{Colors.END}")
    
    try:
        import requests
        
        # Backend health
        try:
            response = requests.get("http://localhost:8000/health", timeout=3)
            if response.status_code == 200:
                print("✅ Backend API responding")
            else:
                print(f"⚠️  Backend responded with: {response.status_code}")
        except:
            print("⚠️  Backend not responding")
        
        # Frontend health
        try:
            response = requests.get("http://localhost:3000", timeout=3)
            if response.status_code == 200:
                print("✅ Frontend responding")
            else:
                print(f"⚠️  Frontend responded with: {response.status_code}")
        except:
            print("⚠️  Frontend not responding")
    
    except ImportError:
        print("⚠️  Cannot check - requests library not available")

def cleanup_and_exit(backend_process, frontend_process):
    """Clean shutdown of services and workflow cleanup"""
    print(f"\n{Colors.YELLOW}🛑 Shutting down services...{Colors.END}")
    
    # Clean up any running workflow executions in database
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('mcp_multiagent.db')
        cursor = conn.cursor()
        
        # Check for running executions and abort them
        cursor.execute('SELECT id FROM workflow_executions WHERE status IN ("running", "pending", "in_progress")')
        running_executions = cursor.fetchall()
        
        if running_executions:
            print(f"🧹 Aborting {len(running_executions)} running workflow executions...")
            cursor.execute('UPDATE workflow_executions SET status = "aborted", end_time = ?, error_details = ? WHERE status IN ("running", "pending", "in_progress")',
                          (datetime.now().isoformat(), "System shutdown"))
            conn.commit()
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Database cleanup error: {e}")
    
    # Kill any orphaned Claude CLI processes (excluding this session)
    try:
        # Get current process to exclude it
        current_pid = os.getpid()
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        claude_processes = []
        
        for line in result.stdout.split('\n'):
            if 'claude' in line and 'claude-code' not in line and str(current_pid) not in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        claude_processes.append(pid)
                    except ValueError:
                        continue
        
        if claude_processes:
            print(f"🧹 Cleaning up {len(claude_processes)} orphaned Claude CLI processes...")
            for pid in claude_processes:
                try:
                    subprocess.run(['kill', str(pid)], stderr=subprocess.DEVNULL)
                except:
                    pass
        
    except Exception as e:
        print(f"⚠️  Claude process cleanup: {e}")
    
    # Kill backend processes
    try:
        if backend_process:
            backend_process.terminate()
            backend_process.wait(timeout=5)
        else:
            # Kill any uvicorn processes
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
            # Kill any vite/npm dev processes
            subprocess.run(['pkill', '-f', 'npm.*dev'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'vite'], stderr=subprocess.DEVNULL)
        print("✅ Frontend stopped")
    except:
        print("⚠️  Frontend process cleanup")
    
    print(f"{Colors.GREEN}👋 Goodbye!{Colors.END}")

def main():
    """Main launcher function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start services
        backend_process = start_backend()
        frontend_process = start_frontend()
        
        # Quick health check
        time.sleep(2)
        quick_health_check()
        
        # Show access info with WSL-aware URLs
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 System Ready!{Colors.END}")
        
        # Get WSL IP for display
        wsl_ip = None
        if platform.system() == "Linux" and "microsoft" in platform.uname().release.lower():
            try:
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                wsl_ip = result.stdout.strip().split()[0]
                if wsl_ip and not wsl_ip.startswith('127.'):
                    print(f"📱 Frontend: {Colors.BLUE}http://{wsl_ip}:3000{Colors.END} (Windows browser)")
                    print(f"🔧 Backend API: {Colors.BLUE}http://{wsl_ip}:8000{Colors.END} (Windows)")
                    print(f"📚 API Docs: {Colors.BLUE}http://{wsl_ip}:8000/docs{Colors.END} (Windows)")
                    print(f"🐧 Local URLs: http://localhost:3000 | http://localhost:8000 (WSL only)")
                else:
                    wsl_ip = None
            except:
                wsl_ip = None
        
        if not wsl_ip:
            print(f"📱 Frontend: {Colors.BLUE}http://localhost:3000{Colors.END}")
            print(f"🔧 Backend API: {Colors.BLUE}http://localhost:8000{Colors.END}")
            print(f"📚 API Docs: {Colors.BLUE}http://localhost:8000/docs{Colors.END}")
        
        print(f"\n{Colors.YELLOW}Press Ctrl+C to stop all services{Colors.END}")
        
        # Open browser (WSL-friendly)
        try:
            if platform.system() == "Linux" and "microsoft" in platform.uname().release.lower():
                # WSL environment - get WSL IP for Windows browser
                try:
                    import socket
                    # Get WSL IP address
                    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                    wsl_ip = result.stdout.strip().split()[0]
                    
                    if wsl_ip and not wsl_ip.startswith('127.'):
                        url = f'http://{wsl_ip}:3000'
                        subprocess.run(['cmd.exe', '/c', 'start', url], 
                                     stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                        print(f"{Colors.GREEN}🌐 Opening Windows browser: {url}{Colors.END}")
                    else:
                        print(f"{Colors.YELLOW}💡 Open in Windows browser: http://[WSL_IP]:3000{Colors.END}")
                        print(f"💡 Find WSL IP with: hostname -I{Colors.END}")
                except Exception:
                    print(f"{Colors.YELLOW}💡 Open in Windows browser: http://[WSL_IP]:3000{Colors.END}")
            else:
                webbrowser.open('http://localhost:3000')
        except Exception as e:
            print(f"{Colors.YELLOW}💡 Manual browser: http://localhost:3000{Colors.END}")
        
        # Keep running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        cleanup_and_exit(backend_process, frontend_process)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        cleanup_and_exit(backend_process, frontend_process)
        sys.exit(1)

if __name__ == "__main__":
    main()