"""
Selenium-backed WhatsApp Web automation utilities.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterable, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import config
from .database import Database
from .models import CampaignSettings, Contact, Template
from .utils import build_template_context, render_template

StatusCallback = Callable[[str], None]


class WhatsAppSender:
    def __init__(self, browser: str = config.DEFAULT_BROWSER, profile_path: Optional[Path] = None) -> None:
        self.browser = browser
        self.profile_path = profile_path
        self.driver: Optional[webdriver.Chrome] = None

    def _ensure_driver(self) -> webdriver.Chrome:
        if self.driver:
            return self.driver
        options = ChromeOptions()
        options.add_argument("--disable-notifications")
        if self.profile_path:
            options.add_argument(f"--user-data-dir={self.profile_path}")
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        self.driver = driver
        return driver

    def open_session(self) -> None:
        driver = self._ensure_driver()
        driver.get("https://web.whatsapp.com")

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _select_chat(self, number: str) -> None:
        driver = self._ensure_driver()
        wait = WebDriverWait(driver, 15)
        search_box = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )
        search_box.clear()
        search_box.send_keys(number)
        search_box.send_keys(Keys.ENTER)
        time.sleep(1.5)

    def _send_text(self, message: str) -> None:
        driver = self._ensure_driver()
        wait = WebDriverWait(driver, 10)
        box = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
        )
        for line in message.splitlines():
            box.send_keys(line)
            box.send_keys(Keys.SHIFT, Keys.ENTER)
        # remove trailing newline inserted by SHIFT/ENTER
        box.send_keys(Keys.BACKSPACE)
        box.send_keys(Keys.ENTER)

    def send_message(self, number: str, message: str) -> None:
        driver = self._ensure_driver()
        if driver.current_url != "https://web.whatsapp.com/":
            self.open_session()
        try:
            self._select_chat(number)
        except TimeoutException as exc:
            raise RuntimeError(f"Tidak bisa menemukan kontak {number}") from exc
        self._send_text(message)


class MessageController:
    def __init__(self, db: Database, sender: WhatsAppSender) -> None:
        self.db = db
        self.sender = sender
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run_campaign(
        self,
        contacts: Iterable[Contact],
        template: Template,
        settings: CampaignSettings,
        callback: Optional[StatusCallback] = None,
    ) -> None:
        self._stop_requested = False
        for idx, contact in enumerate(contacts, start=1):
            if self._stop_requested:
                self._emit(callback, "Kampanye dihentikan oleh pengguna")
                break
            try:
                personalized = render_template(
                    template.body,
                    build_template_context(contact=contact),
                )
                self.sender.send_message(contact.number, personalized)
                status = f"Berhasil ({idx}) -> {contact.name}"
                self.db.add_log(contact.number, "sent", status)
                self._emit(callback, status)
            except Exception as exc:  # noqa: BLE001
                status = f"Gagal -> {contact.name}: {exc}"
                self.db.add_log(contact.number, "failed", str(exc))
                self._emit(callback, status)
            time.sleep(max(1, settings.delay_seconds))

    @staticmethod
    def _emit(callback: Optional[StatusCallback], message: str) -> None:
        if callback:
            callback(message)
