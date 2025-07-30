#!/usr/bin/env python3
"""
Test suite for Legal Mind Agent

Comprehensive tests for all package components with async support.
"""

import pytest
import asyncio
from pathlib import Path

# Configure pytest for async testing
pytest_plugins = ['pytest_asyncio']

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_data_dir():
    """Get the test data directory"""
    return Path(__file__).parent / "data"

@pytest.fixture
def mock_azure_credentials():
    """Mock Azure credentials for testing"""
    return {
        "endpoint": "https://test-endpoint.com",
        "key": "test-key-12345",
        "app_id": "test-app-id",
        "app_password": "test-app-password"
    }
