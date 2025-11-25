"""Test configuration for pytest."""

import pytest


@pytest.fixture
def sample_task_description() -> str:
    """Provide a sample task description for tests."""
    return "Implement a simple calculator function that adds two numbers."


@pytest.fixture
def sample_project_description() -> str:
    """Provide a sample project description for tests."""
    return """
    Create a utility that:
    1. Reads user input
    2. Performs calculations
    3. Returns results
    """
