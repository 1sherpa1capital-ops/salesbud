"""
Test configuration and fixtures for SalesBud
"""

import os
import tempfile

import pytest

# Set test environment variables before importing salesbud
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DRY_RUN", "1")  # Always dry-run in tests


@pytest.fixture
def temp_db_path():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_lead():
    """Sample lead data for testing"""
    return {
        "id": 1,
        "name": "Test User",
        "title": "CEO",
        "company": "Test Corp",
        "linkedin_url": "https://linkedin.com/in/testuser",
        "email": "test@example.com",
        "status": "new",
        "sequence_step": 0,
        "email_sequence_step": 0,
        "created_at": "2026-03-12T10:00:00",
        "updated_at": "2026-03-12T10:00:00",
    }


@pytest.fixture
def mock_config():
    """Sample configuration for testing"""
    return {
        "dry_run": "1",
        "dms_per_hour": "8",
        "dms_per_day": "50",
        "emails_per_hour": "10",
        "emails_per_day": "50",
    }


class MockDB:
    """In-memory database mock for unit testing"""

    def __init__(self):
        self.leads = {}
        self.activities = []
        self.config = {}
        self._next_id = 1

    def add_lead(self, lead_data):
        lead_id = self._next_id
        self._next_id += 1
        lead_data["id"] = lead_id
        self.leads[lead_id] = lead_data
        return lead_id

    def get_lead(self, lead_id):
        return self.leads.get(lead_id)

    def get_all_leads(self):
        return list(self.leads.values())

    def log_activity(self, lead_id, activity_type, content=""):
        self.activities.append(
            {
                "lead_id": lead_id,
                "activity_type": activity_type,
                "content": content,
            }
        )

    def set_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)


@pytest.fixture
def mock_db():
    """Provide a fresh mock database for each test"""
    return MockDB()
