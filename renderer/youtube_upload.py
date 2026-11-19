#!/usr/bin/env python3
"""Upload a rendered Short to YouTube as PRIVATE using OAuth refresh-token credentials."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

def output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={str(value).replace(chr(10), ' ')}\n")

def request(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:2500]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e

def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not (client_id and client_secret and refresh_token):
        output("upload_status", "not_configured")
        output("video_url", "")
        print("YouTube upload skipped: OAuth secrets are not configured.")
        return 0

    video = Path("short.mp4")
    if not video.is_file() or video.stat().st_size == 0:
        raise RuntimeError("Rendered MP4 is missing or empty.")

    token_body = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    _, _, token_raw = request(
        "https://oauth2.googleapis.com/token",
        token_body,
        {"Content-Type": "application/x-www-form-urlencoded"},
        "POST",
    )
    access_token = json.loads(token_raw)["access_token"]

    title = os.environ.get("SHORT_TITLE", "GTA 6 Short").strip()[:100]
    description = os.environ.get(
        "SHORT_DESCRIPTION",
        "Grand Theft Auto VI gaming moment. #GTA6 #GTAVI #Shorts",
    ).strip()[:5000]
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["GTA 6", "GTA VI", "Grand Theft Auto VI", "gaming", "Shorts"],
            "categoryId": "20",
        },
        "status": {
            "privacyStatus": "private",
        },
    }
    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    status, headers, _ = request(
        init_url,
        json.dumps(metadata).encode(),
        {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(video.stat().st_size),
        },
        "POST",
    )
    upload_url = headers.get("Location") or headers.get("location")
    if status not in (200, 201) or not upload_url:
        raise RuntimeError("YouTube did not return a resumable upload URL.")

    _, _, result_raw = request(
        upload_url,
        video.read_bytes(),
        {"Authorization": "Bearer " + access_token, "Content-Type": "video/mp4"},
        "PUT",
    )
    video_id = json.loads(result_raw).get("id")
    if not video_id:
        raise RuntimeError("YouTube upload response did not contain a video ID.")
    video_url = "https://www.youtube.com/watch?v=" + video_id
    output("upload_status", "uploaded")
    output("video_url", video_url)
    print(json.dumps({"ok": True, "privacy": "private", "video_url": video_url}))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        output("upload_status", "failed")
        output("video_url", "")
        output("error", str(exc)[:1000])
        print("YOUTUBE_UPLOAD_FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
