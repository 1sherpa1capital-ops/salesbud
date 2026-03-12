"""
Integration tests for CLI commands
"""

import pytest
import subprocess
import json


class TestCLIStatus:
    """Test status command"""

    def test_status_command_runs(self):
        """Test that status command executes"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "status", "--toon"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        # Should complete without error
        assert result.returncode == 0

        # Should output valid TOON
        output = result.stdout.strip()
        assert output.startswith("{")

    def test_status_output_format(self):
        """Test status output structure"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "status", "--toon"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        # Parse TOON output
        output = result.stdout.strip()

        # Check for expected fields (simplified check)
        assert "s:" in output  # success field
        assert "c:" in output  # count field
        assert "d:" in output  # data field
        assert "e:" in output  # errors field


class TestCLIConfig:
    """Test config command"""

    def test_config_get_all(self):
        """Test getting all config"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "config", "--toon"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        assert result.returncode == 0

    def test_config_get_single(self):
        """Test getting single config value"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "config", "dry_run", "--toon"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        assert result.returncode == 0


class TestCLIDashboard:
    """Test dashboard command"""

    def test_dashboard_runs(self):
        """Test dashboard displays"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "dashboard", "--toon"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        assert result.returncode == 0


class TestCLIHelp:
    """Test help functionality"""

    def test_main_help(self):
        """Test main help output"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_command_help(self):
        """Test individual command help"""
        result = subprocess.run(
            ["python", "-m", "salesbud", "scrape", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/guestr/Desktop/syntolabs/salesbud",
        )

        assert result.returncode == 0
