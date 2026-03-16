from asyncio import Event, create_task, TimeoutError, wait_for
from collections import deque
from typing import Any

from discord import Message, Forbidden, HTTPException, NotFound

from lib.contexts import CustomApplicationContext
from lib.enums import AudioPlayerLoopMode
from lib.logger import get_logger
from lib.music.queue import SongQueue
from lib.music.song import Song
from lib.music.source import TidalSource

log = get_logger(__name__)


class Player:
    def __init__(self, ctx: CustomApplicationContext) -> None:
        self.ctx = ctx

        self._queue = SongQueue(maxsize=200)
        self._current = None
        self._message = None
        self._voice = None

        self._event = Event()
        self._skip_votes = set()
        self._loop = AudioPlayerLoopMode.NONE
        self._history = deque(maxlen=5)

        self._task = create_task(self._run())

    @property
    def active(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def message(self) -> Message:
        return self._message

    @message.setter
    def message(self, message: Message) -> None:
        if self.message is not None:
            try:
                create_task(self.message.delete())
            except (Forbidden, HTTPException, NotFound):
                pass
        self._message = message

    async def _run(self) -> None:
        while True:
            self._event.clear()
            self._current = None
            self.message = None

            try:
                song = await wait_for(self._queue.get(), timeout=300)
            except TimeoutError:
                return

            if isinstance(song.source, str):
                try:
                    source = await TidalSource.from_url(song.source, song.requester)
                except Exception as e:
                    log.error(f"Failed to play song: {e}")
                    continue
                song = Song(source)

            self._current = song
            self._voice.play((song.source, song.requester), after=self._prepare_next)
            self.message = await self.send(embed=song.get_embed(self._loop, self._queue[:5]))
            await self._event.wait()

    def _prepare_next(self, error=None) -> None:
        if error:
            log.error(f"Player prepare_next method failed: {error}")
        self._skip_votes.clear()
        self._event.set()

    async def send(self, *args: Any, **kwargs: Any) -> Message | None:
        try:
            return await self.ctx.send(*args, **kwargs)
        except (Forbidden, HTTPException):
            pass
