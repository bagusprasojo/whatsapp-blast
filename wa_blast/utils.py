"""
Utility helpers for the WhatsApp Blast application.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Mapping, Optional, TYPE_CHECKING

from jinja2 import Environment, StrictUndefined, TemplateError

if TYPE_CHECKING:  # pragma: no cover
    from .models import Contact


def _format_date(value: Any, fmt: str = "%d-%m-%Y") -> str:
    """Jinja filter: format datetime/date values."""
    if isinstance(value, datetime):
        return value.strftime(fmt)
    if isinstance(value, date):
        return value.strftime(fmt)
    raise ValueError("format_date filter expects date/datetime input")


TEMPLATE_ENV = Environment(
    autoescape=False,
    lstrip_blocks=True,
    trim_blocks=True,
    undefined=StrictUndefined,
)
TEMPLATE_ENV.filters["format_date"] = _format_date


def build_template_context(
    *,
    contact: Optional["Contact"] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Provide default context for template rendering."""
    now = datetime.now()
    context: Dict[str, Any] = {
        "now": now,
        "today": now.date(),
    }
    if contact:
        context["contact"] = {
            "id": contact.id,
            "name": contact.name,
            "nama": contact.name,
            "number": contact.number,
            "nomor": contact.number,
        }
    if extra:
        context.update(extra)
    return context


def render_template(body: str, context: Mapping[str, Any]) -> str:
    """Render template text using Jinja2."""
    try:
        template = TEMPLATE_ENV.from_string(body)
        return template.render(**context)
    except TemplateError as exc:  # pragma: no cover - UI handles feedback
        raise ValueError(f"Template error: {exc}") from exc
