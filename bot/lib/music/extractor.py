from base64 import b64decode
from json import loads

from aiohttp import ClientSession
from discord import PCMVolumeTransformer, Member, FFmpegPCMAudio

from lib.music.linker import Linker

SERVICES: list[str] = [
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
    def __init__(self, requester: Member, source: FFmpegPCMAudio, *, data: dict, volume: float = 0.5) -> None:
        super().__init__(source, volume)

        self._requester = requester
        self._data = data

    @classmethod
    async def from_url(cls, url: str, requester: Member) -> "TidalSource":
        tidal_id: str = await Linker().get_tidal_id(url)

        for service in SERVICES:
            async with ClientSession().get(
                    f"{service}/track?id={tidal_id}&quality=LOW"
            ) as response:
                if response.status != 200:
                    continue

                data: dict = await response.json()

                try:
                    manifest: str = data["data"]["manifest"]
                    stream_data = loads(b64decode(manifest).decode("utf-8"))
                    url = stream_data["urls"][0]
                    break
                except (KeyError, IndexError):
                    continue
        else:
            raise Exception("Failed to extract URL")
        return cls(requester, FFmpegPCMAudio(url, **FFMPEG_OPTIONS), data=data)
