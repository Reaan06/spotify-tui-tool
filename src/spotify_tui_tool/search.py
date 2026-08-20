"""SearchService — Spotify URI validation, opening, and history.

Phase 1 (MVP) supports manual URI paste only.  Web scraping is deferred.

Design (from exploration.md):
    SPOTIFY_URI_PATTERN   → regex for spotify:type:22char-id
    validate_uri()        → Optional[ParsedURI]  (None for invalid)
    parse_uri()           → ParsedURI            (raises InvalidURIError)
    open_uri()            → validate → playerctl open → add to history
    history (property)    → last-10, most-recent-first, de-duplicated
"""

from __future__ import annotations

import re
from typing import Optional

from spotify_tui_tool.exceptions import InvalidURIError
from spotify_tui_tool.models import ParsedURI
from spotify_tui_tool.playerctl import PlayerController


class SearchService:
    """Validate, parse, and open Spotify URIs via ``playerctl``.

    Parameters:
        player: A :class:`PlayerController` instance.  When omitted a new
            default instance (player name ``spotify``) is created.
    """

    #: Valid Spotify URI types.
    VALID_TYPES = ("track", "album", "playlist", "artist", "show", "episode")

    #: Matches ``spotify:<type>:<22-char-id>`` — case-sensitive, exact length.
    SPOTIFY_URI_PATTERN = re.compile(
        r"spotify:(track|album|playlist|artist|show|episode):([a-zA-Z0-9]{22})"
    )

    #: Matches ``https://open.spotify.com/<type>/<22-char-id>`` URLs.
    SPOTIFY_URL_PATTERN = re.compile(
        r"https://open\.spotify\.com/(track|album|playlist|artist|show|episode)/"
        r"([a-zA-Z0-9]{22})"
    )

    def __init__(self, player: Optional[PlayerController] = None) -> None:
        self._player = player if player is not None else PlayerController()
        self._history: list[ParsedURI] = []

    # ------------------------------------------------------------------
    # Validation & parsing
    # ------------------------------------------------------------------

    def validate_uri(self, uri: str) -> Optional[ParsedURI]:
        """Return a :class:`ParsedURI` if *uri* is valid, else ``None``.

        Handles both `spotify:type:id` URIs and
        `https://open.spotify.com/type/id` URLs.  Leading/trailing
        whitespace is stripped before matching.
        """
        uri = uri.strip()

        # Native spotify: URI
        match = self.SPOTIFY_URI_PATTERN.fullmatch(uri)
        if match:
            return ParsedURI(type=match.group(1), id=match.group(2), uri=uri)

        # open.spotify.com URL
        match = self.SPOTIFY_URL_PATTERN.fullmatch(uri)
        if match:
            uri_type, uri_id = match.group(1), match.group(2)
            return ParsedURI(
                type=uri_type,
                id=uri_id,
                uri=f"spotify:{uri_type}:{uri_id}",
            )

        return None

    def parse_uri(self, uri: str) -> ParsedURI:
        """Parse *uri* into a :class:`ParsedURI`.

        Raises:
            InvalidURIError: If *uri* does not match any known format.
        """
        result = self.validate_uri(uri)
        if result is None:
            raise InvalidURIError(uri.strip())
        return result

    # ------------------------------------------------------------------
    # Opening
    # ------------------------------------------------------------------

    def open_uri(self, uri: str) -> None:
        """Validate, open via playerctl, and record in history.

        Raises:
            InvalidURIError: If *uri* is malformed.
            PlaybackError: If playerctl fails to open the URI.
        """
        parsed = self.parse_uri(uri)
        self._player.open_uri(parsed.uri)
        self._add_to_history(parsed)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    @property
    def history(self) -> list[ParsedURI]:
        """Most-recent-first copy of the search history (max 10)."""
        return list(self._history)

    def _add_to_history(self, parsed: ParsedURI) -> None:
        """Insert *parsed* at front, de-duplicate, cap at 10 entries."""
        self._history = [h for h in self._history if h.uri != parsed.uri]
        self._history.insert(0, parsed)
        if len(self._history) > 10:
            self._history = self._history[:10]
