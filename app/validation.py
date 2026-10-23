"""Pure validation helpers for user-supplied values."""

import re
from urllib.parse import urlsplit

MAX_URL_LENGTH = 2048
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")

RESERVED_ALIASES = frozenset({"links","docs","redoc","openapi.json","health","favicon.ico"})

def validate_url(value:str)->str:
    """Return the URL unchanged if it is an absolute http(s) URL, else raise ValueError."""
    url = value.strip()

    if not url:
        raise ValueError("URL must not be empty.")
    if len(url)>MAX_URL_LENGTH:
        raise ValueError(f"URL must be at most {MAX_URL_LENGTH} characters long.")
    if any(ch.isspace() for ch in url):
        raise ValueError("URL must not contain whitespace.")

    try:
        parts = urlsplit(url)
        hostname = parts.hostname
        parts.port
    except ValueError:
        raise ValueError("URL is malformed.") from None
    if parts.scheme.lower() not in ("http","https"):
        raise ValueError("URL must start with http:// or https://.")
    if not hostname:
        raise ValueError("URL must include a host name, e.g. https://example.com/page.")
    return url


def validate_alias(value:str)->str:
    if not ALIAS_PATTERN.fullmatch(value):
        raise ValueError(
            "Alias must be 3-32 characters long and contain only letters, digits, '-' and '_'."
        )
    return value


def is_reserved_alias(alias:str)->bool:
    return alias.lower() in RESERVED_ALIASES



















