from typing import Self
from urllib.parse import urlparse

from discord import Member, Embed, EmbedAuthor

from lib.enums import SongEmbedSize, AudioPlayerLoopMode
from lib.music.source import Source
from lib.utils import format_time, truncate


class Song:
    def __init__(self, source: Source | str, requester: Member = None) -> None:
        if isinstance(source, str):
            if not requester:
                raise ValueError("Requester must be provided when creating a Song from url")

        self._source = source
        self._requester = requester

    @property
    def source(self) -> Source | str:
        """
        It is recommended to use the properties of this class instead of this property
        :return: The source of the song.
        """
        return self._source

    @source.setter
    def source(self, source: Source | str) -> None:
        """
        Can be used to change the source of the song.

        :param source: The new source of the song.
        :return: None
        """
        self._source = source

    @property
    def requester(self) -> Member:
        """
        :return: The user who requested the song.
        """
        if isinstance(self.source, str):
            return self._requester
        return self._source.requester

    @property
    def title(self) -> str | None:
        """
        :return: The title of the song.
        """
        if isinstance(self.source, str):
            return None
        return self._source.title

    @property
    def artist(self) -> str | None:
        """
        :return: The artist of the song.
        """
        if isinstance(self.source, str):
            return None
        return self._source.artist

    @property
    def url(self) -> str:
        """
        :return: The url of the song.
        """
        if isinstance(self.source, str):
            return self._source
        return self._source.url

    @property
    def duration(self) -> int | None:
        """
        :return: The duration of the song in seconds.
        """
        if isinstance(self.source, str):
            return None
        return 0

    def get_embed(
            self,
            loop: AudioPlayerLoopMode,
            queue: list[Self],
            size: SongEmbedSize = SongEmbedSize.DEFAULT,
            progress: float = 0
    ) -> Embed:
        """
        Get an embed for the song

        :param loop: AudioPlayerLoop
            The loop mode of the player
        :param queue: list[Song]
            The queue of the player.
            It Should contain all songs that are intended to be shown in the embed
        :param size: SongEmbedSize
            The size of the embed
        :param progress: int
            Whether to include the elapsed time in the embed.
            If 0, the elapsed time will not be included
        :return: `discord.Embed`
        """

        if isinstance(self.source, str):
            return Embed(
                author=EmbedAuthor(
                    name="The current song is currently being processed.",
                )
            )

        embed: Embed = Embed(
            title=self.title,
            color=0x1ed760
        )
        if progress:
            elapsed_time: int = int(self.duration * progress)
            duration = f"{format_time(elapsed_time)} **/** {format_time(self.duration)}"
        else:
            duration = format_time(self.duration)

        description: str = (
            f"[URL]({self.source.url}) **|** [{self.source.artist}]({self.url}) **|** "
            f"{duration} **|** {self.requester.mention}"
        )
        embed.description = description

        if size == SongEmbedSize.SMALL:
            return embed
        embed.set_thumbnail(url=self.source.thumbnail_url)

        embed.add_field(
            name="Loop",
            value={
                AudioPlayerLoopMode.NONE: "Disabled",
                AudioPlayerLoopMode.QUEUE: "Queue",
                AudioPlayerLoopMode.SONG: "Song"}[loop]
        )

        if not len(queue) or size == SongEmbedSize.NO_QUEUE:
            return embed

        _queue: list[str] = []
        for i, song in enumerate(queue[:5], start=1):
            # Remove query params, embeds are limited in length
            _url = urlparse(song.url)
            url: str = f"{_url.scheme}://{_url.netloc}{_url.path}"

            _queue.append(f"`{i}`. [{truncate(f'{song.title}', 55)}]({url})")

        if len(queue) > 5:
            _queue.append(f"Execute **/**`queue` to **see {len(queue) - 5} more**.")

        embed.add_field(
            name="Queue",
            value="\n".join(_queue),
            inline=False
        )
        return embed

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Song):
            return NotImplemented
        return self.url == other.url
