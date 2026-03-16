from base64 import b64decode
from json import loads

from aiohttp import ClientSession
from discord import PCMVolumeTransformer, Member, FFmpegPCMAudio

from lib.music.linker import Linker

STREAM_SERVICES: list[str] = [
    "https://hifi-one.spotisaver.net",
    "https://hifi-two.spotisaver.net",
    "https://eu-central.monochrome.tf",
    "https://us-west.monochrome.tf",
    "https://api.monochrome.tf",
    "https://monochrome-api.samidy.com",
    "https://tidal.kinoplus.online",
]

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5 "
        "-http_proxy socks5h://tor:9050"
    ),
    'options': '-vn'
}


class TidalSource(PCMVolumeTransformer):
    def __init__(
            self,
            url: str,
            requester: Member,
            stream_url: str,
            *,
            metadata: dict,
            volume: float = 0.5
    ) -> None:
        super().__init__(FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS), volume)

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
        return self._metadata["artistName"]

    @property
    def thumbnail_url(self) -> str:
        return self._metadata["thumbnailUrl"]

    @property
    def url(self) -> str:
        return self._url

    def reset(self) -> None:
        self.original.cleanup()
        self.original = FFmpegPCMAudio(self.original, **FFMPEG_OPTIONS)

    @classmethod
    async def from_url(cls, url: str, requester: Member) -> "TidalSource":
        tidal_entry: dict = await Linker().fetch_tidal(url)

        for service in STREAM_SERVICES:
            async with ClientSession().get(
                    f"{service}/track?id={tidal_entry['id']}&quality=LOW"
            ) as response:
                if response.status != 200:
                    continue

                tidal_stream: dict = await response.json()
                try:
                    manifest: str = tidal_stream["data"]["manifest"]
                    tidal_manifest = loads(b64decode(manifest).decode("utf-8"))
                    stream_url = tidal_manifest["urls"][0]
                    break
                except (KeyError, IndexError):
                    continue
        else:
            raise Exception("Failed to extract URL")
        return cls(url, requester, stream_url, metadata=tidal_entry)
