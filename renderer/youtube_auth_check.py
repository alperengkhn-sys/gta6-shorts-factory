#!/usr/bin/env python3
"""Verify YouTube OAuth refresh credentials without uploading or changing videos."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main():
    names = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    values = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError("Missing GitHub Actions secret(s): " + ", ".join(missing))

    body = urllib.parse.urlencode({
        "client_id": values["YOUTUBE_CLIENT_ID"],
        "client_secret": values["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": values["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        # Never print the request body or any credential/token value.
        raise RuntimeError(f"Google rejected the refresh-token request (HTTP {exc.code}).") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("Could not reach Google's OAuth token endpoint.") from None

    if not payload.get("access_token"):
        raise RuntimeError("Google returned no access token.")
    scopes = set(str(payload.get("scope", "")).split())
    upload_scope = "https://www.googleapis.com/auth/youtube.upload"
    read_scopes = {
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube",
    }
    thumbnail_scopes = {
        upload_scope,
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtubepartner",
    }
    write_scopes = {
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube",
    }
    analytics_scopes = {
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    }
    if scopes and upload_scope not in scopes:
        raise RuntimeError("The refreshed token does not include the YouTube upload scope.")
    print("PASS: Google accepted the refresh token; YouTube upload scope is present.")
    print("SHORTS_THUMBNAIL_UPLOAD: " +
          ("available" if not scopes or bool(scopes & thumbnail_scopes) else "missing_thumbnail_upload_scope"))
    print("SHORTS_PROCESSING_STATUS: " +
          ("available" if not scopes or bool(scopes & read_scopes) else "fallback_120s_retry_until_accepted"))
    print("EXISTING_VIDEO_METADATA_UPDATE: " +
          ("available" if not scopes or bool(scopes & write_scopes) else "not_requested_for_new_uploads"))
    missing_analytics_scopes = analytics_scopes - scopes
    print("CHANNEL_ANALYTICS: " +
          ("available" if not missing_analytics_scopes else
           "reauthorization_required:" + ",".join(sorted(missing_analytics_scopes))) )
    print("No video was uploaded or modified. Token values are never printed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("YOUTUBE_OAUTH_CHECK_FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
