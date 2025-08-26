#!/usr/bin/env python3
"""
AI-Server Test Runner
Comprehensive test execution with logging, reporting, and performance metrics
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_config import TestConfig


class TestRunner:
    """Main test runner for AI-Server testing suite"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.start_time = None
        self.results = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "tests_run": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "coverage": None,
            "components": {},
            "performance": {}
        }
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration for test execution"""
        # Ensure logs directory exists
        self.config.TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            format=self.config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(self.config.get_log_file_path("test_execution")),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("test_runner")
        self.logger.info("Test runner initialized")
    
    def run_pytest_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Execute pytest command with specified arguments"""
        cmd = ["python3", "-m", "pytest"] + args
        
        self.logger.info(f"Executing: {' '.join(cmd)}")
        
        return subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        self.logger.info("Starting unit tests...")
        
        args = [
            "tests/unit/",
            "-v",
            "--tb=short",
            f"--junitxml={self.config.TEST_REPORTS_DIR}/unit_tests.xml",
            "--json-report",
            f"--json-report-file={self.config.TEST_REPORTS_DIR}/unit_tests.json"
        ]
        
        result = self.run_pytest_command(args)
        
        return {
            "category": "unit",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        self.logger.info("Starting integration tests...")
        
        args = [
            "tests/integration/",
            "-v",
            "--tb=short",
            f"--junitxml={self.config.TEST_REPORTS_DIR}/integration_tests.xml",
            "--json-report",
            f"--json-report-file={self.config.TEST_REPORTS_DIR}/integration_tests.json"
        ]
        
        result = self.run_pytest_command(args)
        
        return {
            "category": "integration",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_functional_tests(self) -> Dict[str, Any]:
        """Run functional tests"""
        self.logger.info("Starting functional tests...")
        
        args = [
            "tests/functional/",
            "-v",
            "--tb=short",
            f"--junitxml={self.config.TEST_REPORTS_DIR}/functional_tests.xml",
            "--json-report",
            f"--json-report-file={self.config.TEST_REPORTS_DIR}/functional_tests.json"
        ]
        
        result = self.run_pytest_command(args)
        
        return {
            "category": "functional",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_component_tests(self, component: str) -> Dict[str, Any]:
        """Run tests for specific component"""
        self.logger.info(f"Starting tests for component: {component}")
        
        # Map component names to test patterns
        component_patterns = {
            "startup": "tests/unit/test_startup_script.py",
            "memory-server": "tests/unit/test_memory_server.py",
            "llm-server": "tests/unit/test_llm_server.py",
            "model-watcher": "tests/unit/test_model_watcher.py"
        }
        
        if component not in component_patterns:
            raise ValueError(f"Unknown component: {component}")
        
        args = [
            component_patterns[component],
            "-v",
            "--tb=long",
            f"--junitxml={self.config.TEST_REPORTS_DIR}/{component}_tests.xml",
            "--json-report",
            f"--json-report-file={self.config.TEST_REPORTS_DIR}/{component}_tests.json"
        ]
        
        result = self.run_pytest_command(args)
        
        return {
            "category": "component",
            "component": component,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_coverage_tests(self) -> Dict[str, Any]:
        """Run tests with coverage analysis"""
        self.logger.info("Starting coverage analysis...")
        
        args = [
            "tests/",
            "--cov=bin/",
            "--cov=apps/",
            "--cov=services/",
            f"--cov-report=html:{self.config.TEST_REPORTS_DIR}/coverage/",
            f"--cov-report=json:{self.config.TEST_REPORTS_DIR}/coverage.json",
            "--cov-report=term-missing",
            "-v"
        ]
        
        result = self.run_pytest_command(args)
        
        return {
            "category": "coverage",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        self.logger.info("Starting performance tests...")
        
        args = [
            "tests/",
            "--benchmark-only",
            "--benchmark-sort=mean",
            f"--benchmark-json={self.config.TEST_REPORTS_DIR}/benchmark.json",
            "-v"
        ]
        
        result = self.run_pytest_command(args)
        
        return {
            "category": "performance",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def analyze_test_results(self, test_results: List[Dict[str, Any]]):
        """Analyze test results and update summary"""
        for result in test_results:
            category = result["category"]
            
            # Parse JSON report if available
            json_file = self.config.TEST_REPORTS_DIR / f"{category}_tests.json"
            if json_file.exists():
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                    
                    self.results["components"][category] = {
                        "tests_run": data.get("summary", {}).get("total", 0),
                        "passed": data.get("summary", {}).get("passed", 0),
                        "failed": data.get("summary", {}).get("failed", 0),
                        "skipped": data.get("summary", {}).get("skipped", 0),
                        "duration": data.get("duration", 0)
                    }
                    
                    # Update overall results
                    self.results["tests_run"] += data.get("summary", {}).get("total", 0)
                    self.results["passed"] += data.get("summary", {}).get("passed", 0)
                    self.results["failed"] += data.get("summary", {}).get("failed", 0)
                    self.results["skipped"] += data.get("summary", {}).get("skipped", 0)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON report for {category}: {e}")
            
            # Log results
            if result["returncode"] == 0:
                self.logger.info(f"{category.title()} tests completed successfully")
            else:
                self.logger.error(f"{category.title()} tests failed with code {result['returncode']}")
                if result["stderr"]:
                    self.logger.error(f"Error output: {result['stderr']}")
    
    def generate_summary_report(self):
        """Generate summary report"""
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration"] = time.time() - self.start_time
        
        # Write JSON report
        report_file = self.config.TEST_REPORTS_DIR / "test_results.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("AI-SERVER TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.results['tests_run']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Skipped: {self.results['skipped']}")
        print(f"Duration: {self.results['duration']:.2f} seconds")
        print(f"Success Rate: {(self.results['passed']/self.results['tests_run']*100):.1f}%" if self.results['tests_run'] > 0 else "No tests run")
        
        # Component breakdown
        if self.results["components"]:
            print("\nComponent Results:")
            for component, stats in self.results["components"].items():
                print(f"  {component.title()}: {stats['passed']}/{stats['tests_run']} passed ({stats['duration']:.2f}s)")
        
        print(f"\nDetailed reports available in: {self.config.TEST_REPORTS_DIR}")
        print("="*60)
        
        return self.results["failed"] == 0
    
    async def run_all_tests(self):
        """Run complete test suite"""
        self.logger.info("Starting complete test suite...")
        self.start_time = time.time()
        self.results["start_time"] = datetime.now().isoformat()
        
        # Ensure test directories exist
        self.config.TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        (self.config.TEST_REPORTS_DIR / "coverage").mkdir(parents=True, exist_ok=True)
        
        test_results = []
        
        try:
            # Run different test categories
            test_results.append(self.run_unit_tests())
            test_results.append(self.run_integration_tests())
            test_results.append(self.run_functional_tests())
            test_results.append(self.run_coverage_tests())
            
            # Analyze results
            self.analyze_test_results(test_results)
            
            # Generate summary
            success = self.generate_summary_report()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return False


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description="AI-Server Test Runner")
    
    # Test selection arguments
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only") 
    parser.add_argument("--functional", action="store_true", help="Run functional tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--component", choices=["startup", "memory-server", "llm-server", "model-watcher"], help="Run tests for specific component")
    
    # Configuration arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-j", type=int, help="Run tests in parallel (number of workers)")
    parser.add_argument("--timeout", type=int, default=300, help="Test timeout in seconds")
    
    args = parser.parse_args()
    
    # Create test configuration
    config = TestConfig()
    
    # Create test runner
    runner = TestRunner(config)
    
    # Determine what tests to run
    if args.all or not any([args.unit, args.integration, args.functional, args.coverage, args.performance, args.component]):
        # Run all tests
        success = asyncio.run(runner.run_all_tests())
    else:
        # Run specific test categories
        test_results = []
        
        if args.unit:
            test_results.append(runner.run_unit_tests())
        if args.integration:
            test_results.append(runner.run_integration_tests())
        if args.functional:
            test_results.append(runner.run_functional_tests())
        if args.coverage:
            test_results.append(runner.run_coverage_tests())
        if args.performance:
            test_results.append(runner.run_performance_tests())
        if args.component:
            test_results.append(runner.run_component_tests(args.component))
        
        runner.start_time = time.time()
        runner.results["start_time"] = datetime.now().isoformat()
        
        runner.analyze_test_results(test_results)
        success = runner.generate_summary_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()