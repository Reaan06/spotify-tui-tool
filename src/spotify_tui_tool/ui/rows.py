"""Stable browse-row conversion and lookup helpers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from textual.message import Message

from spotify_tui_tool.models import BrowseRow

__all__ = [
    "BrowseRow",
    "row_from_track",
    "row_from_album",
    "row_from_artist",
    "row_from_playlist",
    "rows_from_library",
    "rows_from_playlists",
    "rows_from_search",
    "BrowseRowActivated",
    "activation_uri",
]


class BrowseRowActivated(Message):
    """Bubbled by a browse surface for Enter or a row double-click."""

    def __init__(self, row: BrowseRow) -> None:
        self.row = row
        super().__init__()


def activation_uri(row: BrowseRow) -> str | None:
    """Return only the stored playable URI; never derive one from labels."""
    if row.playable and row.uri:
        return row.uri
    return None


def _names(items: Iterable[dict[str, Any]]) -> str:
    return ", ".join(str(item.get("name", "")) for item in items if item.get("name"))


def _identifier(payload: dict[str, Any], uri: str = "") -> str:
    return str(payload.get("id") or (uri.rsplit(":", 1)[-1] if uri else ""))


def _uri(payload: dict[str, Any]) -> str:
    return str(payload.get("uri") or "")


def row_from_track(track: dict[str, Any], *, kind: str = "track") -> BrowseRow:
    uri = _uri(track)
    duration_ms = int(track.get("duration_ms") or 0)
    duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
    return BrowseRow(
        kind=kind,
        id=_identifier(track, uri),
        uri=uri,
        title=str(track.get("name") or "Unknown"),
        subtitle=_names(track.get("artists", [])),
        playable=kind == "track" and uri.startswith("spotify:track:"),
        detail=str(track.get("album", {}).get("name") or "Unknown"),
        auxiliary=duration,
    )


def row_from_album(album: dict[str, Any]) -> BrowseRow:
    uri = _uri(album)
    return BrowseRow(
        kind="album",
        id=_identifier(album, uri),
        uri=uri,
        title=str(album.get("name") or "Unknown"),
        subtitle=_names(album.get("artists", [])),
        playable=False,
        detail=f"{int(album.get('total_tracks') or 0)} tracks",
    )


def row_from_artist(artist: dict[str, Any]) -> BrowseRow:
    uri = _uri(artist)
    genres = ", ".join(str(genre) for genre in artist.get("genres", [])[:2])
    return BrowseRow(
        kind="artist",
        id=_identifier(artist, uri),
        uri=uri,
        title=str(artist.get("name") or "Unknown"),
        subtitle=genres or "—",
        playable=False,
        detail="—",
    )


def row_from_playlist(playlist: dict[str, Any]) -> BrowseRow:
    uri = _uri(playlist)
    description = str(playlist.get("description") or "")[:50]
    count = int(playlist.get("tracks", {}).get("total") or 0)
    return BrowseRow(
        kind="playlist",
        id=_identifier(playlist, uri),
        uri=uri,
        title=str(playlist.get("name") or "Unknown"),
        subtitle=description,
        playable=False,
        detail=str(count),
    )


def rows_from_library(items: Iterable[dict[str, Any]]) -> list[BrowseRow]:
    """Convert ``/me/tracks`` items without discarding track identity."""
    rows: list[BrowseRow] = []
    for index, item in enumerate(items):
        track = item.get("track", item)
        if isinstance(track, dict):
            row = row_from_track(track, kind="track")
            if not row.id:
                row = replace(row, id=f"index-{index}")
            rows.append(row)
    return rows


def rows_from_playlists(items: Iterable[dict[str, Any]]) -> list[BrowseRow]:
    rows: list[BrowseRow] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        row = row_from_playlist(item)
        if not row.id:
            row = replace(row, id=f"index-{index}")
        rows.append(row)
    return rows


def rows_from_search(results: dict[str, Any]) -> list[BrowseRow]:
    """Convert the bounded track/album/artist search window in display order."""
    rows: list[BrowseRow] = []
    rows.extend(
        row_from_track(track)
        for track in results.get("tracks", {}).get("items", [])
        if isinstance(track, dict)
    )
    rows.extend(
        row_from_album(album)
        for album in results.get("albums", {}).get("items", [])
        if isinstance(album, dict)
    )
    rows.extend(
        row_from_artist(artist)
        for artist in results.get("artists", {}).get("items", [])
        if isinstance(artist, dict)
    )
    unique_rows: list[BrowseRow] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if row.key in seen:
            row = replace(row, id=row.id or f"index-{index}")
            while row.key in seen:
                row = replace(row, id=f"index-{index}-{len(seen)}")
        seen.add(row.key)
        unique_rows.append(row)
    return unique_rows
