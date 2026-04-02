from urllib.parse import urlparse

from lib.logger import get_logger
from lib.music.dto.spotify_dto import SpotifyTrack
from lib.music.services.hifi_api import HifiApi
from lib.music.services.reccobeats import ReccoBeats
from lib.music.services.spotify import Spotify
from lib.music.song import Song
from lib.music.source import Source


log = get_logger(__name__)

class Resolver:
    def __init__(self, spotify: Spotify, reccobeats: ReccoBeats, hifi_api: HifiApi) -> None:
        self._spotify = spotify
        self._hifi_api = hifi_api
        self._reccobeats = reccobeats

    async def resolve(self, song: Song) -> None:
        url = urlparse(song.url)
        track_id = url.path.split("/")[-1]
        metadata: SpotifyTrack = await self._spotify.fetch_track(track_id)

        isrc = await self._reccobeats.get_isrc(track_id)
        title = metadata.title
        artists = metadata.artist_names
        search = f"{title} {artists}"

        stream_url = None
        if isrc:
            stream_url = await self._hifi_api.by_isrc(isrc)

        if not stream_url:
            log.info("Falling back to search %s", search)
            stream_url = await self._hifi_api.by_search(search)

        if not stream_url:
            raise ValueError(f"Failed to fetch stream for: {track_id}")

        song.resolve(metadata, Source(stream_url))
