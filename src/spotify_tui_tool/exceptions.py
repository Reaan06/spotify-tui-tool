"""Exception hierarchy for the Spotify TUI Tool.

Every exception is a thin subclass of ``Exception`` so callers can decide
whether to catch individually or broadly.  The most specific errors carry
a human-readable message that matches the spec's acceptance criteria.
"""


class PlayerctlNotFoundError(Exception):
    """Raised when the ``playerctl`` binary is not on ``$PATH``."""

    def __init__(self) -> None:
        super().__init__("playerctl not found")


class SpotifyNotRunningError(Exception):
    """Raised when playerctl is installed but no MPRIS player is running."""

    def __init__(self) -> None:
        super().__init__("No player is running. Start Spotify (or SpotX-patched client) and try again.")


class InvalidURIError(Exception):
    """Raised when a string fails Spotify URI validation."""

    def __init__(self, uri: str) -> None:
        super().__init__(f"Invalid Spotify URI: {uri!r}")


class PlaybackError(Exception):
    """Raised when a playerctl command exits with a non-zero status.

    Attributes:
        stderr: The stderr output captured from playerctl, if any.
    """

    def __init__(self, message: str, stderr: str = "") -> None:
        self.stderr = stderr or message
        super().__init__(message)
