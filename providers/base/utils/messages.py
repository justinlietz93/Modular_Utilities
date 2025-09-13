"""Message extraction helpers shared across providers."""
from __future__ import annotations

from typing import Optional, List, Tuple
from ...base.models import Message

def extract_system_and_user(messages: List[Message]) -> Tuple[Optional[str], str]:
    """Return (first_system_message, concatenated_user_text).

    Ignores assistant/tool messages for now (could be extended later).
    """
    system_message: Optional[str] = None
    user_segments: List[str] = []
    for m in messages:
        if not isinstance(m, Message):
            continue
        if m.role == "system" and system_message is None:
            system_message = m.text_or_joined()
        elif m.role == "user":
            user_segments.append(m.text_or_joined())
    return system_message, "\n".join(s for s in user_segments if s)

__all__ = ["extract_system_and_user"]
