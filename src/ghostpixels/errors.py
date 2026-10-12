class GhostPixelsError(Exception):
    """Base class for all GhostPixels errors."""


class CapacityError(GhostPixelsError):
    """Raised when data does not fit in the image."""


class NoHiddenDataError(GhostPixelsError):
    """Raised when an image does not contain any GhostPixels data."""


class CorruptDataError(GhostPixelsError):
    """Raised when hidden data is present but damaged or unreadable."""
