"""Unit tests for placeholder adapters."""

import warnings

from ai_meta_orchestrator.adapters.credentials.credential_adapter import (
    PlaceholderCredentialManager,
)
from ai_meta_orchestrator.adapters.external_cli.cli_adapters import (
    CodexCLIAdapter,
    CopilotCLIAdapter,
    GeminiCLIAdapter,
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

    def test_gemini_adapter_not_available(self) -> None:
        """Test Gemini CLI adapter reports not available."""
        adapter = GeminiCLIAdapter()
        assert adapter.is_available() is False
        assert adapter.cli_type == ExternalCLIType.GEMINI

    def test_codex_adapter_not_available(self) -> None:
        """Test Codex CLI adapter reports not available."""
        adapter = CodexCLIAdapter()
        assert adapter.is_available() is False
        assert adapter.cli_type == ExternalCLIType.CODEX

    def test_copilot_adapter_not_available(self) -> None:
        """Test Copilot CLI adapter reports not available."""
        adapter = CopilotCLIAdapter()
        assert adapter.is_available() is False
        assert adapter.cli_type == ExternalCLIType.COPILOT

    def test_execute_returns_not_implemented(self) -> None:
        """Test execute returns not implemented error."""
        adapter = GeminiCLIAdapter()
        result = adapter.execute("test command")
        assert result.success is False
        assert "not yet implemented" in result.error

    def test_get_cli_adapter_factory(self) -> None:
        """Test CLI adapter factory function."""
        adapter = get_cli_adapter(ExternalCLIType.GEMINI)
        assert isinstance(adapter, GeminiCLIAdapter)

        adapter = get_cli_adapter(ExternalCLIType.CODEX)
        assert isinstance(adapter, CodexCLIAdapter)


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
