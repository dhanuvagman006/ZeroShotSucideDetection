from __future__ import annotations

import mimetypes
import os
import smtplib
from contextlib import suppress
from email.message import EmailMessage
from pathlib import Path
from typing import Mapping, Optional, Sequence


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_threshold() -> float:
    return _float_env("ALERT_RISK_THRESHOLD", 0.5)


def _smtp_host() -> Optional[str]:
    return os.getenv("SMTP_HOST")


def _smtp_port() -> int:
    raw = os.getenv("SMTP_PORT", "587")
    try:
        return int(raw)
    except ValueError:
        return 587


def _smtp_username() -> Optional[str]:
    return os.getenv("SMTP_USERNAME")


def _smtp_password() -> Optional[str]:
    return os.getenv("SMTP_PASSWORD")


def _alert_recipient() -> Optional[str]:
    return os.getenv("ALERT_EMAIL_TO")


def _alert_sender() -> Optional[str]:
    return os.getenv("ALERT_EMAIL_FROM") or _smtp_username() or _alert_recipient()


def alerts_enabled() -> bool:
    return all([
        _alert_recipient(),
        _smtp_host(),
        _smtp_username(),
        _smtp_password(),
    ])


def risk_exceeds_threshold(score: float, indicators: Optional[Sequence[str]] = None) -> bool:
    try:
        score_val = float(score)
    except (TypeError, ValueError):
        score_val = 0.0
    return score_val >= _get_threshold() or bool(indicators)


def _attach_image(
    msg: EmailMessage,
    *,
    image_bytes: Optional[bytes],
    image_path: Optional[str],
    filename: Optional[str],
) -> None:
    data = image_bytes
    derived_name = filename
    if data is None and image_path:
        path = Path(image_path)
        if path.exists():
            data = path.read_bytes()
            derived_name = derived_name or path.name
    if not data:
        return
    if derived_name is None:
        derived_name = "frame.jpg"
    mime_type, _ = mimetypes.guess_type(derived_name)
    maintype, subtype = (mime_type or "image/jpeg").split("/", 1)
    msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=derived_name)


def _build_body(score: float, indicators: Sequence[str], source: str, extra: Optional[Mapping[str, str]]) -> str:
    lines = [
        "A new suicide-risk event was detected.",
        f"Source: {source}",
        f"Score: {score:.3f}",
    ]
    if indicators:
        lines.append("Indicators: " + ", ".join(indicators))
    if extra:
        for key, value in extra.items():
            if value:
                lines.append(f"{key}: {value}")
    return "\n".join(lines)


def notify_risk_detection(
    *,
    score: float,
    indicators: Optional[Sequence[str]],
    source: str,
    image_path: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    extra: Optional[Mapping[str, str]] = None,
) -> bool:
    """Send an email alert if thresholds are exceeded. Returns True when an email was attempted."""

    if not alerts_enabled():
        return False
    indicators = indicators or []
    if not risk_exceeds_threshold(score, indicators):
        return False

    recipient = _alert_recipient()
    sender = _alert_sender()
    if not recipient or not sender:
        return False

    msg = EmailMessage()
    msg["To"] = recipient
    msg["From"] = sender
    subject = os.getenv("ALERT_EMAIL_SUBJECT") or f"Suicide risk detected ({source})"
    msg["Subject"] = subject
    msg.set_content(_build_body(score, indicators, source, extra))

    _attach_image(msg, image_bytes=image_bytes, image_path=image_path, filename=filename)

    host = _smtp_host()
    username = _smtp_username()
    password = _smtp_password()
    if not (host and username and password):
        return False

    use_ssl = _bool_env("SMTP_USE_SSL", False)
    use_tls = _bool_env("SMTP_USE_TLS", True)

    server: Optional[smtplib.SMTP] = None
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, _smtp_port())
        else:
            server = smtplib.SMTP(host, _smtp_port())
        server.ehlo()
        if not use_ssl and use_tls:
            with suppress(Exception):
                server.starttls()
                server.ehlo()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[alerting] failed to send email: {exc}")
        if server is not None:
            with suppress(Exception):
                server.quit()
        return False
