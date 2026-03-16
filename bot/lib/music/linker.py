from aiohttp import ClientSession
from aiolimiter import AsyncLimiter


class Linker:
    _instance: "Linker" = None

    def __new__(cls, *args, **kwargs) -> "Linker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._instance is not None:
            return

        self._limiter = AsyncLimiter(max_rate=10, time_period=60)

    async def fetch_tidal(self, url: str) -> dict:
        async with self._limiter:
            data = await self._request(url)
            key: str = [k.startswith("TIDAL_SONG::") for k in data.keys()][0]
            return data[key]

    @staticmethod
    async def _request(url: str) -> dict:
        async with ClientSession().get(
                f"https://api.song.link/v1-alpha.1/links?url={url}"
        ) as response:
            try:
                if response.status != 200:
                    raise Exception("Failed to extract data from Tidal")
                return await response.json()
            except (KeyError, IndexError):
                raise Exception("Failed to extract data from Tidal")

