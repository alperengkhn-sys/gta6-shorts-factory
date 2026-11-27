#!/usr/bin/env python3
"""Verify the signed source and download path before rendering a public Twitch clip."""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import hmac
import math
import os
import sys
from urllib.parse import urlsplit


def permission_message(job_id: str, source_url: str, broadcaster_id: str,
                      max_source_seconds: str, permission_expires_at: str = "",
                      render_attempt: str = "", download_url: str = "") -> bytes:
    return "\n".join((
        str(job_id),
        str(source_url),
        str(broadcaster_id),
        str(max_source_seconds),
        str(permission_expires_at),
        str(render_attempt),
        str(download_url),
    )).encode("utf-8")


def make_permission_signature(secret: str, job_id: str, source_url: str,
                              broadcaster_id: str, max_source_seconds: str,
                              permission_expires_at: str = "",
                              render_attempt: str = "", download_url: str = "") -> str:
    digest = hmac.new(
        str(secret).encode("utf-8"),
        permission_message(job_id, source_url, broadcaster_id,
                           max_source_seconds, permission_expires_at, render_attempt, download_url),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_permission_attestation(*, secret: str, job_id: str, source_url: str,
                                  broadcaster_id: str, max_source_seconds: str,
                                  permission_expires_at: str, render_attempt: str,
                                  download_url: str, signature: str,
                                  now: dt.datetime | None = None) -> dict:
    """Raise ValueError unless the signed source, broadcaster and time cap are valid."""
    fields = (job_id, source_url, broadcaster_id, max_source_seconds, render_attempt, signature)
    if not secret or not all(str(value).strip() for value in fields):
        raise ValueError("Signed source attestation is missing; rendering is blocked.")
    parsed_source = urlsplit(str(source_url))
    source_host = (parsed_source.hostname or "").lower().rstrip(".")
    source_parts = [part for part in parsed_source.path.split("/") if part]
    is_clip_page = (
        parsed_source.scheme == "https"
        and source_host in {"twitch.tv", "www.twitch.tv", "clips.twitch.tv"}
        and not parsed_source.username and not parsed_source.password and not parsed_source.fragment
        and (
            (source_host == "clips.twitch.tv" and len(source_parts) >= 1)
            or (source_host in {"twitch.tv", "www.twitch.tv"}
                and "clip" in [part.lower() for part in source_parts]
                and len(source_parts) >= 3)
        )
    )
    if not is_clip_page:
        raise ValueError("A real public HTTPS Twitch clip page is required.")
    parsed_download = urlsplit(str(download_url or "").strip())
    if download_url and (
        parsed_download.scheme != "https" or not parsed_download.hostname
        or parsed_download.username or parsed_download.password or parsed_download.fragment
        or parsed_download.hostname.lower().rstrip(".") in {"twitch.tv", "www.twitch.tv", "clips.twitch.tv"}
    ):
        raise ValueError("The official temporary MP4 URL is invalid; a Twitch clip page is not an MP4 URL.")
    try:
        maximum = float(max_source_seconds)
    except (TypeError, ValueError):
        raise ValueError("Permission time limit is invalid.") from None
    if not math.isfinite(maximum) or not 25.0 <= maximum <= 175.0:
        raise ValueError("Permission time limit is outside the allowed 25–175 second range.")
    if permission_expires_at:
        try:
            expiry = dt.datetime.fromisoformat(str(permission_expires_at).replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Creator permission expiry is invalid.") from None
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=dt.timezone.utc)
        current = now or dt.datetime.now(dt.timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=dt.timezone.utc)
        if expiry <= current:
            raise ValueError("Creator permission has expired; publishing is blocked.")
    expected = make_permission_signature(
        secret, job_id, source_url, broadcaster_id, max_source_seconds, permission_expires_at,
        render_attempt,
        download_url,
    )
    if not hmac.compare_digest(expected, str(signature)):
        raise ValueError("Permission attestation is invalid; publishing is blocked.")
    return {
        "job_id": str(job_id),
        "broadcaster_id": str(broadcaster_id),
        "render_attempt": str(render_attempt),
        "max_source_seconds": maximum,
        "permission_expires_at": str(permission_expires_at or ""),
        "download_host": parsed_download.hostname if download_url else "public-twitch-page",
        "verified": True,
    }


def main() -> int:
    try:
        result = verify_permission_attestation(
            secret=os.environ.get("PERMISSION_SECRET", ""),
            job_id=os.environ.get("JOB_ID", ""),
            source_url=os.environ.get("SOURCE_URL", ""),
            broadcaster_id=os.environ.get("BROADCASTER_ID", ""),
            max_source_seconds=os.environ.get("MAX_SOURCE_SECONDS", ""),
            permission_expires_at=os.environ.get("PERMISSION_EXPIRES_AT", ""),
            render_attempt=os.environ.get("RENDER_ATTEMPT", ""),
            download_url=os.environ.get("DOWNLOAD_URL", ""),
            signature=os.environ.get("PERMISSION_ATTESTATION", ""),
        )
    except ValueError as exc:
        print("PERMISSION_CHECK_FAILED: " + str(exc), file=sys.stderr)
        return 1
    print(
        "PASS: signed public Twitch source attestation verified for broadcaster "
        + result["broadcaster_id"]
        + "; source limit "
        + str(result["max_source_seconds"])
        + " seconds."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
