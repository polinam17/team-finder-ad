import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

PHONE_RE = re.compile(r"^(?:\+7|8)\d{10}$")
GITHUB_HOSTS = {"github.com", "www.github.com"}


def normalize_phone(value):
    """Проверяет формат 8XXXXXXXXXX / +7XXXXXXXXXX и приводит номер к виду +7XXXXXXXXXX."""
    value = (value or "").strip()
    if not PHONE_RE.match(value):
        raise ValidationError("Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX.")
    if value.startswith("8"):
        value = "+7" + value[1:]
    return value


def validate_github_url(value):
    """Ссылка должна вести именно на GitHub."""
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in GITHUB_HOSTS:
        raise ValidationError("Ссылка должна вести на GitHub (https://github.com/...).")
