"""
Unit tests for input validation
"""

import pytest
from pydantic import ValidationError

from salesbud.models.validation import (
    AddEmailInput,
    ConnectInput,
    ScrapeInput,
    SendEmailInput,
    SetCompanyUrlInput,
)


class TestScrapeInput:
    """Test scrape input validation"""

    def test_valid_scrape_input(self):
        """Test valid scrape parameters"""
        input_data = ScrapeInput(query="CEO", location="Austin, TX", max_results=50)
        assert input_data.query == "CEO"
        assert input_data.location == "Austin, TX"
        assert input_data.max_results == 50

    def test_scrape_query_required(self):
        """Test that query is required"""
        with pytest.raises(ValidationError) as exc_info:
            ScrapeInput(location="Austin, TX")
        assert "query" in str(exc_info.value)

    def test_scrape_max_results_bounds(self):
        """Test max_results validation"""
        # Too high
        with pytest.raises(ValidationError):
            ScrapeInput(query="CEO", max_results=501)

        # Too low
        with pytest.raises(ValidationError):
            ScrapeInput(query="CEO", max_results=0)

        # At boundary
        input_data = ScrapeInput(query="CEO", max_results=500)
        assert input_data.max_results == 500


class TestAddEmailInput:
    """Test add email input validation"""

    def test_valid_email(self):
        """Test valid email address"""
        input_data = AddEmailInput(lead_id=1, email="test@example.com")
        assert input_data.lead_id == 1
        assert input_data.email == "test@example.com"

    def test_invalid_email(self):
        """Test invalid email rejection"""
        with pytest.raises(ValidationError):
            AddEmailInput(lead_id=1, email="not-an-email")

    def test_email_normalization(self):
        """Test email is lowercased"""
        input_data = AddEmailInput(lead_id=1, email="TEST@EXAMPLE.COM")
        assert input_data.email == "test@example.com"


class TestSendEmailInput:
    """Test send email input validation"""

    def test_valid_email(self):
        """Test valid email sending parameters"""
        input_data = SendEmailInput(
            to="recipient@example.com", subject="Test Subject", body="Test body content"
        )
        assert input_data.to == "recipient@example.com"
        assert input_data.subject == "Test Subject"
        assert input_data.body == "Test body content"

    def test_subject_max_length(self):
        """Test subject line length limit"""
        # Should fail with too long subject
        with pytest.raises(ValidationError):
            SendEmailInput(
                to="test@example.com",
                subject="x" * 1000,  # Way too long
                body="Test",
            )


class TestSetCompanyUrlInput:
    """Test set company URL input validation"""

    def test_valid_url(self):
        """Test valid company URL"""
        input_data = SetCompanyUrlInput(lead_id=1, company_url="https://example.com")
        assert input_data.company_url == "https://example.com"

    def test_invalid_url(self):
        """Test invalid URL rejection"""
        with pytest.raises(ValidationError):
            SetCompanyUrlInput(lead_id=1, company_url="not-a-url")

    def test_non_http_url(self):
        """Test that non-HTTP(S) URLs are rejected"""
        with pytest.raises(ValidationError):
            SetCompanyUrlInput(lead_id=1, company_url="ftp://example.com")


class TestConnectInput:
    """Test connection input validation"""

    def test_valid_input(self):
        """Test valid connection parameters"""
        input_data = ConnectInput(max_requests=10, delay_seconds=5)
        assert input_data.max_requests == 10
        assert input_data.delay_seconds == 5

    def test_delay_bounds(self):
        """Test delay validation"""
        # Too short
        with pytest.raises(ValidationError):
            ConnectInput(delay_seconds=0)

        # Valid
        input_data = ConnectInput(delay_seconds=60)
        assert input_data.delay_seconds == 60
