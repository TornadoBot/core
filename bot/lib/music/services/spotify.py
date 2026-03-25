from json import loads

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from redis.asyncio import Redis

from lib.music.dto.spotify_dto import SpotifyTrack
from lib.utils import find_key


class Spotify:
    """Client for fetching track metadata from the Spotify embed page.

    Metadata is cached in Redis and identified by type and ID.
    Only the entity object is extracted and stored.
    """

    EMBED_URL = "https://open.spotify.com/embed/"

    def __init__(self, session: ClientSession, redis: Redis) -> None:
        """
        :param session: Shared aiohttp client session.
        :param redis: Async Redis client for caching.
        """
        self._session = session
        self._redis = redis

    async def fetch_track(self, track_id: str) -> SpotifyTrack:
        """Fetch metadata for a Spotify track.

        :param track_id: The Spotify track ID.
        :returns: The entity object containing track metadata.
        """
        return await self._acquire("track", track_id)

    async def _acquire(self, _type: str, _id: str) -> SpotifyTrack:
        """Return an entity from the cache or fetch it from Spotify.

        :param _type: The entity type, e.g. ``track``.
        :param _id: The entity ID.
        :returns: The entity object.
        """
        key = f"spotify:{_type}:{_id}"
        if data := await self._redis.get(key):
            return SpotifyTrack.from_json(data)
        url = f"{self.EMBED_URL}{_type}/{_id}"
        return await self._fetch(url, key)

    async def _fetch(self, url: str, key: str) -> SpotifyTrack:
        """Fetch the Spotify embed page and extract the entity object.

        Parses the ``__NEXT_DATA__`` script tag from the HTML response
        and recursively searches for the entity object.

        :param url: The Spotify embed URL to fetch.
        :param key: The Redis key to cache the result under.
        :returns: The entity object.
        :raises aiohttp.ClientResponseError: If the HTTP request fails.
        :raises ValueError: If no entity object is found in the response.
        """
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        data = loads(tag.string)
        entity = find_key(data, "entity")

        if entity is None:
            raise ValueError(f"No entity found in response for {url}")
        entry = SpotifyTrack.from_dict(entity)
        await self._redis.set(key, entry.to_json(), ex=60 * 60 * 24 * 180)
        return entry

