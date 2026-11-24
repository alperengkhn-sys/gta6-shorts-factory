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
    scopes = payload.get("scope", "")
    if scopes and "https://www.googleapis.com/auth/youtube.upload" not in scopes.split():
        raise RuntimeError("The refreshed token does not include the YouTube upload scope.")
    print("PASS: Google accepted the refresh token; YouTube upload scope is present.")
    print("No video was uploaded or modified.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("YOUTUBE_OAUTH_CHECK_FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
