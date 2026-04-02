from base64 import b64decode
from json import loads
from urllib.parse import quote

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

    async def by_isrc(self, isrc: str) -> str | None:
        """Fetch a stream URL for the given ISRC code.

        Iterates through all known proxy services and returns the first
        working stream URL. Returns ``None`` if no service succeeds.

        :param isrc: The ISRC code to fetch a stream for.
        :returns: A stream URL, or ``None`` if no service returned one.
        """
        return await self._query_by(isrc=isrc)

    async def by_search(self, search: str) -> str | None:
        """Fetch a stream URL for the given search query.

        Iterates through all known proxy services and returns the first
        working stream URL. Returns ``None`` if no service succeeds.

        :param search: The search query to fetch a stream for.
        :returns: A stream URL, or ``None`` if no service returned one.
        """
        return await self._query_by(search=search)

    async def _query_by(self, isrc: str = None, search: str = None) -> str | None:
        """Fetch a stream URL for the given ISRC code or search query.

        Iterates through all known proxy services and returns the first
        working stream URL. Returns ``None`` if no service succeeds.

        :param isrc: The isrc to fetch a stream for.
        :param search: The search query to fetch a stream for.
        :returns: A stream URL, or ``None`` if no service returned one.
        """

        query = isrc or quote(search)
        if not query:
            return None
        param_name = "i" if isrc else "s"

        for service in self.APIS:
            try:
                tidal_id = await self._search(service, param_name, query)
            except ValueError:
                log.warning("%s failed to resolve tidal id for %s", service, query)
                continue
            except ClientError as e:
                log.error("%s failed: %s", service, e)
                continue
            break
        else:
            return None

        for service in self.APIS:
            try:
                stream_url = await self._manifest(service, tidal_id)
            except ValueError:
                log.warning("Service %s resolve stream for tidal id %s", service, tidal_id)
                continue
            except ClientError as e:
                log.error("%s failed: %s", service, e)
                continue
            break
        else:
            return None

        log.info("Resolved stream for %s via %s", query, service)
        return stream_url

    async def _search(self, provider: str, param_name: str, query: str) -> str:
        """Resolve a Tidal track ID from a search query.

        Returns the cached value if available, otherwise queries the provider.

        :param provider: The base URL of the proxy service.
        :param param_name: The parameter name to search by (e.g., ``s`` for ``track``).
        :param query: The search query.

        :returns: The Tidal track ID.

        :raises ValueError: If no valid Tidal ID is found in the response.
        :raises aiohttp.ClientError: If the HTTP request fails.
        """
        key = f"tidal:search:{query}"
        if data := await self._redis.get(key):
            tidal_id = data.decode()
            log.debug("Cache hit for %s -> tidal id %s", query, tidal_id)
            return tidal_id

        async with self._session.get(
            f"{provider}/search/",
            params={param_name: query, "limit": 1},
            timeout=ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        items = find_key(data, "items")
        if not items:
            raise ValueError("No items in response for %s" % query)

        try:
            tidal_id = str(items[0]["id"])
        except (TypeError, IndexError, KeyError) as e:
            raise ValueError("Invalid item structure for %s" % query) from e

        ex = {
            "i": None,
            "s": 60 * 60 * 24 * 30,
        }
        await self._redis.set(key, tidal_id, ex=ex[param_name])
        log.debug("Resolved %s -> tidal id %s via %s", query, tidal_id, provider)
        return tidal_id

    async def _manifest(self, provider: str, tidal_id: str) -> str:
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