"""Safe Cloudinary helpers for configuration diagnostics and error reporting."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)

# Redact long credential-looking tokens from Cloudinary error strings.
_SECRET_LIKE = re.compile(r'(?i)\b([a-f0-9]{16,}|[A-Za-z0-9_-]{20,})\b')


def parse_cloudinary_url(cloudinary_url: str) -> dict[str, str]:
    """Parse cloudinary://api_key:api_secret@cloud_name into credential parts."""
    raw = (cloudinary_url or '').strip()
    if not raw:
        return {}

    parsed = urlparse(raw)
    if parsed.scheme != 'cloudinary':
        raise ValueError(
            "CLOUDINARY_URL must use the cloudinary:// scheme "
            "(cloudinary://API_KEY:API_SECRET@CLOUD_NAME)."
        )

    cloud_name = (parsed.hostname or '').strip()
    api_key = unquote(parsed.username or '').strip()
    api_secret = unquote(parsed.password or '').strip()

    if not all((cloud_name, api_key, api_secret)):
        raise ValueError(
            "CLOUDINARY_URL is incomplete. Expected "
            "cloudinary://API_KEY:API_SECRET@CLOUD_NAME."
        )

    return {
        'CLOUD_NAME': cloud_name,
        'API_KEY': api_key,
        'API_SECRET': api_secret,
    }


def resolve_cloudinary_credentials(
    *,
    cloud_name: str = '',
    api_key: str = '',
    api_secret: str = '',
    cloudinary_url: str = '',
) -> tuple[dict[str, str], str]:
    """
    Resolve Cloudinary credentials from explicit vars or CLOUDINARY_URL.

    Returns (credentials_dict, source_label).
    Prefer the three explicit variables when all are present; otherwise parse URL.
    """
    cloud_name = (cloud_name or '').strip()
    api_key = (api_key or '').strip()
    api_secret = (api_secret or '').strip()
    cloudinary_url = (cloudinary_url or '').strip()

    if cloud_name and api_key and api_secret:
        return (
            {
                'CLOUD_NAME': cloud_name,
                'API_KEY': api_key,
                'API_SECRET': api_secret,
            },
            'explicit_env',
        )

    if cloudinary_url:
        return parse_cloudinary_url(cloudinary_url), 'cloudinary_url'

    partial = any((cloud_name, api_key, api_secret, cloudinary_url))
    if partial:
        raise ValueError(
            'Incomplete Cloudinary configuration. Set CLOUDINARY_URL or all of '
            'CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.'
        )

    return {}, 'none'


def sanitize_cloudinary_error(exc: BaseException) -> str:
    """Return a log/admin-safe error summary without credential material."""
    raw = f'{type(exc).__name__}: {exc}'.strip()
    sanitized = _SECRET_LIKE.sub('[redacted]', raw)
    sanitized = re.sub(
        r'(?i)(api[_-]?secret|password)\s*[:=]\s*\S+',
        r'\1=[redacted]',
        sanitized,
    )
    return sanitized[:500]


def log_upload_failure(scope: str, exc: BaseException, **extra: Any) -> str:
    """Log an upload failure with safe details; return the sanitized message."""
    safe = sanitize_cloudinary_error(exc)
    payload = {k: v for k, v in extra.items() if v is not None}
    logger.exception(
        'Cloudinary %s upload failed (%s)%s',
        scope,
        safe,
        f' context={payload}' if payload else '',
    )
    return safe
