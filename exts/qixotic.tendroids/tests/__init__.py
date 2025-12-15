"""
Test Suite for qixotic.tendroids

This package contains unit tests and integration tests for the tendroids extension.

Test Categories:
- Unit tests: Can run without Omniverse (use mocks)
- Integration tests: Require Omniverse runtime

Running Tests:
    # From extension root directory:
    python -m pytest tests/ -v
    
    # Run only unit tests (no Omniverse required):
    python -m pytest tests/ -v -m "not integration"
    
    # Run with coverage:
    python -m pytest tests/ -v --cov=qixotic.tendroids
"""
