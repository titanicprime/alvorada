class AlvoradaError(Exception):
    """Base exception for Project Alvorada tooling."""


class ValidationError(AlvoradaError):
    """Raised when validation fails."""


class DictionaryError(AlvoradaError):
    """Raised when canonical dictionary checks fail."""


class CodebookError(AlvoradaError):
    """Raised when codebook validation or translation fails."""


class DeltaError(AlvoradaError):
    """Raised when state-delta replay fails."""


class HashVerificationError(AlvoradaError):
    """Raised when integrity verification fails."""


class LineageError(AlvoradaError):
    """Raised when lineage verification fails."""
