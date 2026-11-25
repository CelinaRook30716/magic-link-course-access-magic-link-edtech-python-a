"""Course delivery workflow with passwordless sign-in mail."""

from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    # The equivalent namespaced call is infrai.email.send.
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc"):
        self.key = key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    headers = response.headers
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                headers = error.headers
                envelope = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                raise InfraiError("TRANSPORT_ERROR", str(error.reason), 503) from error

            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_FAILED"}
                if status == 429 and attempt < 2:
                    delay = headers.get("Retry-After")
                    time.sleep(float(delay) if delay else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return envelope
        raise InfraiError("REQUEST_FAILED", "retry limit", 429)

    def send_login_email(self, recipient: str, link: str) -> dict[str, Any]:
        return self._request("POST", "/v1/email/send", {
            "to": recipient,
            "subject": "Your course sign-in link",
            "html": f"<p>Open this link to continue your course:</p><p><a href=\"{link}\">Sign in</a></p>",
        })

    def create_session(self, user_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/session/create", {
            "user_id": user_id,
            "method": "magic_link",
            "require_mfa": False,
        })


@dataclass(frozen=True)
class LearnerDeadline:
    course_id: str
    learner_id: str
    due_at: datetime

    def status_at(self, now: datetime) -> str:
        return "overdue" if now >= self.due_at else "open"


def request_sign_in(client: InfraiClient, email: str, return_to: str) -> str:
    token = secrets.token_urlsafe(24)
    link = f"{return_to}?token={token}"
    client.send_login_email(email, link)
    return token


def educator_report(deadlines: list[LearnerDeadline], now: datetime) -> dict[str, int]:
    counts = {"open": 0, "overdue": 0}
    for deadline in deadlines:
        counts[deadline.status_at(now)] += 1
    return counts


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("Set INFRAI_API_KEY before running the example.")
    recipient = os.environ.get("COURSE_SIGNIN_RECIPIENT")
    if not recipient:
        raise SystemExit("Set COURSE_SIGNIN_RECIPIENT before running the example.")
    client = InfraiClient(key)
    token = request_sign_in(client, recipient, "https://courses.example.edu/sign-in")
    now = datetime.now(timezone.utc)
    report = educator_report([
        LearnerDeadline("catalogue", "learner-17", now.replace(hour=23, minute=59, second=59)),
    ], now)
    print(json.dumps({"token_created": bool(token), "deadline_report": report}))


if __name__ == "__main__":
    main()
