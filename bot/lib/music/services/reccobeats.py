from aiohttp import ClientSession
from aiolimiter import AsyncLimiter
from redis.asyncio import Redis

from lib.logger import get_logger
from lib.utils import find_key

log = get_logger(__name__)

class ReccoBeats:
    API_URL = "https://api.reccobeats.com"

    def __init__(self, session: ClientSession, redis: Redis) -> None:
        self._session = session
        self._redis = redis
        self._limiter = AsyncLimiter(max_rate=3, time_period=5)

    async def get_isrc(self, track_id: str) -> str:
        key = f"reccobeats:isrc:{track_id}"
        if data := await self._redis.get(key):
            return data.decode()
        return await self._acquire(track_id, key)

    async def _acquire(self, track_id: str, key: str) -> str:
        path = f"/v1/track"
        async with self._limiter:
            async with self._session.get(
                    f"{self.API_URL}{path}",
                    params={"ids": track_id}
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        isrc: str | None = find_key(data, "isrc")

        if not isrc:
            log.info("No isrc found for track %s", track_id)

        await self._redis.set(key, isrc, ex=60 * 60 * 24 * 180)
        log.info("isrc found for track %s", track_id)
        return isrc