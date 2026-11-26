#!/usr/bin/env python3
"""Verify a Cloudflare Worker HMAC attestation before rendering creator footage."""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import hmac
import math
import os
import sys


def permission_message(job_id: str, source_url: str, broadcaster_id: str,
                      max_source_seconds: str, permission_expires_at: str = "",
                      render_attempt: str = "") -> bytes:
    return "\n".join((
        str(job_id),
        str(source_url),
        str(broadcaster_id),
        str(max_source_seconds),
        str(permission_expires_at),
        str(render_attempt),
    )).encode("utf-8")


def make_permission_signature(secret: str, job_id: str, source_url: str,
                              broadcaster_id: str, max_source_seconds: str,
                              permission_expires_at: str = "",
                              render_attempt: str = "") -> str:
    digest = hmac.new(
        str(secret).encode("utf-8"),
        permission_message(job_id, source_url, broadcaster_id,
                           max_source_seconds, permission_expires_at, render_attempt),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_permission_attestation(*, secret: str, job_id: str, source_url: str,
                                  broadcaster_id: str, max_source_seconds: str,
                                  permission_expires_at: str, render_attempt: str,
                                  signature: str, now: dt.datetime | None = None) -> dict:
    """Raise ValueError unless the signed source, broadcaster and time cap are valid."""
    fields = (job_id, source_url, broadcaster_id, max_source_seconds, render_attempt, signature)
    if not secret or not all(str(value).strip() for value in fields):
        raise ValueError("Permission attestation is missing; publishing is blocked.")
    try:
        maximum = float(max_source_seconds)
    except (TypeError, ValueError):
        raise ValueError("Permission time limit is invalid.") from None
    if not math.isfinite(maximum) or not 45.0 <= maximum <= 175.0:
        raise ValueError("Permission time limit is outside the allowed 45–175 second range.")
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
    )
    if not hmac.compare_digest(expected, str(signature)):
        raise ValueError("Permission attestation is invalid; publishing is blocked.")
    return {
        "job_id": str(job_id),
        "broadcaster_id": str(broadcaster_id),
        "render_attempt": str(render_attempt),
        "max_source_seconds": maximum,
        "permission_expires_at": str(permission_expires_at or ""),
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
            signature=os.environ.get("PERMISSION_ATTESTATION", ""),
        )
    except ValueError as exc:
        print("PERMISSION_CHECK_FAILED: " + str(exc), file=sys.stderr)
        return 1
    print(
        "PASS: signed creator permission verified for broadcaster "
        + result["broadcaster_id"]
        + "; source limit "
        + str(result["max_source_seconds"])
        + " seconds."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
