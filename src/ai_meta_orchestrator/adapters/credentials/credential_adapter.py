"""Credential management adapters.

This module provides credential management implementations:
- PlaceholderCredentialManager: Simple in-memory storage for development
- EnvironmentCredentialManager: Environment variable-based credentials
- SecureCredentialManager: Encrypted credential storage
"""

import base64
import hashlib
import os
from typing import Any

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


class EnvironmentCredentialManager(CredentialManagerPort):
    """Environment variable-based credential manager.

    This manager reads credentials from environment variables with
    optional prefix support for namespacing.
    """

    def __init__(
        self,
        prefix: str = "ORCHESTRATOR_",
        fallback_to_direct: bool = True,
    ) -> None:
        """Initialize the environment credential manager.

        Args:
            prefix: Prefix for environment variable names.
            fallback_to_direct: If True, try the key directly without prefix
                               if prefixed key is not found.
        """
        self._prefix = prefix
        self._fallback_to_direct = fallback_to_direct
        self._overrides: dict[str, str] = {}

    def _get_env_key(self, key: str) -> str:
        """Get the environment variable key for a credential key."""
        return f"{self._prefix}{key.upper()}"

    def get_credential(self, key: str) -> str | None:
        """Get a credential from environment or overrides.

        Args:
            key: The credential key.

        Returns:
            The credential value or None if not found.
        """
        # First check overrides
        if key in self._overrides:
            return self._overrides[key]

        # Try with prefix
        env_key = self._get_env_key(key)
        value = os.environ.get(env_key)
        if value is not None:
            return value

        # Fallback to direct key
        if self._fallback_to_direct:
            return os.environ.get(key.upper())

        return None

    def set_credential(self, key: str, value: str) -> bool:
        """Set a credential override.

        Note: This doesn't modify actual environment variables,
        only sets an in-memory override.

        Args:
            key: The credential key.
            value: The credential value.

        Returns:
            True if successful.
        """
        self._overrides[key] = value
        return True

    def has_credential(self, key: str) -> bool:
        """Check if a credential exists.

        Args:
            key: The credential key.

        Returns:
            True if the credential exists.
        """
        return self.get_credential(key) is not None

    def list_available_credentials(self) -> list[str]:
        """List all available credential keys (prefixed env vars).

        Returns:
            List of credential keys found in environment.
        """
        credentials = []
        for key in os.environ:
            if key.startswith(self._prefix):
                # Remove prefix and return the key name
                cred_key = key[len(self._prefix):]
                credentials.append(cred_key.lower())
        return credentials


class SecureCredentialManager(CredentialManagerPort):
    """Secure credential manager with encryption support.

    This manager provides encrypted storage of credentials with
    key derivation from a master password or environment variable.

    Note: This is a basic implementation. For production use,
    consider using a dedicated secrets management service like
    AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault.
    """

    def __init__(
        self,
        encryption_key: str | None = None,
        storage_backend: CredentialManagerPort | None = None,
    ) -> None:
        """Initialize the secure credential manager.

        Args:
            encryption_key: Key used for encryption. If None, uses
                           ORCHESTRATOR_ENCRYPTION_KEY environment variable.
            storage_backend: Backend for storing encrypted credentials.
                            Defaults to PlaceholderCredentialManager.
        """
        self._key = encryption_key or os.environ.get("ORCHESTRATOR_ENCRYPTION_KEY", "")
        self._backend = storage_backend or PlaceholderCredentialManager()
        self._derived_key: bytes | None = None

        if self._key:
            self._derived_key = self._derive_key(self._key)

    def _derive_key(self, password: str) -> bytes:
        """Derive an encryption key from a password.

        Args:
            password: The password to derive from.

        Returns:
            32-byte derived key.
        """
        # Simple key derivation using SHA-256
        # For production, use a proper KDF like PBKDF2, scrypt, or Argon2
        return hashlib.sha256(password.encode()).digest()

    def _xor_encrypt(self, data: str, key: bytes) -> str:
        """Simple XOR encryption.

        Note: This is NOT secure for production use. Use proper encryption
        (e.g., Fernet, AES-GCM) for real security requirements.

        Args:
            data: The data to encrypt.
            key: The encryption key.

        Returns:
            Base64-encoded encrypted data.
        """
        data_bytes = data.encode()
        encrypted = bytes(
            data_bytes[i] ^ key[i % len(key)]
            for i in range(len(data_bytes))
        )
        return base64.b64encode(encrypted).decode()

    def _xor_decrypt(self, encrypted_data: str, key: bytes) -> str:
        """Simple XOR decryption.

        Args:
            encrypted_data: Base64-encoded encrypted data.
            key: The encryption key.

        Returns:
            Decrypted data.
        """
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = bytes(
            encrypted[i] ^ key[i % len(key)]
            for i in range(len(encrypted))
        )
        return decrypted.decode()

    def get_credential(self, key: str) -> str | None:
        """Get and decrypt a credential.

        Args:
            key: The credential key.

        Returns:
            The decrypted credential value or None if not found.
        """
        encrypted = self._backend.get_credential(key)
        if encrypted is None:
            return None

        if self._derived_key is None:
            return encrypted  # No encryption configured

        try:
            return self._xor_decrypt(encrypted, self._derived_key)
        except Exception:
            return None

    def set_credential(self, key: str, value: str) -> bool:
        """Encrypt and store a credential.

        Args:
            key: The credential key.
            value: The credential value.

        Returns:
            True if successful.
        """
        if self._derived_key is not None:
            encrypted = self._xor_encrypt(value, self._derived_key)
        else:
            encrypted = value

        return self._backend.set_credential(key, encrypted)

    def has_credential(self, key: str) -> bool:
        """Check if a credential exists.

        Args:
            key: The credential key.

        Returns:
            True if the credential exists.
        """
        return self._backend.has_credential(key)

    @property
    def is_encrypted(self) -> bool:
        """Check if encryption is enabled."""
        return self._derived_key is not None


def create_credential_manager(
    manager_type: str = "environment",
    **kwargs: Any,
) -> CredentialManagerPort:
    """Factory function to create a credential manager.

    Args:
        manager_type: Type of manager ("placeholder", "environment", "secure").
        **kwargs: Additional arguments for the manager.

    Returns:
        A CredentialManagerPort implementation.
    """
    if manager_type == "secure":
        return SecureCredentialManager(**kwargs)
    elif manager_type == "environment":
        return EnvironmentCredentialManager(**kwargs)
    return PlaceholderCredentialManager()
