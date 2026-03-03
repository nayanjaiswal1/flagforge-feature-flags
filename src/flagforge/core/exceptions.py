"""FlagForge exception hierarchy."""


class FlagForgeError(Exception):
    """Base exception for all FlagForge errors."""

    def __init__(self, message: str = "An error occurred in FlagForge"):
        self.message = message
        super().__init__(self.message)


class StorageError(FlagForgeError):
    """Raised when storage operations fail."""

    def __init__(self, message: str = "Storage operation failed"):
        self.message = message
        super().__init__(self.message)


class CacheError(FlagForgeError):
    """Raised when cache operations fail."""

    def __init__(self, message: str = "Cache operation failed"):
        self.message = message
        super().__init__(self.message)
