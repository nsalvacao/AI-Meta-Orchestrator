"""Unit tests for configuration management."""

import os
from unittest.mock import patch

from ai_meta_orchestrator.infrastructure.config import (
    LLMConfig,
    ObservabilityConfig,
    OrchestratorConfig,
    WorkflowDefaults,
    load_config,
)


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_default_values(self) -> None:
        """Test default LLM configuration values."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.api_key_env == "OPENAI_API_KEY"

    def test_get_api_key_from_env(self) -> None:
        """Test getting API key from environment."""
        config = LLMConfig(api_key_env="TEST_API_KEY")
        with patch.dict(os.environ, {"TEST_API_KEY": "secret123"}):
            assert config.get_api_key() == "secret123"

    def test_get_api_key_not_set(self) -> None:
        """Test getting API key when not set."""
        config = LLMConfig(api_key_env="NONEXISTENT_KEY")
        with patch.dict(os.environ, {}, clear=True):
            assert config.get_api_key() is None


class TestWorkflowDefaults:
    """Tests for workflow defaults configuration."""

    def test_default_values(self) -> None:
        """Test default workflow configuration values."""
        config = WorkflowDefaults()
        assert config.max_iterations == 10
        assert config.enable_evaluation is True
        assert config.enable_correction_loop is True
        assert config.verbose is True


class TestObservabilityConfig:
    """Tests for observability configuration."""

    def test_default_values(self) -> None:
        """Test default observability configuration values."""
        config = ObservabilityConfig()
        assert config.enabled is True
        assert config.log_level == "INFO"
        assert config.metrics_enabled is False
        assert config.tracing_enabled is False


class TestOrchestratorConfig:
    """Tests for main orchestrator configuration."""

    def test_default_config(self) -> None:
        """Test default orchestrator configuration."""
        config = OrchestratorConfig()
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.workflow, WorkflowDefaults)
        assert isinstance(config.observability, ObservabilityConfig)


class TestLoadConfig:
    """Tests for configuration loading."""

    def test_load_default_config(self) -> None:
        """Test loading default configuration."""
        config = load_config()
        assert isinstance(config, OrchestratorConfig)

    def test_load_config_with_env_overrides(self) -> None:
        """Test loading configuration with environment overrides."""
        env_vars = {
            "ORCHESTRATOR_LLM_PROVIDER": "anthropic",
            "ORCHESTRATOR_LLM_MODEL": "claude-3",
            "ORCHESTRATOR_LOG_LEVEL": "DEBUG",
            "ORCHESTRATOR_VERBOSE": "false",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config()
            assert config.llm.provider == "anthropic"
            assert config.llm.model == "claude-3"
            assert config.observability.log_level == "DEBUG"
            assert config.workflow.verbose is False

    def test_load_config_verbose_variations(self) -> None:
        """Test verbose flag with different values."""
        for value in ["true", "1", "yes"]:
            with patch.dict(os.environ, {"ORCHESTRATOR_VERBOSE": value}):
                config = load_config()
                assert config.workflow.verbose is True

        for value in ["false", "0", "no"]:
            with patch.dict(os.environ, {"ORCHESTRATOR_VERBOSE": value}):
                config = load_config()
                assert config.workflow.verbose is False
