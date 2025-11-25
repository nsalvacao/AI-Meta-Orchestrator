"""Placeholder credential management adapter.

This adapter is a placeholder for future credential management implementation.
It will eventually support:
- Secure storage of API keys
- Environment variable integration
- Secret management services (AWS Secrets Manager, Azure Key Vault, etc.)
- Credential rotation
"""

from ai_meta_orchestrator.ports.external_ports.external_port import CredentialManagerPort


class PlaceholderCredentialManager(CredentialManagerPort):
    """Placeholder credential manager.

    This is a simple in-memory implementation for development purposes.
    In production, this should be replaced with a secure credential store.

    WARNING: Do not use this implementation for storing real credentials
    in production environments.
    """

    def __init__(self) -> None:
        """Initialize the placeholder credential manager."""
        self._credentials: dict[str, str] = {}
        self._warning_issued = False

    def _warn_placeholder(self) -> None:
        """Issue a warning that this is a placeholder implementation."""
        if not self._warning_issued:
            import warnings

            warnings.warn(
                "Using placeholder credential manager. "
                "Do not use for production credentials.",
                UserWarning,
                stacklevel=3,
            )
            self._warning_issued = True

    def get_credential(self, key: str) -> str | None:
        """Get a credential by key.

        Args:
            key: The credential key.

        Returns:
            The credential value or None if not found.
        """
        self._warn_placeholder()
        return self._credentials.get(key)

    def set_credential(self, key: str, value: str) -> bool:
        """Set a credential.

        Args:
            key: The credential key.
            value: The credential value.

        Returns:
            True if successful.
        """
        self._warn_placeholder()
        self._credentials[key] = value
        return True

    def has_credential(self, key: str) -> bool:
        """Check if a credential exists.

        Args:
            key: The credential key.

        Returns:
            True if the credential exists.
        """
        return key in self._credentials
