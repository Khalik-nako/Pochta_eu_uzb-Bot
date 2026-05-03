from typing import Any
from . import uz, ru


def get_messages(lang: str) -> Any:
    if lang == "ru":
        return ru.messages
    return uz.messages


def t(lang: str, key: str, **kwargs) -> str:
    msgs = get_messages(lang)
    text = getattr(msgs, key, f"[{key}]")
    if callable(text):
        return text(**kwargs)
    if kwargs and isinstance(text, str):
        return text.format(**kwargs)
    return text
