from difflib import SequenceMatcher
from random import randrange
from time import strftime, gmtime
from typing import Any

from millify import millify


def ordinal(n: int) -> str:
    """Returns the ordinal suffix for a number."""
    return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def format_time(seconds: int) -> str:
    """Formats a time in seconds to a human-readable format."""
    if seconds < 3600:
        return strftime("%M:%S", gmtime(seconds))
    elif 86400 > seconds >= 3600:
        return strftime("%H:%M:%S", gmtime(seconds))
    return strftime("%H:%M:%S", gmtime(seconds))


def shortened(n: int) -> str:
    """Shortens a number to a human-readable format."""
    return millify(n, precision=1, drop_nulls=True)


def truncate(s: str, limit: int, ending: str = "...") -> str:
    """Shortens a string to a certain limit and adds an ending."""
    return s[:limit - len(ending)] + ending if len(s) > limit else s


def random_hex(length: int) -> str:
    """Generates a random hex string."""
    return f'{randrange(16**length):x}'.zfill(length)


def similarity(a: str, b: str) -> float:
    """Calculates the similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def find_key(data: dict | list, key: str) -> Any | None:
    """Recursively search for a key in a nested dictionary.

    :param data: The dictionary to search.
    :param key: The key to find.
    :returns: The value associated with the key, or ``None`` if not found.
    """
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            if result := find_key(value, key):
                return result
    elif isinstance(data, list):
        for item in data:
            if result := find_key(item, key):
                return result
    return None