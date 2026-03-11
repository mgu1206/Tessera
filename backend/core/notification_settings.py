"""In-memory app settings store (notifications + polling)."""

import logging

logger = logging.getLogger(__name__)

_settings: dict = {
    # Notifications
    "telegram_enabled": False,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "imessage_enabled": False,
    "imessage_recipients": [],
    # Polling
    "poll_interval_seconds": 5,
    "report_interval_seconds": 300,
    "max_attempts": 0,
}


def get_all() -> dict:
    return dict(_settings)


def update(data: dict) -> dict:
    for key in _settings:
        if key in data:
            _settings[key] = data[key]
    _settings["imessage_recipients"] = _settings["imessage_recipients"][:5]
    return dict(_settings)


def get_telegram() -> tuple[bool, str, str]:
    return _settings["telegram_enabled"], _settings["telegram_bot_token"], _settings["telegram_chat_id"]


def get_imessage() -> tuple[bool, list[str]]:
    return _settings["imessage_enabled"], _settings["imessage_recipients"]


def get_polling() -> dict:
    return {
        "poll_interval_seconds": _settings["poll_interval_seconds"],
        "report_interval_seconds": _settings["report_interval_seconds"],
        "max_attempts": _settings["max_attempts"],
    }
