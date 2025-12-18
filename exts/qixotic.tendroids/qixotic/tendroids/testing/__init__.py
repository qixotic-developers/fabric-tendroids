"""
Testing Package - Automated creature-tendroid interaction tests

Provides predefined test cases and execution controller for
systematic testing of deflection, contact, and recovery behaviors.
"""

from .test_case import TestCase, TestWaypoint, TestResult
from .test_controller import TestController
from .test_registry import (
    ALL_TESTS,
    TESTS_BY_ID,
    TESTS_BY_CATEGORY,
    get_test_by_id,
    get_all_test_ids,
    get_all_test_names,
)

__all__ = [
    # Data classes
    "TestCase",
    "TestWaypoint", 
    "TestResult",
    # Controller
    "TestController",
    # Registry
    "ALL_TESTS",
    "TESTS_BY_ID",
    "TESTS_BY_CATEGORY",
    "get_test_by_id",
    "get_all_test_ids",
    "get_all_test_names",
]
