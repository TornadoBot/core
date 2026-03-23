from urllib.parse import quote

from aiohttp import ClientSession
from redis.asyncio import Redis
from typing_extensions import overload

from lib.utils import find_key


class Deezer:
    """Client for fetching ISRC codes via the Deezer search API.

    ISRC codes are cached in Redis indefinitely, identified by Spotify track ID.
    """

    SEARCH_URL = "https://api.deezer.com/search/track"

    def __init__(self, session: ClientSession, redis: Redis) -> None:
        """
        :param session: Shared aiohttp client session.
        :param redis: Async Redis client for caching.
        """
        self._session = session
        self._redis = redis


    async def fetch_isrc(self, search: str, track_id: str) -> str:
        """
        Fetch the ISRC code for a track by search.
        Returns the cached value if available, otherwise queries the Deezer API.

        :param search: The track title.
        :param track_id: The Spotify track ID, used as the cache key.
        :returns: The ISRC code.
        """
        key = f"isrc:{track_id}"
        if data := await self._redis.get(key):
            return data.decode()

        url = f"{self.SEARCH_URL}?q={search}&limit=1"
        return await self._fetch(url, key)

    async def _fetch(self, url: str, key: str) -> str:
        """Fetch the Deezer search results and extract the ISRC code.

        :param url: The Deezer search URL to fetch.
        :param key: The Redis key to cache the result under.
        :returns: The ISRC code.
        :raises aiohttp.ClientResponseError: If the HTTP request fails.
        :raises ValueError: If no ISRC code is found in the response.
        """
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()

        isrc = find_key(data, "isrc")
        if isrc is None:
            raise ValueError(f"No entity found in response for {url}")

        await self._redis.set(key, isrc)
        return isrc