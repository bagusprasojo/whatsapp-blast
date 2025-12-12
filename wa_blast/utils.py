"""
Utility helpers for the WhatsApp Blast application.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict


PLACEHOLDERS = {
    "{{nama}}": lambda data: data.get("name", ""),
    "{{nomor}}": lambda data: data.get("number", ""),
    "{{tanggal}}": lambda data: datetime.now().strftime("%d-%m-%Y"),
}


def render_template(body: str, data: Dict[str, str]) -> str:
    """Replace supported placeholders with their values."""
    rendered = body
    for placeholder, resolver in PLACEHOLDERS.items():
        rendered = rendered.replace(placeholder, str(resolver(data)))
    return rendered
