from asyncio import Event, create_task, TimeoutError, wait_for, Task
from collections import deque
from typing import Any

from discord import Message, Forbidden, HTTPException, NotFound
from discord.voice import VoiceClient

from lib.contexts import CustomApplicationContext
from lib.enums import AudioPlayerLoopMode
from lib.logger import get_logger
from lib.music.queue import SongQueue
from lib.music.song import Song

log = get_logger(__name__)


class Player:
    def __init__(self, ctx: CustomApplicationContext) -> None:
        self.ctx = ctx

        self._queue = SongQueue(maxsize=200)
        self._resolver = ctx.bot.resolver
        self._current = None
        self._message = None
        self._voice = None

        self._event = Event()
        self._skip_votes = set()
        self._loop = AudioPlayerLoopMode.NONE
        self._history = deque(maxlen=5)

        self._task = create_task(self._run())
        self._task.add_done_callback(self._handle_exception)

    def __bool__(self) -> bool:
        return self.active

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

    @property
    def voice(self) -> VoiceClient:
        return self._voice

    @voice.setter
    def voice(self, voice: VoiceClient) -> None:
        self._voice = voice

    def put(self, song: Song) -> None:
        self._queue.put_nowait(song)

    def cleanup(self) -> None:
        self._queue.clear()
        self._voice.stop()
        create_task(self._voice.disconnect())
        if self.active:
            self._task.cancel()

    async def _run(self) -> None:
        while True:
            self._event.clear()
            self._current = None
            self.message = None

            try:
                song = await wait_for(self._queue.get(), timeout=300)
            except TimeoutError:
                self.cleanup()
                return

            if isinstance(song.source, str):
                try:
                    source = await self._resolver.by_url(song.source, song.requester)
                except Exception as e:
                    log.error(f"Failed to fetch source: {e}")
                    continue
                song = Song(source)

            self._current = song
            self._voice.play(song.source, after=self._prepare_next)
            self.message = await self.send(embed=song.get_embed(self._loop, self._queue[:5]))
            await self._event.wait()

    def _handle_exception(self, task: Task) -> None:
        if task.exception():
            log.error(
                "Audio player for %s raised an exception: %s",
                self.ctx.guild_id ,
                task.exception()
            )

    def _prepare_next(self, error=None) -> None:
        if error:
            log.error(f"Voice failed: {error}")
        self._skip_votes.clear()
        self._event.set()

    async def send(self, *args: Any, **kwargs: Any) -> Message | None:
        try:
            return await self.ctx.send(*args, **kwargs)
        except (Forbidden, HTTPException):
            pass
