"""
Dataclass models for the WhatsApp Blast application.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Contact:
    id: Optional[int]
    name: str
    number: str


@dataclass
class Template:
    id: Optional[int]
    title: str
    body: str


@dataclass
class ScheduleEntry:
    id: Optional[int]
    start_time: datetime
    template_id: int
    status: str


@dataclass
class LogEntry:
    id: Optional[int]
    number: str
    status: str
    timestamp: datetime
    message: str


@dataclass
class CampaignSettings:
    delay_seconds: int
    template_id: int
