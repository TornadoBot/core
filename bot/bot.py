from os import environ

from aiohttp import ClientSession
from discord import Bot
from redis.asyncio import Redis

from lib.logger import get_logger
from lib.music.resolver import Resolver
from lib.music.services.hifi_api import HifiApi
from lib.music.services.reccobeats import ReccoBeats
from lib.music.services.spotify import Spotify
from lib.tor import Tor

log = get_logger(__name__)


class TornadoBot(Bot):
    REDIS_HOST = environ.get("REDIS_HOST") or "127.0.0.1"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._session = None
        self._redis = None

        self.proxy = Tor()
        self.spotify = None
        self.reccobeats = None
        self.hifi_api = None
        self.resolver = None

    async def on_connect(self) -> None:
        self._session = ClientSession()
        self._redis = Redis(host=self.REDIS_HOST)

        self.spotify = Spotify(self._session, self._redis)
        self.hifi_api = HifiApi(self._session, self._redis)
        self.reccobeats = ReccoBeats(self._session, self._redis)

        self.resolver = Resolver(self.spotify, self.reccobeats, self.hifi_api)

        await self.proxy.connect()

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user.name} ({self.user.id})")

    async def close(self):
        await self._session.close()
        await self._redis.aclose()
        await self.proxy.disconnect()
        await super().close()
