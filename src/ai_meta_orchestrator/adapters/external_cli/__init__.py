"""External CLI adapters for AI tools.

This module provides adapters for external AI CLI tools:
- Gemini CLI: Google's Gemini AI command-line interface
- Codex CLI: OpenAI's Codex command-line interface
- Copilot CLI: GitHub Copilot command-line interface
"""

from ai_meta_orchestrator.adapters.external_cli.cli_adapters import (
    BaseCLIAdapter,
    CLIConfig,
    CodexCLIAdapter,
    CopilotCLIAdapter,
    GeminiCLIAdapter,
    PlaceholderCLIAdapter,
    get_cli_adapter,
)
from ai_meta_orchestrator.adapters.external_cli.cli_agents import (
    CodexAgent,
    CopilotAgent,
    ExternalCLIAgent,
    GeminiAgent,
    create_cli_agent,
)

__all__ = [
    # Adapters
    "BaseCLIAdapter",
    "CLIConfig",
    "CodexCLIAdapter",
    "CopilotCLIAdapter",
    "GeminiCLIAdapter",
    "PlaceholderCLIAdapter",
    "get_cli_adapter",
    # Agents
    "CodexAgent",
    "CopilotAgent",
    "ExternalCLIAgent",
    "GeminiAgent",
    "create_cli_agent",
]
