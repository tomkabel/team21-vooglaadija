"""Username helpers for registration and display defaults."""


def default_username_from_email(
    email: str,
    *,
    max_length: int = 64,
    min_length: int = 3,
) -> str:
    """Derive a default username from an email local part.

    Ensures the result is at most ``max_length`` and at least ``min_length``
    characters so it satisfies the same rules as ``/web/settings/username``.
    """
    base = email.split("@", maxsplit=1)[0].strip()
    if not base:
        candidate = "user"
    else:
        candidate = base[:max_length]

    if len(candidate) < min_length:
        candidate = (candidate + "user")[:max_length]

    if len(candidate) < min_length:
        candidate = (candidate + "x" * (min_length - len(candidate)))[:max_length]

    return candidate
