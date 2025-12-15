"""
Test Runner Script

Runs the test suite for qixotic.tendroids extension.
Can be run from command line or imported.

Usage:
    # Run all tests
    python run_tests.py
    
    # Run with verbose output
    python run_tests.py -v
    
    # Run specific test file
    python run_tests.py tests/test_envelope_constants.py
    
    # Run with coverage
    python run_tests.py --cov
"""

import sys
import subprocess
from pathlib import Path


def run_tests(args=None):
    """
    Run pytest with the given arguments.
    
    Args:
        args: List of command line arguments for pytest
        
    Returns:
        Exit code from pytest
    """
    if args is None:
        args = ["-v"]
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"] + args
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {script_dir}")
    print("=" * 60)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=str(script_dir))
    
    return result.returncode


def main():
    """Main entry point."""
    # Get any command line args (skip script name)
    args = sys.argv[1:] if len(sys.argv) > 1 else ["-v"]
    
    exit_code = run_tests(args)
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
