#!/usr/bin/env python3
"""Upload a rendered Short privately with a future YouTube auto-publish time."""
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
        with urllib.request.urlopen(req, timeout=600) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as e:
        if e.code == 308:
            return e.code, dict(e.headers), e.read()
        detail = e.read().decode("utf-8", "replace")[:2500]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e

def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not (client_id and client_secret and refresh_token):
        output("upload_status", "not_configured")
        output("video_url", "")
        output("thumbnail_status", "not_configured")
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
    # Safety default: upload privately only. Never schedule public release
    # automatically; the channel owner must review rights, edits and metadata.
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["GTA 6", "GTA VI", "Grand Theft Auto VI", "GTA 6 gameplay", "GTA 6 clips", "gaming shorts", "Shorts"],
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

    # Stream the resumable upload in bounded chunks instead of loading the
    # entire MP4 into memory. YouTube acknowledges intermediate chunks with 308.
    total_size = video.stat().st_size
    chunk_size = 8 * 1024 * 1024
    offset = 0
    result_raw = b""
    while offset < total_size:
        with video.open("rb") as stream:
            stream.seek(offset)
            chunk = stream.read(min(chunk_size, total_size - offset))
        end = offset + len(chunk) - 1
        status, _, response_raw = request(
            upload_url,
            chunk,
            {
                "Authorization": "Bearer " + access_token,
                "Content-Type": "video/mp4",
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {offset}-{end}/{total_size}",
            },
            "PUT",
        )
        if status == 308:
            offset = end + 1
            continue
        if status not in (200, 201):
            raise RuntimeError(f"YouTube resumable upload returned unexpected HTTP {status}.")
        result_raw = response_raw
        offset = end + 1
        break
    if offset != total_size or not result_raw:
        raise RuntimeError("YouTube resumable upload ended before the final acknowledgement.")
    video_id = json.loads(result_raw).get("id")
    if not video_id:
        raise RuntimeError("YouTube upload response did not contain a video ID.")
    video_url = "https://www.youtube.com/watch?v=" + video_id
    thumbnail_status = "not_available"
    cover = Path("short-cover.jpg")
    if cover.is_file() and cover.stat().st_size:
        try:
            thumb_status, _, _ = request(
                "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=" + urllib.parse.quote(video_id),
                cover.read_bytes(),
                {"Authorization": "Bearer " + access_token, "Content-Type": "image/jpeg"},
                "POST",
            )
            thumbnail_status = "uploaded" if thumb_status in (200, 201) else "failed"
        except Exception as exc:
            thumbnail_status = "failed"
            print("YouTube thumbnail upload failed: " + str(exc)[:500], file=sys.stderr)
    output("upload_status", "uploaded_private")
    output("video_url", video_url)
    output("thumbnail_status", thumbnail_status)
     print(json.dumps({"ok": True, "privacy": "private",
                      "video_url": video_url, "thumbnail_status": thumbnail_status}))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        output("upload_status", "failed")
        output("video_url", "")
        output("thumbnail_status", "failed")
        output("error", str(exc)[:1000])
        print("YOUTUBE_UPLOAD_FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
