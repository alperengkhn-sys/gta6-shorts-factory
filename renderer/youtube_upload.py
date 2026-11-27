#!/usr/bin/env python3
"""Automatically publish a rendered Short publicly on the configured YouTube channel."""
import json
import os
import sys
import time
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


def upload_custom_thumbnail(video_id, cover, access_token, granted_scopes):
    """Upload a custom Shorts thumbnail with the narrowest available OAuth scope."""
    scopes = set(granted_scopes or ())
    processing_read_scopes = {
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube",
    }
    thumbnail_upload_scopes = {
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtubepartner",
    }
    if scopes and not (scopes & thumbnail_upload_scopes):
        return "missing_thumbnail_upload_scope"

    if scopes & processing_read_scopes:
        processing_ready = False
        for attempt in range(40):
            status_url = (
                "https://www.googleapis.com/youtube/v3/videos?part=processingDetails,status&id="
                + urllib.parse.quote(video_id)
            )
            _, _, status_raw = request(
                status_url,
                headers={"Authorization": "Bearer " + access_token},
                method="GET",
            )
            items = json.loads(status_raw).get("items", [])
            if not items:
                raise RuntimeError("YouTube processing status did not return the uploaded video.")
            item = items[0]
            upload_status = str(item.get("status", {}).get("uploadStatus", ""))
            if upload_status in ("rejected", "failed"):
                reason = item.get("status", {}).get("rejectionReason", "unknown")
                raise RuntimeError("YouTube rejected the uploaded video: " + str(reason))
            processing_status = str(item.get("processingDetails", {}).get("processingStatus", ""))
            if processing_status == "succeeded":
                processing_ready = True
                break
            if processing_status == "failed":
                reason = item.get("processingDetails", {}).get("processingFailureReason", "unknown")
                raise RuntimeError("YouTube video processing failed: " + str(reason))
            print(
                f"YOUTUBE_PROCESSING_WAIT: status={processing_status or 'not_ready'} "
                f"attempt={attempt + 1}/40",
                flush=True,
            )
            time.sleep(15)
        if not processing_ready:
            return "processing_timeout"
    else:
        # Official thumbnails.set accepts youtube.upload. Read scope is only
        # needed to poll processingDetails, so retain the working time-buffer
        # path rather than skipping the user's requested cover altogether.
        print(
            "YOUTUBE_PROCESSING_WAIT: no read scope; waiting 120 seconds before thumbnails.set "
            "using youtube.upload.",
            flush=True,
        )
        time.sleep(120)

    status, _, _ = request(
        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId="
        + urllib.parse.quote(video_id),
        Path(cover).read_bytes(),
        {"Authorization": "Bearer " + access_token, "Content-Type": "image/jpeg"},
        "POST",
    )
    if status not in (200, 201):
        raise RuntimeError(f"YouTube thumbnails.set returned unexpected HTTP {status}.")
    return "uploaded"


def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
    missing = [name for name, value in (
        ("YOUTUBE_CLIENT_ID", client_id),
        ("YOUTUBE_CLIENT_SECRET", client_secret),
        ("YOUTUBE_REFRESH_TOKEN", refresh_token),
    ) if not value]
    if missing:
        message = "Missing required GitHub Actions secrets: " + ", ".join(missing)
        output("upload_status", "failed")
        output("video_url", "")
        output("thumbnail_status", "failed")
        output("error", message)
        print("YOUTUBE_UPLOAD_FAILED: " + message, file=sys.stderr)
        return 1

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
    token_info = json.loads(token_raw)
    access_token = token_info["access_token"]
    granted_scopes = set(str(token_info.get("scope", "")).split())

    title = os.environ.get("SHORT_TITLE", "GTA 6 Short").strip()[:100]
    description = os.environ.get(
        "SHORT_DESCRIPTION",
        "Grand Theft Auto VI gaming moment. #GTA6 #GTAVI #Shorts",
    ).strip()[:5000]
    privacy = os.environ.get("SHORT_PRIVACY_STATUS", "public").strip().lower()
    if privacy not in ("public", "private", "unlisted"):
        raise RuntimeError("SHORT_PRIVACY_STATUS must be public, private, or unlisted.")
    raw_tags = os.environ.get("SHORT_TAGS", "").strip()
    tags = []
    if raw_tags:
        try:
            parsed_tags = json.loads(raw_tags)
            if isinstance(parsed_tags, list):
                tags = [str(tag).strip() for tag in parsed_tags if str(tag).strip()]
        except json.JSONDecodeError:
            tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    if not tags:
        tags = ["GTA 6", "GTA VI", "Grand Theft Auto VI", "GTA 6 gameplay", "GTA 6 clips", "gaming shorts", "Shorts"]
    # YouTube's combined tag text is limited; keep the most relevant tags first.
    limited_tags = []
    tag_chars = 0
    for tag in tags:
        if tag_chars + len(tag) + 1 > 480:
            continue
        if tag.lower() not in {existing.lower() for existing in limited_tags}:
            limited_tags.append(tag)
            tag_chars += len(tag) + 1
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": limited_tags,
            "categoryId": "20",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            # Allow legitimate off-platform embeds and sharing; this does not affect Shorts-feed eligibility.
            "embeddable": True,
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
            thumbnail_status = upload_custom_thumbnail(
                video_id, cover, access_token, granted_scopes
            )
            if thumbnail_status == "uploaded":
                print("YOUTUBE_THUMBNAIL_UPLOADED: custom Shorts cover accepted by YouTube.", flush=True)
            elif thumbnail_status == "processing_timeout":
                print("YOUTUBE_THUMBNAIL_PENDING: processing did not finish within ten minutes.", file=sys.stderr)
            else:
                print("YOUTUBE_THUMBNAIL_FAILED: OAuth scope does not permit thumbnails.set.", file=sys.stderr)
        except Exception as exc:
            thumbnail_status = "failed"
            print("YOUTUBE_THUMBNAIL_FAILED: " + str(exc)[:700], file=sys.stderr)
    output("upload_status", "uploaded_" + privacy)
    output("video_url", video_url)
    output("thumbnail_status", thumbnail_status)
    print(json.dumps({"ok": True, "privacy": privacy,
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
