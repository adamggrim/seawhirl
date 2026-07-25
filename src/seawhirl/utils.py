from typing import Any


def is_supported_terminal(stream: Any) -> bool:
    is_tty = hasattr(stream, 'isatty') and stream.isatty()
    is_utf8 = getattr(stream, 'encoding', '').lower() in ('utf-8', 'utf8')
    return is_tty and is_utf8
