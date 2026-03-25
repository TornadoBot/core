from dataclasses import dataclass
from datetime import datetime
from json import dumps, loads
from typing import Self


@dataclass
class SpotifyArtist:
    name: str
    uri: str

    @property
    def id(self) -> str:
        return self.uri.split(":")[-1]


@dataclass
class SpotifyTrack:
    id: str
    title: str
    uri: str
    artists: list[SpotifyArtist]
    duration_ms: int
    release_date: datetime
    is_explicit: bool
    preview_url: str | None = None
    cover_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        artists = [
            SpotifyArtist(name=a["name"], uri=a["uri"])
            for a in data.get("artists", [])
        ]

        images = data.get("visualIdentity", {}).get("image", [])
        cover = max(images, key=lambda i: i["maxWidth"], default=None)

        return cls(
            id=data["id"],
            title=data["title"],
            uri=data["uri"],
            artists=artists,
            duration_ms=data["duration"],
            release_date=datetime.fromisoformat(
                data["releaseDate"]["isoString"].replace("Z", "+00:00")
            ),
            is_explicit=data.get("isExplicit", False),
            preview_url=data.get("audioPreview", {}).get("url"),
            cover_url=cover["url"] if cover else None,
        )

    def to_json(self) -> str:
        return dumps({
            "id": self.id,
            "title": self.title,
            "uri": self.uri,
            "artists": [{"name": a.name, "uri": a.uri} for a in self.artists],
            "duration_ms": self.duration_ms,
            "release_date": self.release_date.isoformat(),
            "is_explicit": self.is_explicit,
            "preview_url": self.preview_url,
            "cover_url": self.cover_url,
        })

    @classmethod
    def from_json(cls, raw: str) -> Self:
        data = loads(raw)
        return cls(
            **{**data,
               "artists": [SpotifyArtist(**a) for a in data["artists"]],
               "release_date": datetime.fromisoformat(data["release_date"])}
        )

    @property
    def artist_names(self) -> str:
        return ", ".join(a.name for a in self.artists)
