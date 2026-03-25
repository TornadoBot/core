from urllib.parse import urlparse, quote

from lib.music.dto.spotify_dto import SpotifyTrack
from lib.music.services.hifi_api import HifiApi
from lib.music.services.spotify import Spotify
from lib.music.song import Song
from lib.music.source import Source


class Resolver:
    def __init__(self, spotify: Spotify, hifi_api: HifiApi) -> None:
        self._spotify = spotify
        self._hifi_api = hifi_api

    async def resolve(self, song: Song) -> None:
        url = urlparse(song.url)
        track_id = url.path.split("/")[-1]
        metadata: SpotifyTrack = await self._spotify.fetch_track(track_id)
        title = metadata.title
        artists = metadata.artist_names
        search = quote(f"{title} {artists}")
        stream_url = await self._hifi_api.by_search(search)

        if not stream_url:
            raise ValueError(f"Failed to fetch stream for: {search}")

        song.resolve(metadata, Source(stream_url))
