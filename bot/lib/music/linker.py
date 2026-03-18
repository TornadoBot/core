from json import dumps, loads
from os import environ
from urllib.parse import quote

from aiohttp import ClientSession
from aiolimiter import AsyncLimiter
from redis.asyncio import Redis

REDIS_HOST = environ.get("REDIS_HOST") or "127.0.0.1"


class Linker:
    _instance: "Linker" = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> "Linker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._limiter = AsyncLimiter(max_rate=10, time_period=60)
        self._redis = Redis(host=REDIS_HOST, port=6379)
        self._session = ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        self._initialized = True

    async def fetch_tidal(self, url: str) -> dict:
        if data := await self._redis.get(url):
            data = loads(data)
        else:
            async with self._limiter:
                data = await self._request(quote(url))
            await self._redis.set(url, dumps(data))

        data = data["entitiesByUniqueId"]
        key: str = [k for k in data.keys() if k.startswith("TIDAL_SONG::")][0]
        return data[key]

    async def _request(self, url: str) -> dict:
        async with self._session.get(
                f"https://api.song.link/v1-alpha.1/links?url={url}"
        ) as response:
            try:
                if response.status != 200:
                    raise Exception(f"Song link response status {response.status}")
                return await response.json()
            except (KeyError, IndexError):
                raise Exception("Failed to extract data from Tidal")

