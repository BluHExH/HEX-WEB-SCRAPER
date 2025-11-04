"""
Tests for CLI
"""

import pytest
from click.testing import CliRunner

from cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI runner"""
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help command"""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "HEX Web Scraper CLI" in result.output


def test_cli_run_help(runner):
    """Test CLI run command help"""
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "Run the scraper" in result.output


def test_cli_test_target_help(runner):
    """Test CLI test-target command help"""
    result = runner.invoke(cli, ["test-target", "--help"])
    assert result.exit_code == 0
    assert "Test a target configuration" in result.output


def test_cli_export_help(runner):
    """Test CLI export command help"""
    result = runner.invoke(cli, ["export", "--help"])
    assert result.exit_code == 0
    assert "Export scraped data" in result.output
