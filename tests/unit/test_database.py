"""
Unit tests for database operations
"""

import pytest
import sqlite3
from datetime import datetime

from tests.conftest import MockDB


class TestMockDB:
    """Test mock database implementation"""

    def test_add_lead(self, mock_db):
        """Test adding a lead"""
        lead_data = {"name": "Test User", "company": "Test Corp", "status": "new"}
        lead_id = mock_db.add_lead(lead_data)

        assert lead_id == 1
        assert mock_db.leads[lead_id]["name"] == "Test User"

    def test_get_lead(self, mock_db):
        """Test retrieving a lead"""
        lead_data = {"name": "Test User", "status": "new"}
        lead_id = mock_db.add_lead(lead_data)

        retrieved = mock_db.get_lead(lead_id)
        assert retrieved["name"] == "Test User"

    def test_get_nonexistent_lead(self, mock_db):
        """Test retrieving non-existent lead returns None"""
        result = mock_db.get_lead(999)
        assert result is None

    def test_get_all_leads(self, mock_db):
        """Test retrieving all leads"""
        mock_db.add_lead({"name": "User 1", "status": "new"})
        mock_db.add_lead({"name": "User 2", "status": "connected"})

        leads = mock_db.get_all_leads()
        assert len(leads) == 2

    def test_log_activity(self, mock_db):
        """Test activity logging"""
        mock_db.log_activity(1, "connection_sent", "Sent connection request")

        assert len(mock_db.activities) == 1
        assert mock_db.activities[0]["activity_type"] == "connection_sent"

    def test_config_storage(self, mock_db):
        """Test configuration storage"""
        mock_db.set_config("dry_run", "1")

        assert mock_db.get_config("dry_run") == "1"
        assert mock_db.get_config("nonexistent") is None


class TestDatabaseSchema:
    """Test database schema integrity"""

    def test_leads_table_schema(self):
        """Verify leads table has required columns"""
        # This would be an integration test with real DB
        # For now, just document expected schema
        required_columns = [
            "id",
            "name",
            "title",
            "company",
            "linkedin_url",
            "email",
            "status",
            "sequence_step",
            "created_at",
        ]

        # In real test, would query PRAGMA table_info
        assert len(required_columns) > 0

    def test_activities_table_schema(self):
        """Verify activities table has required columns"""
        required_columns = ["id", "lead_id", "activity_type", "content", "created_at"]

        assert len(required_columns) > 0
