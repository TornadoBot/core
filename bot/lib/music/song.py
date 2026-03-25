from typing import Self
from urllib.parse import urlparse

from discord import Member, Embed, EmbedAuthor

from lib.enums import SongEmbedSize, AudioPlayerLoopMode
from lib.music.dto.spotify_dto import SpotifyTrack
from lib.music.source import Source
from lib.utils import format_time, truncate


class Song:
    def __init__(
            self,
            url: str,
            requester: Member = None,
            metadata: SpotifyTrack = None,
            source: Source | None = None
    ) -> None:
        self._url = url
        self._metadata = metadata
        self._requester = requester
        self._source = source

    @property
    def source(self) -> Source | None:
        return self._source

    @source.setter
    def source(self, source: Source) -> None:
        self._source = source

    @property
    def requester(self) -> Member:
        return self._requester

    @property
    def title(self) -> str:
        if self._metadata:
            return self._metadata.title
        return "Spotify Track"

    @property
    def artist(self) -> str | None:
        if self._metadata:
            return self._metadata.artist_names
        return None

    @property
    def url(self) -> str:
        return self._url

    @property
    def duration(self) -> int:
        if self._metadata:
            return self._metadata.duration_ms // 1000
        return 195  # average song length in 2020

    @property
    def thumbnail_url(self) -> str | None:
        if self._metadata:
            return self._metadata.cover_url
        return None

    def resolve(self, metadata: SpotifyTrack, source: Source) -> None:
        self._metadata = metadata
        self._source = source

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

        if self._metadata is None:
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

        embed.description = (
            f"[URL]({self.url}) **|** {self.artist} **|** "
            f"{duration} **|** {self.requester.mention}"
        )
        embed.set_thumbnail(url=self.thumbnail_url)
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
