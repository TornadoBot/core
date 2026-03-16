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

    async def get_tidal_id(self, url: str) -> str:
        async with self._limiter:
            return await self._request(url)

    @staticmethod
    async def _request(url: str) -> str:
        async with ClientSession().get(
                f"https://api.song.link/v1-alpha.1/links?url={url}"
        ) as response:
            if response.status != 200:
                raise Exception("Failed to extract Tidal ID")

            data: dict = await response.json()

            try:
                key: str = [k.startswith("TIDAL_SONG::") for k in data.keys()][0]
                return data[key]["id"]
            except (KeyError, IndexError):
                raise Exception("Failed to extract Tidal ID")

