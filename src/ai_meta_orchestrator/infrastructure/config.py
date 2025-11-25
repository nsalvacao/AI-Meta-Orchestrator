"""Configuration management for the orchestrator."""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfig:
    """Configuration for the LLM provider.

    Attributes:
        provider: The LLM provider (e.g., "openai", "anthropic").
        model: The model to use.
        temperature: Temperature for generation.
        max_tokens: Maximum tokens for generation.
        api_key_env: Environment variable name for the API key.
    """

    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key_env: str = "OPENAI_API_KEY"

    def get_api_key(self) -> str | None:
        """Get the API key from environment."""
        return os.environ.get(self.api_key_env)


@dataclass
class WorkflowDefaults:
    """Default configuration for workflows.

    Attributes:
        max_iterations: Default maximum iterations.
        enable_evaluation: Default evaluation setting.
        enable_correction_loop: Default correction loop setting.
        verbose: Default verbose setting.
    """

    max_iterations: int = 10
    enable_evaluation: bool = True
    enable_correction_loop: bool = True
    verbose: bool = True


@dataclass
class ObservabilityConfig:
    """Configuration for observability.

    Attributes:
        enabled: Whether observability is enabled.
        log_level: Logging level.
        metrics_enabled: Whether metrics collection is enabled.
        tracing_enabled: Whether distributed tracing is enabled.
    """

    enabled: bool = True
    log_level: str = "INFO"
    metrics_enabled: bool = False
    tracing_enabled: bool = False


@dataclass
class OrchestratorConfig:
    """Main configuration for the orchestrator.

    Attributes:
        llm: LLM provider configuration.
        workflow: Default workflow configuration.
        observability: Observability configuration.
        extra: Additional configuration options.
    """

    llm: LLMConfig = field(default_factory=LLMConfig)
    workflow: WorkflowDefaults = field(default_factory=WorkflowDefaults)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    extra: dict[str, Any] = field(default_factory=dict)


def load_config(config_path: str | None = None) -> OrchestratorConfig:
    """Load configuration from file or environment.

    Args:
        config_path: Optional path to a configuration file.

    Returns:
        OrchestratorConfig instance.
    """
    # For now, return default configuration
    # Future: Load from YAML/TOML file if path provided
    config = OrchestratorConfig()

    # Override from environment variables
    if os.environ.get("ORCHESTRATOR_LLM_PROVIDER"):
        config.llm.provider = os.environ["ORCHESTRATOR_LLM_PROVIDER"]

    if os.environ.get("ORCHESTRATOR_LLM_MODEL"):
        config.llm.model = os.environ["ORCHESTRATOR_LLM_MODEL"]

    if os.environ.get("ORCHESTRATOR_LOG_LEVEL"):
        config.observability.log_level = os.environ["ORCHESTRATOR_LOG_LEVEL"]

    if os.environ.get("ORCHESTRATOR_VERBOSE"):
        config.workflow.verbose = os.environ["ORCHESTRATOR_VERBOSE"].lower() in (
            "true",
            "1",
            "yes",
        )

    return config
