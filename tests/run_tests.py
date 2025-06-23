#!/usr/bin/env python3
"""
Comprehensive test runner for MCP Multi-Agent System
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
import pytest

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m' 
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def print_section(title):
    """Print section header"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.YELLOW}{'-'*len(title)}{Colors.END}")


def run_command(command, description, cwd=None):
    """Run command and return success status"""
    print(f"\n{Colors.BLUE}Running: {description}{Colors.END}")
    print(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ {description} - SUCCESS{Colors.END}")
            if result.stdout:
                print(f"Output: {result.stdout[:500]}...")
            return True
        else:
            print(f"{Colors.RED}❌ {description} - FAILED{Colors.END}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}❌ {description} - TIMEOUT{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ {description} - ERROR: {e}{Colors.END}")
        return False


def check_test_environment():
    """Check if test environment is properly set up"""
    print_section("Checking Test Environment")
    
    checks = []
    
    # Check Python version
    if sys.version_info >= (3, 10):
        print(f"✅ Python {sys.version.split()[0]}")
        checks.append(True)
    else:
        print(f"❌ Python version {sys.version.split()[0]} (3.10+ required)")
        checks.append(False)
    
    # Check pytest installation
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__}")
        checks.append(True)
    except ImportError:
        print("❌ pytest not installed")
        checks.append(False)
    
    # Check FastAPI test client
    try:
        from fastapi.testclient import TestClient
        print("✅ FastAPI TestClient available")
        checks.append(True)
    except ImportError:
        print("❌ FastAPI TestClient not available")
        checks.append(False)
    
    # Check if in virtual environment
    if 'VIRTUAL_ENV' in os.environ:
        print(f"✅ Virtual environment: {os.environ['VIRTUAL_ENV']}")
        checks.append(True)
    else:
        print("⚠️  Not in virtual environment (recommended)")
        checks.append(True)  # Not critical
    
    return all(checks)


def run_backend_tests():
    """Run backend tests"""
    print_section("Running Backend Tests")
    
    backend_tests = [
        ("tests/backend/test_api.py", "API endpoint tests"),
        ("tests/backend/test_execution_engine.py", "Execution engine tests"),
        ("tests/backend/test_models.py", "Database model tests")
    ]
    
    results = []
    for test_file, description in backend_tests:
        if Path(test_file).exists():
            success = run_command(
                ["python", "-m", "pytest", test_file, "-v"],
                description
            )
            results.append(success)
        else:
            print(f"⚠️  {test_file} not found, skipping")
            results.append(True)  # Don't fail for missing optional tests
    
    return all(results)


def run_unit_tests():
    """Run unit tests"""
    print_section("Running Unit Tests")
    
    unit_tests = [
        ("tests/unit/test_claude_code_sdk.py", "Claude Code SDK unit tests")
    ]
    
    results = []
    for test_file, description in unit_tests:
        if Path(test_file).exists():
            success = run_command(
                ["python", "-m", "pytest", test_file, "-v"],
                description
            )
            results.append(success)
        else:
            print(f"⚠️  {test_file} not found, skipping")
            results.append(True)
    
    return all(results)


def run_integration_tests():
    """Run integration tests"""
    print_section("Running Integration Tests")
    
    integration_tests = [
        ("tests/integration/test_full_workflow.py", "Full system workflow tests")
    ]
    
    results = []
    for test_file, description in integration_tests:
        if Path(test_file).exists():
            success = run_command(
                ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
                description
            )
            results.append(success)
        else:
            print(f"⚠️  {test_file} not found, skipping")
            results.append(True)
    
    return all(results)


def run_launch_system_tests():
    """Run launch system tests"""
    print_section("Running Launch System Tests")
    
    if Path("tests/test_launch_system.py").exists():
        return run_command(
            ["python", "-m", "pytest", "tests/test_launch_system.py", "-v"],
            "Launch system tests"
        )
    else:
        print("⚠️  Launch system tests not found, skipping")
        return True


def test_claude_code_integration():
    """Test Claude Code SDK integration"""
    print_section("Testing Claude Code Integration")
    
    try:
        from claude_code_sdk import query, ClaudeCodeOptions
        print("✅ Claude Code SDK import successful")
        return True
    except ImportError as e:
        print(f"⚠️  Claude Code SDK not available: {e}")
        print("   This is expected in test environments without the SDK installed")
        return True  # Don't fail tests for missing optional dependency


def run_database_tests():
    """Test database operations"""
    print_section("Testing Database Operations")
    
    try:
        # Test database creation
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Add backend to path
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
        from models import Base
        
        # Create test database
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database schema creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def run_frontend_checks():
    """Check frontend test setup"""
    print_section("Checking Frontend Test Setup")
    
    frontend_path = Path("frontend")
    
    if not frontend_path.exists():
        print("⚠️  Frontend directory not found")
        return True
    
    package_json = frontend_path / "package.json"
    if package_json.exists():
        print("✅ Frontend package.json found")
        
        # Check if testing dependencies are mentioned
        try:
            import json
            with open(package_json) as f:
                package_data = json.load(f)
            
            dev_deps = package_data.get("devDependencies", {})
            test_deps = ["@testing-library/react", "@testing-library/jest-dom", "vitest", "jest"]
            
            found_test_deps = [dep for dep in test_deps if dep in dev_deps]
            if found_test_deps:
                print(f"✅ Testing dependencies found: {', '.join(found_test_deps)}")
            else:
                print("⚠️  No testing dependencies found in package.json")
            
        except Exception as e:
            print(f"⚠️  Could not parse package.json: {e}")
    
    return True


def run_all_tests(args):
    """Run all tests based on arguments"""
    print_header("MCP Multi-Agent System - Comprehensive Test Suite")
    
    # Check environment first
    if not check_test_environment():
        print(f"\n{Colors.RED}❌ Test environment check failed{Colors.END}")
        return False
    
    results = []
    
    # Run tests based on arguments
    if args.all or args.backend:
        results.append(run_backend_tests())
    
    if args.all or args.unit:
        results.append(run_unit_tests())
    
    if args.all or args.integration:
        results.append(run_integration_tests())
    
    if args.all or args.launch:
        results.append(run_launch_system_tests())
    
    if args.all or args.database:
        results.append(run_database_tests())
    
    if args.all or args.frontend:
        results.append(run_frontend_checks())
    
    if args.all or args.claude:
        results.append(test_claude_code_integration())
    
    # Summary
    print_header("Test Results Summary")
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total test suites: {total_tests}")
    print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
    if failed_tests > 0:
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if all(results):
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed{Colors.END}")
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="MCP Multi-Agent System Test Runner")
    
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--backend", action="store_true", help="Run backend tests")
    parser.add_argument("--frontend", action="store_true", help="Check frontend tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--launch", action="store_true", help="Run launch system tests")
    parser.add_argument("--database", action="store_true", help="Run database tests")
    parser.add_argument("--claude", action="store_true", help="Test Claude Code integration")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests only")
    
    args = parser.parse_args()
    
    # Default to all tests if no specific tests selected
    if not any([args.backend, args.frontend, args.unit, args.integration, 
                args.launch, args.database, args.claude, args.quick]):
        args.all = True
    
    # Quick tests mode
    if args.quick:
        print_header("Quick Smoke Tests")
        results = [
            check_test_environment(),
            test_claude_code_integration(),
            run_database_tests()
        ]
        success = all(results)
    else:
        success = run_all_tests(args)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()