"""Git and CI/CD adapters.

This module provides implementations for Git and CI/CD operations.
- PlaceholderGitCICDAdapter: Stub implementation
- GitCICDAdapter: Functional Git operations using subprocess
"""

import os
import subprocess
from typing import Any

from ai_meta_orchestrator.ports.external_ports.external_port import GitCICDPort


class PlaceholderGitCICDAdapter(GitCICDPort):
    """Placeholder Git and CI/CD adapter.

    This adapter provides stub implementations for Git and CI/CD operations.
    Real implementation will be added in future versions.
    """

    def __init__(self) -> None:
        """Initialize the placeholder adapter."""
        self._current_branch: str | None = None

    def get_current_branch(self) -> str | None:
        """Get the current Git branch.

        Returns:
            None - placeholder not implemented.
        """
        # Placeholder: In future, this will use gitpython or subprocess
        return None

    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch.

        Args:
            branch_name: Name of the branch to create.

        Returns:
            False - placeholder not implemented.
        """
        # Placeholder: In future, this will create actual branches
        return False

    def commit_changes(self, message: str) -> bool:
        """Commit current changes.

        Args:
            message: The commit message.

        Returns:
            False - placeholder not implemented.
        """
        # Placeholder: In future, this will create actual commits
        return False

    def trigger_pipeline(self, pipeline_name: str) -> str | None:
        """Trigger a CI/CD pipeline.

        Args:
            pipeline_name: Name of the pipeline to trigger.

        Returns:
            None - placeholder not implemented.
        """
        # Placeholder: In future, this will trigger actual pipelines
        return None


class GitCICDAdapter(GitCICDPort):
    """Functional Git and CI/CD adapter.

    This adapter provides real Git operations using subprocess.
    It supports basic Git operations and can be extended for CI/CD integration.
    """

    def __init__(self, working_dir: str | None = None) -> None:
        """Initialize the Git adapter.

        Args:
            working_dir: Optional working directory for Git operations.
                        Defaults to current directory.
        """
        self._working_dir = working_dir or os.getcwd()
        self._git_available = self._check_git_available()

    def _check_git_available(self) -> bool:
        """Check if Git is available on the system."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a Git command.

        Args:
            *args: Git command arguments.

        Returns:
            CompletedProcess with the result.
        """
        return subprocess.run(
            ["git", *args],
            cwd=self._working_dir,
            capture_output=True,
            text=True,
            check=False,
        )

    def _is_git_repo(self) -> bool:
        """Check if the working directory is a Git repository."""
        result = self._run_git("rev-parse", "--git-dir")
        return result.returncode == 0

    def get_current_branch(self) -> str | None:
        """Get the current Git branch.

        Returns:
            The branch name or None if not in a Git repository.
        """
        if not self._git_available or not self._is_git_repo():
            return None

        result = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch.

        Args:
            branch_name: Name of the branch to create.

        Returns:
            True if successful, False otherwise.
        """
        if not self._git_available or not self._is_git_repo():
            return False

        result = self._run_git("checkout", "-b", branch_name)
        return result.returncode == 0

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout an existing branch.

        Args:
            branch_name: Name of the branch to checkout.

        Returns:
            True if successful, False otherwise.
        """
        if not self._git_available or not self._is_git_repo():
            return False

        result = self._run_git("checkout", branch_name)
        return result.returncode == 0

    def commit_changes(self, message: str) -> bool:
        """Commit current changes.

        Args:
            message: The commit message.

        Returns:
            True if successful, False otherwise.
        """
        if not self._git_available or not self._is_git_repo():
            return False

        # First stage all changes
        add_result = self._run_git("add", "-A")
        if add_result.returncode != 0:
            return False

        # Then commit
        result = self._run_git("commit", "-m", message)
        return result.returncode == 0

    def get_status(self) -> dict[str, Any]:
        """Get the current Git status.

        Returns:
            Dictionary with status information.
        """
        if not self._git_available or not self._is_git_repo():
            return {"available": False}

        result = self._run_git("status", "--porcelain")
        if result.returncode != 0:
            return {"available": True, "error": result.stderr}

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return {
            "available": True,
            "branch": self.get_current_branch(),
            "changes": len(lines),
            "clean": len(lines) == 0,
        }

    def get_log(self, count: int = 10) -> list[dict[str, str]]:
        """Get recent commit log.

        Args:
            count: Number of commits to retrieve.

        Returns:
            List of commit dictionaries.
        """
        if not self._git_available or not self._is_git_repo():
            return []

        result = self._run_git(
            "log",
            f"-{count}",
            "--format=%H|%an|%ae|%s|%ci",
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "subject": parts[3],
                        "date": parts[4],
                    })
        return commits

    def push(self, remote: str = "origin", branch: str | None = None) -> bool:
        """Push changes to remote.

        Args:
            remote: Remote name (default: origin).
            branch: Branch to push (default: current branch).

        Returns:
            True if successful, False otherwise.
        """
        if not self._git_available or not self._is_git_repo():
            return False

        branch = branch or self.get_current_branch()
        if not branch:
            return False

        result = self._run_git("push", remote, branch)
        return result.returncode == 0

    def pull(self, remote: str = "origin", branch: str | None = None) -> bool:
        """Pull changes from remote.

        Args:
            remote: Remote name (default: origin).
            branch: Branch to pull (default: current branch).

        Returns:
            True if successful, False otherwise.
        """
        if not self._git_available or not self._is_git_repo():
            return False

        branch = branch or self.get_current_branch()
        if not branch:
            return False

        result = self._run_git("pull", remote, branch)
        return result.returncode == 0

    def trigger_pipeline(self, pipeline_name: str) -> str | None:
        """Trigger a CI/CD pipeline.

        This is a placeholder for future CI/CD integration.
        Currently returns None as no CI/CD system is configured.

        Args:
            pipeline_name: Name of the pipeline to trigger.

        Returns:
            Pipeline run ID or None if not implemented.
        """
        # Future: Integrate with GitHub Actions, GitLab CI, etc.
        return None

    @property
    def is_available(self) -> bool:
        """Check if Git is available."""
        return self._git_available

    @property
    def is_repository(self) -> bool:
        """Check if the working directory is a Git repository."""
        return self._git_available and self._is_git_repo()


def create_git_adapter(
    working_dir: str | None = None,
    use_placeholder: bool = False,
) -> GitCICDPort:
    """Factory function to create a Git adapter.

    Args:
        working_dir: Optional working directory for Git operations.
        use_placeholder: If True, return the placeholder adapter.

    Returns:
        A GitCICDPort implementation.
    """
    if use_placeholder:
        return PlaceholderGitCICDAdapter()
    return GitCICDAdapter(working_dir=working_dir)
