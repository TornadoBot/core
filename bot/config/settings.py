from typing import Any

from discord import Intents

intents = Intents.default()
intents.members = True
intents.messages = True
intents.voice_states = True


SETTINGS: dict[str, Any] = {
    'Music': {
        'YouTubeEnabled': True
    },
    'OwnerIDs': [
        272446903940153345
    ],
    'Description': '',
    'Intents': intents,
    "Version": "0.5.7b",
}

