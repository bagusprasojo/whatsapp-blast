"""
Simple authentication client for remote login verification.
"""

from __future__ import annotations

import requests
from typing import Any, Dict


class AuthError(Exception):
    """Raised when authentication fails."""


class AuthClient:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Call remote endpoint and return profile on success."""
        try:
            response = requests.get(
                self.endpoint,
                params={"email": email, "password": password},
                timeout=10,
            )
        except requests.RequestException as exc:  # pragma: no cover - network
            raise AuthError(f"Gagal menghubungi server login: {exc}") from exc
        
        print(response)
        data = response.json()
        print(data)
        
        try:
            data = response.json()
            print(data)
        except ValueError as exc:
            raise AuthError("Response login tidak valid") from exc
        if data.get("status") != "success":
            message = data.get("msg", "Email atau password salah")
            raise AuthError(message)
        profile = data.get("profile")
        if not isinstance(profile, dict):
            raise AuthError("Profil login tidak ditemukan pada response")
        return profile
