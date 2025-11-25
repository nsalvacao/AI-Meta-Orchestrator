"""External CLI adapters for AI tools.

This module provides CLI adapters for external AI tools:
- Gemini CLI: Google's Gemini AI command-line interface
- Codex CLI: OpenAI's Codex command-line interface
- Copilot CLI: GitHub Copilot command-line interface
- Custom CLI tools

Each adapter implements the ExternalCLIPort interface and provides:
- Availability checking (CLI installation detection)
- Authentication support (API keys, tokens)
- Command execution with timeout and error handling
"""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

from ai_meta_orchestrator.ports.external_ports.external_port import (
    CLICommandResult,
    ExternalCLIPort,
    ExternalCLIType,
)


@dataclass
class CLIConfig:
    """Configuration for an external CLI adapter.

    Attributes:
        executable: The CLI executable name or path.
        api_key_env: Environment variable name for API key.
        timeout: Default timeout for commands in seconds.
        extra_args: Additional arguments to pass to all commands.
        working_dir: Working directory for command execution.
    """

    executable: str
    api_key_env: str | None = None
    timeout: int = 300
    extra_args: list[str] = field(default_factory=list)
    working_dir: str | None = None


class BaseCLIAdapter(ExternalCLIPort):
    """Base adapter for external CLI tools.

    This adapter provides common functionality for all CLI integrations:
    - Executable detection
    - Authentication via environment variables
    - Command execution with subprocess
    - Timeout handling
    """

    def __init__(self, cli_type: ExternalCLIType, config: CLIConfig) -> None:
        """Initialize the CLI adapter.

        Args:
            cli_type: The type of CLI this adapter handles.
            config: Configuration for the CLI.
        """
        self._cli_type = cli_type
        self._config = config
        self._executable_path: str | None = None

    @property
    def cli_type(self) -> ExternalCLIType:
        """Get the type of CLI this adapter handles."""
        return self._cli_type

    @property
    def config(self) -> CLIConfig:
        """Get the CLI configuration."""
        return self._config

    def _find_executable(self) -> str | None:
        """Find the CLI executable.

        Returns:
            Path to executable or None if not found.
        """
        return shutil.which(self._config.executable)

    def is_available(self) -> bool:
        """Check if the CLI is available.

        Returns:
            True if the CLI executable is found.
        """
        self._executable_path = self._find_executable()
        return self._executable_path is not None

    def is_authenticated(self) -> bool:
        """Check if authentication credentials are available.

        Returns:
            True if API key is set in environment.
        """
        if self._config.api_key_env is None:
            return True  # No authentication required
        return os.environ.get(self._config.api_key_env) is not None

    def get_api_key(self) -> str | None:
        """Get the API key from environment.

        Returns:
            API key or None if not set.
        """
        if self._config.api_key_env is None:
            return None
        return os.environ.get(self._config.api_key_env)

    def _build_command(self, command: str, **kwargs: Any) -> list[str]:
        """Build the full command with arguments.

        Args:
            command: The command to execute.
            **kwargs: Additional arguments.

        Returns:
            List of command arguments.
        """
        executable = self._executable_path or self._config.executable
        cmd = [executable]

        # Add extra args from config
        cmd.extend(self._config.extra_args)

        # Add the main command
        if command:
            cmd.extend(command.split())

        return cmd

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for command execution.

        Returns:
            Environment dictionary.
        """
        env = os.environ.copy()
        return env

    def execute(self, command: str, **kwargs: Any) -> CLICommandResult:
        """Execute a CLI command.

        Args:
            command: The command to execute.
            **kwargs: Additional arguments:
                - timeout: Override default timeout
                - input_text: Text to pass to stdin
                - working_dir: Override working directory

        Returns:
            CLICommandResult containing output or error.
        """
        if not self.is_available():
            return CLICommandResult(
                success=False,
                output="",
                error=f"{self._cli_type.value} CLI not found. "
                      f"Please install '{self._config.executable}'.",
                exit_code=127,
            )

        if not self.is_authenticated():
            return CLICommandResult(
                success=False,
                output="",
                error=f"Authentication required. Please set {self._config.api_key_env} "
                      "environment variable.",
                exit_code=1,
            )

        timeout = kwargs.get("timeout", self._config.timeout)
        input_text = kwargs.get("input_text")
        working_dir = kwargs.get("working_dir", self._config.working_dir)

        cmd = self._build_command(command, **kwargs)
        env = self._get_env()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                env=env,
                input=input_text,
                check=False,
            )

            return CLICommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else "",
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return CLICommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                exit_code=124,
            )
        except FileNotFoundError:
            return CLICommandResult(
                success=False,
                output="",
                error=f"CLI executable not found: {self._config.executable}",
                exit_code=127,
            )
        except Exception as e:
            return CLICommandResult(
                success=False,
                output="",
                error=f"Error executing command: {e!s}",
                exit_code=1,
            )


class GeminiCLIAdapter(BaseCLIAdapter):
    """Adapter for Google Gemini CLI integration.

    The Gemini CLI allows interaction with Google's Gemini AI models
    from the command line. This adapter supports:
    - Model queries and completions
    - Code generation and analysis
    - File processing

    Environment Variables:
        GOOGLE_API_KEY: API key for Gemini (or GEMINI_API_KEY)

    CLI Installation:
        npm install -g @anthropic-ai/cli  # Example - actual package may differ
        # Or use Google Cloud SDK with Gemini support
    """

    DEFAULT_EXECUTABLE = "gemini"
    API_KEY_ENVS = ["GOOGLE_API_KEY", "GEMINI_API_KEY"]

    def __init__(
        self,
        executable: str | None = None,
        api_key_env: str | None = None,
        timeout: int = 300,
    ) -> None:
        """Initialize the Gemini CLI adapter.

        Args:
            executable: Override CLI executable name.
            api_key_env: Override API key environment variable name.
            timeout: Default timeout for commands.
        """
        config = CLIConfig(
            executable=executable or self.DEFAULT_EXECUTABLE,
            api_key_env=api_key_env or self.API_KEY_ENVS[0],
            timeout=timeout,
        )
        super().__init__(ExternalCLIType.GEMINI, config)

    def is_authenticated(self) -> bool:
        """Check if authentication credentials are available.

        Checks multiple possible environment variable names for Gemini API key.

        Returns:
            True if any API key environment variable is set.
        """
        return any(os.environ.get(env_var) for env_var in self.API_KEY_ENVS)

    def get_api_key(self) -> str | None:
        """Get the API key from environment.

        Checks multiple possible environment variable names.

        Returns:
            API key or None if not set.
        """
        for env_var in self.API_KEY_ENVS:
            key = os.environ.get(env_var)
            if key:
                return key
        return None

    def generate(self, prompt: str, **kwargs: Any) -> CLICommandResult:
        """Generate content using Gemini.

        Args:
            prompt: The prompt for generation.
            **kwargs: Additional generation options.

        Returns:
            CLICommandResult with generated content.
        """
        model = kwargs.get("model", "gemini-pro")
        command = f"generate --model {model} --prompt"

        # Pass prompt via stdin to avoid shell escaping issues
        return self.execute(command, input_text=prompt, **kwargs)

    def analyze_code(self, code: str, task: str = "review", **kwargs: Any) -> CLICommandResult:
        """Analyze code using Gemini.

        Args:
            code: The code to analyze.
            task: Analysis task (review, explain, improve, etc.).
            **kwargs: Additional options.

        Returns:
            CLICommandResult with analysis.
        """
        prompt = f"Task: {task}\n\nCode:\n```\n{code}\n```"
        return self.generate(prompt, **kwargs)


class CodexCLIAdapter(BaseCLIAdapter):
    """Adapter for OpenAI Codex CLI integration.

    The Codex CLI allows interaction with OpenAI's code models.
    This adapter supports:
    - Code completion and generation
    - Natural language to code translation
    - Code explanation

    Environment Variables:
        OPENAI_API_KEY: API key for OpenAI Codex

    CLI Installation:
        pip install openai  # OpenAI Python package includes CLI
        # Or: npm install -g openai-cli
    """

    DEFAULT_EXECUTABLE = "openai"
    API_KEY_ENV = "OPENAI_API_KEY"

    def __init__(
        self,
        executable: str | None = None,
        api_key_env: str | None = None,
        timeout: int = 300,
    ) -> None:
        """Initialize the Codex CLI adapter.

        Args:
            executable: Override CLI executable name.
            api_key_env: Override API key environment variable name.
            timeout: Default timeout for commands.
        """
        config = CLIConfig(
            executable=executable or self.DEFAULT_EXECUTABLE,
            api_key_env=api_key_env or self.API_KEY_ENV,
            timeout=timeout,
        )
        super().__init__(ExternalCLIType.CODEX, config)

    def complete(self, prompt: str, **kwargs: Any) -> CLICommandResult:
        """Complete code using Codex.

        Args:
            prompt: The prompt for completion.
            **kwargs: Additional options (model, max_tokens, temperature, etc.).

        Returns:
            CLICommandResult with completion.
        """
        model = kwargs.get("model", "gpt-4")
        max_tokens = kwargs.get("max_tokens", 2048)

        command = f"api completions.create -m {model} --max-tokens {max_tokens} -p"
        return self.execute(command, input_text=prompt, **kwargs)

    def chat(self, message: str, **kwargs: Any) -> CLICommandResult:
        """Chat with the model.

        Args:
            message: The user message.
            **kwargs: Additional options.

        Returns:
            CLICommandResult with response.
        """
        model = kwargs.get("model", "gpt-4")
        command = f"api chat.completions.create -m {model} --message"
        return self.execute(command, input_text=message, **kwargs)


class CopilotCLIAdapter(BaseCLIAdapter):
    """Adapter for GitHub Copilot CLI integration.

    The Copilot CLI (gh copilot) provides AI-powered command-line assistance.
    This adapter supports:
    - Command suggestions
    - Code explanations
    - Git workflow assistance

    Prerequisites:
        - GitHub CLI (gh) installed
        - Copilot CLI extension installed: gh extension install github/gh-copilot
        - Authenticated with GitHub: gh auth login

    Environment Variables:
        GITHUB_TOKEN: GitHub authentication token (optional if gh auth is used)
    """

    DEFAULT_EXECUTABLE = "gh"
    TOKEN_ENV = "GITHUB_TOKEN"

    def __init__(
        self,
        executable: str | None = None,
        timeout: int = 300,
    ) -> None:
        """Initialize the Copilot CLI adapter.

        Args:
            executable: Override CLI executable name.
            timeout: Default timeout for commands.
        """
        config = CLIConfig(
            executable=executable or self.DEFAULT_EXECUTABLE,
            api_key_env=None,  # Copilot uses gh auth, not API key
            timeout=timeout,
            extra_args=["copilot"],
        )
        super().__init__(ExternalCLIType.COPILOT, config)

    def is_available(self) -> bool:
        """Check if gh copilot is available.

        Checks for both gh CLI and copilot extension.

        Returns:
            True if gh copilot is available.
        """
        # First check if gh is available
        gh_path = shutil.which(self._config.executable)
        if not gh_path:
            return False

        self._executable_path = gh_path

        # Check if copilot extension is installed
        try:
            result = subprocess.run(
                [gh_path, "copilot", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_authenticated(self) -> bool:
        """Check if GitHub authentication is available.

        Returns:
            True if gh auth status indicates logged in.
        """
        gh_path = self._executable_path or shutil.which(self._config.executable)
        if not gh_path:
            return False

        try:
            result = subprocess.run(
                [gh_path, "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def suggest(self, query: str, **kwargs: Any) -> CLICommandResult:
        """Get command suggestions from Copilot.

        Args:
            query: Natural language query for command suggestion.
            **kwargs: Additional options.

        Returns:
            CLICommandResult with suggested commands.
        """
        command = f"suggest \"{query}\""
        return self.execute(command, **kwargs)

    def explain(self, command_to_explain: str, **kwargs: Any) -> CLICommandResult:
        """Get explanation for a command.

        Args:
            command_to_explain: The command to explain.
            **kwargs: Additional options.

        Returns:
            CLICommandResult with explanation.
        """
        command = f"explain \"{command_to_explain}\""
        return self.execute(command, **kwargs)


class PlaceholderCLIAdapter(BaseCLIAdapter):
    """Placeholder adapter for custom or unsupported CLI tools.

    This adapter serves as a fallback for CLI types that don't have
    a specific implementation yet.
    """

    def __init__(self, cli_type: ExternalCLIType) -> None:
        """Initialize the placeholder adapter.

        Args:
            cli_type: The type of CLI this adapter handles.
        """
        config = CLIConfig(
            executable=cli_type.value,
            api_key_env=None,
            timeout=300,
        )
        super().__init__(cli_type, config)


def get_cli_adapter(
    cli_type: ExternalCLIType,
    **kwargs: Any,
) -> ExternalCLIPort:
    """Factory function to get a CLI adapter by type.

    Args:
        cli_type: The type of CLI adapter to create.
        **kwargs: Additional configuration options passed to the adapter.

    Returns:
        An ExternalCLIPort implementation.
    """
    if cli_type == ExternalCLIType.GEMINI:
        return GeminiCLIAdapter(**kwargs)
    elif cli_type == ExternalCLIType.CODEX:
        return CodexCLIAdapter(**kwargs)
    elif cli_type == ExternalCLIType.COPILOT:
        return CopilotCLIAdapter(**kwargs)
    else:
        return PlaceholderCLIAdapter(cli_type)
