from urllib.parse import urlparse, ParseResult, quote

from discord import Member

from lib.music.services.deezer import Deezer
from lib.music.services.hifi_api import HifiApi
from lib.music.services.spotify import Spotify
from lib.music.source import Source


class Resolver:
    def __init__(self, spotify: Spotify, deezer: Deezer, hifi_api: HifiApi) -> None:
        self._spotify = spotify
        self._deezer = deezer
        self._hifi_api = hifi_api

    async def by_url(self, url: str, requester: Member) -> Source:
        parsed = urlparse(url)

        if self._is_spotify_track(parsed):
            return await self._resolve_spotify_track(parsed, requester)

        raise ValueError(f"Unsupported URL: {url}")

    @staticmethod
    def _is_spotify_track(url: ParseResult) -> bool:
        return url.netloc == "open.spotify.com" and "/track/" in url.path

    async def _resolve_spotify_track(self, url: ParseResult, requester: Member) -> Source:
        track_id = url.path.split("/")[-1]
        metadata = await self._spotify.fetch_track(track_id)
        title = metadata["title"]
        artist = metadata["artists"][0]["name"]
        search = quote(f"{title} {artist}")

        isrc = await self._deezer.fetch_isrc(search, track_id)
        stream_url = await self._hifi_api.search(isrc, search)

        if not stream_url:
            raise ValueError(f"Failed to fetch stream for ISRC: {isrc}")

        return Source(str(url), requester, stream_url, metadata=metadata)
