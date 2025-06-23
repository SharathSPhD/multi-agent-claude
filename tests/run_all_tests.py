#!/usr/bin/env python3
"""
Comprehensive test runner for MCP Multi-Agent System
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path


class TestRunner:
    """Test runner for MCP Multi-Agent System"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
    
    def run_unit_tests(self):
        """Run unit tests"""
        print("🧪 Running Unit Tests")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "unit",
            "--tb=short",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.tests_dir)
        return result.returncode == 0
    
    def run_backend_tests(self):
        """Run backend tests"""
        print("\n🔧 Running Backend Tests")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "backend/",
            "--tb=short",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.tests_dir)
        return result.returncode == 0
    
    def run_frontend_tests(self):
        """Run frontend tests"""
        print("\n🌐 Running Frontend Tests")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "frontend/",
            "--tb=short", 
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.tests_dir)
        return result.returncode == 0
    
    def run_control_feature_tests(self):
        """Run control feature tests"""
        print("\n🎮 Running Control Feature Tests")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "controls",
            "--tb=short",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.tests_dir)
        return result.returncode == 0
    
    def run_integration_tests(self, require_services=True):
        """Run integration tests"""
        print("\n🔗 Running Integration Tests")
        print("-" * 40)
        
        if require_services:
            if not self.check_services():
                print("❌ Required services not running")
                print("   Start services with: python launch_system.py")
                return False
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-m", "integration",
            "--tb=short",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.tests_dir)
        return result.returncode == 0
    
    def check_services(self):
        """Check if required services are running"""
        try:
            import requests
            
            # Check backend
            backend_response = requests.get("http://localhost:8000/health", timeout=3)
            if backend_response.status_code != 200:
                print("❌ Backend not responding")
                return False
            
            print("✅ Backend service running")
            return True
        
        except Exception as e:
            print(f"❌ Service check failed: {e}")
            return False
    
    def run_all_tests(self, include_integration=False):
        """Run all tests"""
        print("🎯 MCP Multi-Agent System - Comprehensive Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Unit tests
        results['unit'] = self.run_unit_tests()
        
        # Backend tests
        results['backend'] = self.run_backend_tests()
        
        # Frontend tests  
        results['frontend'] = self.run_frontend_tests()
        
        # Control feature tests
        results['controls'] = self.run_control_feature_tests()
        
        # Integration tests (if requested)
        if include_integration:
            results['integration'] = self.run_integration_tests()
        
        # Summary
        self.print_summary(results)
        
        return all(results.values())
    
    def print_summary(self, results):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 40)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_type, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {test_type.title()}: {status}")
        
        print(f"\n🎉 Overall: {passed_tests}/{total_tests} test suites passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - check output above")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run MCP Multi-Agent System tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--backend", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend", action="store_true", help="Run only frontend tests")
    parser.add_argument("--controls", action="store_true", help="Run only control feature tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests including integration")
    parser.add_argument("--no-services", action="store_true", help="Skip service checks for integration tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Check if any specific test type was requested
    if args.unit:
        success = runner.run_unit_tests()
    elif args.backend:
        success = runner.run_backend_tests()
    elif args.frontend:
        success = runner.run_frontend_tests()
    elif args.controls:
        success = runner.run_control_feature_tests()
    elif args.integration:
        success = runner.run_integration_tests(require_services=not args.no_services)
    elif args.all:
        success = runner.run_all_tests(include_integration=True)
    else:
        # Default: run all tests except integration
        success = runner.run_all_tests(include_integration=False)
        print("\n💡 To include integration tests, use: --all")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()