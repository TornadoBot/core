from discord import PCMVolumeTransformer, Member, FFmpegPCMAudio

from lib.logger import get_logger

log = get_logger(__name__)


class Source(PCMVolumeTransformer):
    FFMPEG_OPTIONS = {
        "before_options": (
            "-reconnect 1 "
            "-reconnect_streamed 1 "
            "-reconnect_delay_max 5 "
            f"-http_proxy http://127.0.0.1:8080"
        ),
        'options': '-vn'
    }

    def __init__(
            self,
            url: str,
            requester: Member,
            stream_url: str,
            *,
            metadata: dict,
            volume: float = 0.5
    ) -> None:
        super().__init__(FFmpegPCMAudio(stream_url, **self.FFMPEG_OPTIONS), volume)

        self._requester = requester
        self._metadata = metadata
        self._url = url
        self._stream_url = stream_url

    @property
    def requester(self) -> Member:
        return self._requester

    @property
    def title(self) -> str:
        return self._metadata["title"]

    @property
    def artist(self) -> str:
        return self._metadata["artists"][0]["name"]

    @property
    def thumbnail_url(self) -> str:
        return self._metadata["image"][0]["url"]

    @property
    def url(self) -> str:
        return self._url

    def reset(self) -> None:
        self.original.cleanup()
        self.original = FFmpegPCMAudio(self.original, **self.FFMPEG_OPTIONS)
