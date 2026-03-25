from discord import PCMVolumeTransformer, FFmpegPCMAudio

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
            stream_url: str,
            volume: float = 0.5
    ) -> None:
        super().__init__(FFmpegPCMAudio(stream_url, **self.FFMPEG_OPTIONS), volume)

    def reset(self) -> None:
        self.original.cleanup()
        self.original = FFmpegPCMAudio(self.original, **self.FFMPEG_OPTIONS)
