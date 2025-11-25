"""Unit tests for adapters."""

import os
import warnings
from unittest.mock import patch

from ai_meta_orchestrator.adapters.credentials.credential_adapter import (
    PlaceholderCredentialManager,
)
from ai_meta_orchestrator.adapters.external_cli.cli_adapters import (
    BaseCLIAdapter,
    CLIConfig,
    CodexCLIAdapter,
    CopilotCLIAdapter,
    GeminiCLIAdapter,
    PlaceholderCLIAdapter,
    get_cli_adapter,
)
from ai_meta_orchestrator.adapters.git_cicd.git_cicd_adapter import (
    PlaceholderGitCICDAdapter,
)
from ai_meta_orchestrator.adapters.observability.observability_adapter import (
    PlaceholderObservabilityAdapter,
)
from ai_meta_orchestrator.ports.external_ports.external_port import ExternalCLIType


class TestCLIAdapters:
    """Tests for CLI adapters."""

    def test_gemini_adapter_cli_type(self) -> None:
        """Test Gemini CLI adapter has correct CLI type."""
        adapter = GeminiCLIAdapter()
        assert adapter.cli_type == ExternalCLIType.GEMINI

    def test_codex_adapter_cli_type(self) -> None:
        """Test Codex CLI adapter has correct CLI type."""
        adapter = CodexCLIAdapter()
        assert adapter.cli_type == ExternalCLIType.CODEX

    def test_copilot_adapter_cli_type(self) -> None:
        """Test Copilot CLI adapter has correct CLI type."""
        adapter = CopilotCLIAdapter()
        assert adapter.cli_type == ExternalCLIType.COPILOT

    def test_gemini_adapter_not_available_when_cli_not_found(self) -> None:
        """Test Gemini CLI adapter reports not available when CLI not found."""
        with patch("shutil.which", return_value=None):
            adapter = GeminiCLIAdapter()
            assert adapter.is_available() is False

    def test_codex_adapter_available_when_cli_found(self) -> None:
        """Test Codex CLI adapter reports available when CLI found."""
        with patch("shutil.which", return_value="/usr/bin/openai"):
            adapter = CodexCLIAdapter()
            assert adapter.is_available() is True

    def test_execute_returns_not_found_when_cli_missing(self) -> None:
        """Test execute returns CLI not found error when executable missing."""
        with patch("shutil.which", return_value=None):
            adapter = GeminiCLIAdapter()
            result = adapter.execute("test command")
            assert result.success is False
            assert "not found" in result.error.lower()
            assert result.exit_code == 127

    def test_execute_returns_auth_required_when_not_authenticated(self) -> None:
        """Test execute returns auth required when API key missing."""
        with (
            patch("shutil.which", return_value="/usr/bin/gemini"),
            patch.dict(os.environ, {}, clear=True),
        ):
            adapter = GeminiCLIAdapter()
            result = adapter.execute("test command")
            assert result.success is False
            assert "authentication required" in result.error.lower()

    def test_get_cli_adapter_factory(self) -> None:
        """Test CLI adapter factory function."""
        adapter = get_cli_adapter(ExternalCLIType.GEMINI)
        assert isinstance(adapter, GeminiCLIAdapter)

        adapter = get_cli_adapter(ExternalCLIType.CODEX)
        assert isinstance(adapter, CodexCLIAdapter)

        adapter = get_cli_adapter(ExternalCLIType.COPILOT)
        assert isinstance(adapter, CopilotCLIAdapter)

        adapter = get_cli_adapter(ExternalCLIType.CUSTOM)
        assert isinstance(adapter, PlaceholderCLIAdapter)

    def test_cli_config_defaults(self) -> None:
        """Test CLIConfig dataclass defaults."""
        config = CLIConfig(executable="test")
        assert config.executable == "test"
        assert config.api_key_env is None
        assert config.timeout == 300
        assert config.extra_args == []
        assert config.working_dir is None

    def test_base_cli_adapter_build_command(self) -> None:
        """Test BaseCLIAdapter builds command correctly."""
        config = CLIConfig(
            executable="test-cli",
            extra_args=["--verbose"],
        )
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)
        adapter._executable_path = "/usr/bin/test-cli"

        cmd = adapter._build_command("run --flag")
        assert cmd == ["/usr/bin/test-cli", "--verbose", "run", "--flag"]

    def test_base_cli_adapter_build_command_with_args(self) -> None:
        """Test BaseCLIAdapter builds command with args safely."""
        config = CLIConfig(
            executable="test-cli",
            extra_args=["--verbose"],
        )
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)
        adapter._executable_path = "/usr/bin/test-cli"

        # Args should be added as separate list items (safe from shell injection)
        cmd = adapter._build_command("suggest", args=["user input with spaces"])
        assert cmd == ["/usr/bin/test-cli", "--verbose", "suggest", "user input with spaces"]

        # Even input with shell metacharacters is safe
        cmd = adapter._build_command("explain", args=["rm -rf /; echo 'pwned'"])
        assert cmd == ["/usr/bin/test-cli", "--verbose", "explain", "rm -rf /; echo 'pwned'"]

    def test_gemini_adapter_api_key_envs(self) -> None:
        """Test Gemini adapter checks multiple API key environment variables."""
        adapter = GeminiCLIAdapter()

        # No API key set
        with patch.dict(os.environ, {}, clear=True):
            assert adapter.is_authenticated() is False
            assert adapter.get_api_key() is None

        # GOOGLE_API_KEY set
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True):
            assert adapter.is_authenticated() is True
            assert adapter.get_api_key() == "test-key"

        # GEMINI_API_KEY set
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key2"}, clear=True):
            assert adapter.is_authenticated() is True
            assert adapter.get_api_key() == "test-key2"


class TestCredentialManager:
    """Tests for credential manager adapter."""

    def test_set_and_get_credential(self) -> None:
        """Test setting and getting credentials."""
        manager = PlaceholderCredentialManager()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            manager.set_credential("test_key", "test_value")
            value = manager.get_credential("test_key")

            assert value == "test_value"
            assert len(w) >= 1

    def test_has_credential(self) -> None:
        """Test checking credential existence."""
        manager = PlaceholderCredentialManager()

        assert manager.has_credential("nonexistent") is False

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            manager.set_credential("exists", "value")

        assert manager.has_credential("exists") is True

    def test_get_nonexistent_credential(self) -> None:
        """Test getting non-existent credential."""
        manager = PlaceholderCredentialManager()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            value = manager.get_credential("nonexistent")

        assert value is None


class TestGitCICDAdapter:
    """Tests for Git/CI-CD adapter."""

    def test_get_current_branch_returns_none(self) -> None:
        """Test get_current_branch returns None (placeholder)."""
        adapter = PlaceholderGitCICDAdapter()
        assert adapter.get_current_branch() is None

    def test_create_branch_returns_false(self) -> None:
        """Test create_branch returns False (placeholder)."""
        adapter = PlaceholderGitCICDAdapter()
        assert adapter.create_branch("test-branch") is False

    def test_commit_changes_returns_false(self) -> None:
        """Test commit_changes returns False (placeholder)."""
        adapter = PlaceholderGitCICDAdapter()
        assert adapter.commit_changes("Test commit") is False

    def test_trigger_pipeline_returns_none(self) -> None:
        """Test trigger_pipeline returns None (placeholder)."""
        adapter = PlaceholderGitCICDAdapter()
        assert adapter.trigger_pipeline("test-pipeline") is None


class TestObservabilityAdapter:
    """Tests for observability adapter."""

    def test_log_event(self) -> None:
        """Test logging an event."""
        adapter = PlaceholderObservabilityAdapter()
        # Should not raise
        adapter.log_event("test_event", {"key": "value"})

    def test_record_metric(self) -> None:
        """Test recording a metric."""
        adapter = PlaceholderObservabilityAdapter()
        # Should not raise
        adapter.record_metric("test_metric", 42.0, {"tag": "value"})

    def test_span_lifecycle(self) -> None:
        """Test span start and end."""
        adapter = PlaceholderObservabilityAdapter()

        span_id = adapter.start_span("test_operation")
        assert span_id is not None
        assert len(span_id) > 0

        # Should not raise
        adapter.end_span(span_id, "ok")

    def test_end_nonexistent_span(self) -> None:
        """Test ending a non-existent span."""
        adapter = PlaceholderObservabilityAdapter()
        # Should not raise
        adapter.end_span("nonexistent-span-id")
