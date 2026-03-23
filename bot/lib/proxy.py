from asyncio import Server
from os import environ

from pproxy import Server as PProxy, Connection

from lib.logger import get_logger

TOR_HOST = environ.get("TOR_HOST") or "127.0.0.1"

log = get_logger(__name__)


class Proxy:
    _handler: Server | None = None

    async def start(self) -> None:
        if self._handler:
            log.debug("Proxy already running, skipping start")
            return

        log.debug("Starting proxy on 127.0.0.1:8080 tunneling via %s:9050", TOR_HOST)
        server = PProxy("http://127.0.0.1:8080")
        remote = Connection(f"socks5://{TOR_HOST}:9050")
        self._handler = await server.start_server({"rserver": [remote]})
        log.info("Proxy started: 127.0.0.1:8080 tunneling via %s:9050", TOR_HOST)

    async def stop(self) -> None:
        if not self._handler:
            log.debug("Proxy not running, skipping stop")
            return

        log.debug("Stopping proxy...")
        self._handler.close()
        await self._handler.wait_closed()
        self._handler = None
        log.info("Proxy stopped")