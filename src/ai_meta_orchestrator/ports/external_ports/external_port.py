"""External system port interfaces - Abstractions for external integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExternalCLIType(str, Enum):
    """Types of external CLI integrations."""

    GEMINI = "gemini"
    CODEX = "codex"
    COPILOT = "copilot"
    CUSTOM = "custom"


@dataclass
class CLICommandResult:
    """Result of executing an external CLI command.

    Attributes:
        success: Whether the command succeeded.
        output: The output from the command.
        error: Error message if failed.
        exit_code: The exit code of the command.
    """

    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0


class ExternalCLIPort(ABC):
    """Abstract interface for external CLI operations.

    This port allows integration with external CLI tools like Gemini CLI,
    Codex CLI, Copilot Agent CLI, etc.
    """

    @property
    @abstractmethod
    def cli_type(self) -> ExternalCLIType:
        """Get the type of CLI this adapter handles."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the CLI is available and properly configured.

        Returns:
            True if the CLI is available, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, command: str, **kwargs: Any) -> CLICommandResult:
        """Execute a CLI command.

        Args:
            command: The command to execute.
            **kwargs: Additional arguments for the command.

        Returns:
            CLICommandResult containing the output or error.
        """
        pass


class CredentialManagerPort(ABC):
    """Abstract interface for credential management.

    Placeholder for future credential management implementation.
    """

    @abstractmethod
    def get_credential(self, key: str) -> str | None:
        """Get a credential by key.

        Args:
            key: The credential key.

        Returns:
            The credential value or None if not found.
        """
        pass

    @abstractmethod
    def set_credential(self, key: str, value: str) -> bool:
        """Set a credential.

        Args:
            key: The credential key.
            value: The credential value.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def has_credential(self, key: str) -> bool:
        """Check if a credential exists.

        Args:
            key: The credential key.

        Returns:
            True if the credential exists, False otherwise.
        """
        pass


class GitCICDPort(ABC):
    """Abstract interface for Git and CI/CD operations.

    Placeholder for future Git/CI-CD integration.
    """

    @abstractmethod
    def get_current_branch(self) -> str | None:
        """Get the current Git branch.

        Returns:
            The branch name or None if not in a Git repository.
        """
        pass

    @abstractmethod
    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch.

        Args:
            branch_name: Name of the branch to create.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def commit_changes(self, message: str) -> bool:
        """Commit current changes.

        Args:
            message: The commit message.

        Returns:
            True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def trigger_pipeline(self, pipeline_name: str) -> str | None:
        """Trigger a CI/CD pipeline.

        Args:
            pipeline_name: Name of the pipeline to trigger.

        Returns:
            Pipeline run ID or None if failed.
        """
        pass


class ObservabilityPort(ABC):
    """Abstract interface for observability and monitoring.

    Placeholder for future observability implementation.
    """

    @abstractmethod
    def log_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Log an event.

        Args:
            event_name: Name of the event.
            data: Event data.
        """
        pass

    @abstractmethod
    def record_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a metric.

        Args:
            metric_name: Name of the metric.
            value: The metric value.
            tags: Optional tags for the metric.
        """
        pass

    @abstractmethod
    def start_span(self, operation_name: str) -> str:
        """Start a tracing span.

        Args:
            operation_name: Name of the operation.

        Returns:
            The span ID.
        """
        pass

    @abstractmethod
    def end_span(self, span_id: str, status: str = "ok") -> None:
        """End a tracing span.

        Args:
            span_id: The span ID to end.
            status: The final status of the span.
        """
        pass
