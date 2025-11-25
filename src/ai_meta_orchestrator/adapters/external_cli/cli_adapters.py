"""Placeholder external CLI adapters.

These adapters are placeholders for future integration with external CLI tools:
- Gemini CLI
- Codex CLI
- Copilot Agent CLI
- Custom CLI tools

Each adapter implements the ExternalCLIPort interface and currently returns
placeholder responses indicating that the integration is not yet implemented.
"""

from typing import Any

from ai_meta_orchestrator.ports.external_ports.external_port import (
    CLICommandResult,
    ExternalCLIPort,
    ExternalCLIType,
)


class PlaceholderCLIAdapter(ExternalCLIPort):
    """Base placeholder adapter for external CLI tools.

    This adapter serves as a template for future CLI integrations.
    """

    def __init__(self, cli_type: ExternalCLIType) -> None:
        """Initialize the placeholder adapter.

        Args:
            cli_type: The type of CLI this adapter handles.
        """
        self._cli_type = cli_type

    @property
    def cli_type(self) -> ExternalCLIType:
        """Get the type of CLI this adapter handles."""
        return self._cli_type

    def is_available(self) -> bool:
        """Check if the CLI is available.

        Returns:
            False - placeholder not implemented.
        """
        return False

    def execute(self, command: str, **kwargs: Any) -> CLICommandResult:
        """Execute a CLI command.

        Args:
            command: The command to execute.
            **kwargs: Additional arguments.

        Returns:
            CLICommandResult indicating not implemented.
        """
        return CLICommandResult(
            success=False,
            output="",
            error=f"{self._cli_type.value} CLI integration not yet implemented",
            exit_code=1,
        )


class GeminiCLIAdapter(PlaceholderCLIAdapter):
    """Placeholder adapter for Gemini CLI integration."""

    def __init__(self) -> None:
        """Initialize the Gemini CLI adapter."""
        super().__init__(ExternalCLIType.GEMINI)


class CodexCLIAdapter(PlaceholderCLIAdapter):
    """Placeholder adapter for Codex CLI integration."""

    def __init__(self) -> None:
        """Initialize the Codex CLI adapter."""
        super().__init__(ExternalCLIType.CODEX)


class CopilotCLIAdapter(PlaceholderCLIAdapter):
    """Placeholder adapter for Copilot Agent CLI integration."""

    def __init__(self) -> None:
        """Initialize the Copilot CLI adapter."""
        super().__init__(ExternalCLIType.COPILOT)


def get_cli_adapter(cli_type: ExternalCLIType) -> ExternalCLIPort:
    """Factory function to get a CLI adapter by type.

    Args:
        cli_type: The type of CLI adapter to create.

    Returns:
        An ExternalCLIPort implementation.
    """
    if cli_type == ExternalCLIType.GEMINI:
        return GeminiCLIAdapter()
    elif cli_type == ExternalCLIType.CODEX:
        return CodexCLIAdapter()
    elif cli_type == ExternalCLIType.COPILOT:
        return CopilotCLIAdapter()
    else:
        return PlaceholderCLIAdapter(cli_type)
