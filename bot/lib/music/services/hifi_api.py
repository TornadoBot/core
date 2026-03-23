from base64 import b64decode
from json import loads

from aiohttp import ClientError, ClientSession, ClientTimeout
from redis.asyncio import Redis

from lib.logger import get_logger
from lib.utils import find_key

log = get_logger(__name__)


class HifiApi:
    """
    Client for fetching stream URLs from unofficial Tidal API proxies.

    Iterates through a list of known proxy services and returns the first
    working stream URL for a given ISRC code.
    """

    APIS = [
        "https://hifi-one.spotisaver.net",
        "https://hifi-two.spotisaver.net",
        "https://eu-central.monochrome.tf",
        "https://us-west.monochrome.tf",
        "https://api.monochrome.tf",
        "https://monochrome-api.samidy.com",
        "https://tidal.kinoplus.online",
    ]

    def __init__(self, session: ClientSession, redis: Redis) -> None:
        """
        :param session: Shared aiohttp client session.
        :param redis: Async Redis client for caching.
        """
        self._session = session
        self._redis = redis

    async def fetch_stream(self, isrc: str) -> str | None:
        """Fetch a stream URL for the given ISRC code.

        Iterates through all known proxy services and returns the first
        working stream URL. Returns ``None`` if no service succeeds.

        :param isrc: The ISRC code to fetch a stream for.
        :returns: A stream URL, or ``None`` if no service returned one.
        """
        for service in self.APIS:
            try:
                tidal_id = await self._try_for_id(service, isrc)
            except (ValueError, ClientError) as e:
                log.warning("Service %s failed to resolve ISRC %s: %s", service, isrc, e)
                continue

            try:
                stream_url = await self._try_for_stream(service, tidal_id)
            except (ValueError, ClientError) as e:
                log.warning("Service %s failed to fetch stream for tidal id %s: %s", service, tidal_id, e)
                continue

            log.info("Resolved stream for ISRC %s via %s", isrc, service)
            return stream_url

        else:
            log.error("All services failed to resolve stream for ISRC %s", isrc)
            return None

    async def _try_for_id(self, provider: str, isrc: str) -> str:
        """Resolve a Tidal track ID from an ISRC code.

        Returns the cached value if available, otherwise queries the provider.

        :param provider: The base URL of the proxy service.
        :param isrc: The ISRC code to resolve.

        :returns: The Tidal track ID.

        :raises ValueError: If no valid Tidal ID is found in the response.
        :raises aiohttp.ClientError: If the HTTP request fails.
        """
        if data := await self._redis.get(f"tidal:{isrc}"):
            tidal_id = data.decode()
            log.debug("Cache hit for ISRC %s -> tidal id %s", isrc, tidal_id)
            return tidal_id

        async with self._session.get(
            f"{provider}/search/",
            params={"i": isrc, "limit": 1},
            timeout=ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        items = find_key(data, "items")
        if not items:
            raise ValueError("No items in response from %s for ISRC %s" % (provider, isrc))

        try:
            tidal_id = str(items[0]["id"])
        except (TypeError, IndexError, KeyError) as e:
            raise ValueError("Invalid item structure from %s for ISRC %s" % (provider, isrc)) from e

        await self._redis.set(f"tidal:{isrc}", tidal_id)
        log.debug("Resolved ISRC %s -> tidal id %s via %s", isrc, tidal_id, provider)
        return tidal_id

    async def _try_for_stream(self, provider: str, tidal_id: str) -> str:
        """Fetch a stream URL for a given Tidal track ID.

        :param provider: The base URL of the proxy service.
        :param tidal_id: The Tidal track ID.
        :returns: The stream URL.
        :raises ValueError: If the manifest or stream URL cannot be extracted.
        :raises aiohttp.ClientError: If the HTTP request fails.
        """
        async with self._session.get(
            f"{provider}/track/",
            params={"id": tidal_id, "quality": "LOW"},
            timeout=ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        manifest_b64 = find_key(data, "manifest")
        if not manifest_b64:
            raise ValueError("No manifest in response from %s for tidal id %s" % (provider, tidal_id))

        try:
            manifest: dict = loads(b64decode(manifest_b64).decode("utf-8"))
            return manifest["urls"][0]
        except (KeyError, IndexError, ValueError) as e:
            raise ValueError("Invalid manifest from %s for tidal id %s" % (provider, tidal_id)) from e