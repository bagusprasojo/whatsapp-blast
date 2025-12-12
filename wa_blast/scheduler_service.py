"""
Background scheduler integration for delayed WhatsApp blasts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler

from .database import Database
from .models import CampaignSettings
from .sender import MessageController


class SchedulerService:
    def __init__(self, db: Database, controller: MessageController) -> None:
        self.db = db
        self.controller = controller
        self.scheduler = BackgroundScheduler()
        self.jobs: Dict[int, str] = {}
        self.scheduler.start()

    def schedule_campaign(self, start_time: datetime, template_id: int, delay_seconds: int) -> int:
        schedule_id = self.db.add_schedule(start_time, template_id)
        job = self.scheduler.add_job(
            self._execute_schedule,
            "date",
            run_date=start_time,
            args=[schedule_id, delay_seconds],
            id=f"schedule-{schedule_id}",
            replace_existing=True,
        )
        self.jobs[schedule_id] = job.id
        return schedule_id

    def cancel_schedule(self, schedule_id: int) -> None:
        job_id = self.jobs.pop(schedule_id, None)
        if job_id and self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        self.db.update_schedule_status(schedule_id, "canceled")

    def reload_jobs(self) -> None:
        for entry in self.db.list_schedules():
            if entry.status == "scheduled" and entry.start_time > datetime.now():
                self.schedule_campaign(entry.start_time, entry.template_id, delay_seconds=2)

    def _execute_schedule(self, schedule_id: int, delay_seconds: int) -> None:
        entry = next((s for s in self.db.list_schedules() if s.id == schedule_id), None)
        if not entry:
            return
        template = next((t for t in self.db.list_templates() if t.id == entry.template_id), None)
        if not template:
            self.db.update_schedule_status(schedule_id, "failed")
            return
        contacts = self.db.list_contacts()
        settings = CampaignSettings(delay_seconds=delay_seconds, template_id=template.id)
        try:
            self.db.update_schedule_status(schedule_id, "running")
            self.controller.run_campaign(contacts, template, settings)
            self.db.update_schedule_status(schedule_id, "completed")
        except Exception:  # noqa: BLE001
            self.db.update_schedule_status(schedule_id, "failed")
