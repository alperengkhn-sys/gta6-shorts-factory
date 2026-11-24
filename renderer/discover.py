#!/usr/bin/env python3
"""Discover recent public GTA VI videos from an operator-supplied channel/feed URL."""
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from urllib.parse import urlparse
# Match GTA VI spellings in video titles using normal regex word boundaries.
GTA6 = re.compile(r"\b(gta\s*6|gta\s*vi|grand theft auto\s*(vi|6))\b", re.I)

CHANNEL_ID = re.compile(r'(?:"channelId"|"externalId"|channelId|externalId)\s*[:=]\s*["\']?(UC[a-zA-Z0-9_-]{22})')


def channel_uploads_playlist(channel_url, page_html=None):
    """Resolve a channel's canonical uploads playlist even when /videos is absent."""
    parsed = urlparse(channel_url)
    match = re.search(r"/channel/(UC[a-zA-Z0-9_-]{22})", parsed.path)
    channel_id = match.group(1) if match else None
    if not channel_id and page_html is None:
        request = urllib.request.Request(
            channel_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GTA6ShortsFactory/1.0)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                page_html = response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError):
            page_html = ""
    if not channel_id and page_html:
        match = CHANNEL_ID.search(page_html)
        if not match:
            match = re.search(r'<meta[^>]+itemprop=["\']channelId["\'][^>]+content=["\'](UC[a-zA-Z0-9_-]{22})', page_html, re.I)
        if match:
            channel_id = match.group(1)
    if not channel_id:
        return None
    return "https://www.youtube.com/playlist?list=UU" + channel_id[2:]


def main():
    channel_url = os.environ["CHANNEL_URL"].strip()
    callback_url = os.environ["CALLBACK_URL"].strip()
    limit = max(1, min(30, int(os.environ.get("MAX_ITEMS", "10"))))
    secret = os.environ.get("RENDER_WEBHOOK_SECRET", "").strip()
    rights_confirmation = os.environ.get("RIGHTS_CONFIRMATION", "").lower() == "true"
    if not channel_url.startswith("https://") or not callback_url.startswith("https://"):
        raise SystemExit("Channel and callback URLs must use HTTPS.")
    if not secret or not rights_confirmation:
        raise SystemExit("Rights attestation or callback secret is missing.")

    command = [
        "yt-dlp", "--quiet", "--no-warnings", "--ignore-errors",
        "--flat-playlist", "--dump-json", "--playlist-end", str(limit),
        channel_url,
    ]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=600)
    entries = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            entries.append(item)
    if not entries:
        root = channel_url.rstrip("/")
        if root.endswith("/videos") or root.endswith("/shorts"):
            root = root.rsplit("/", 1)[0]
        candidates = [root + "/shorts", root + "/videos", root + "/playlists", root]
        tried = {channel_url}
        for fallback_url in candidates:
            if fallback_url in tried:
                continue
            tried.add(fallback_url)
            print("DISCOVERY_FALLBACK trying " + fallback_url, flush=True)
            command[-1] = fallback_url
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=600)
            for line in result.stdout.splitlines():
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    entries.append(item)
            if entries:
                break
    if not entries:
        uploads_url = channel_uploads_playlist(channel_url)
        if uploads_url and uploads_url not in tried:
            print("DISCOVERY_FALLBACK using canonical uploads playlist " + uploads_url, flush=True)
            command[-1] = uploads_url
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=600)
            for line in result.stdout.splitlines():
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    entries.append(item)
    if not entries:
        detail = (result.stderr or result.stdout or "yt-dlp returned no video entries.").strip()
        raise RuntimeError("No public video entries were returned by yt-dlp after channel-tab and uploads-playlist fallbacks: " + detail[-1800:])
    items = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title") or "").strip()[:180]
        if not title or not GTA6.search(title):
            continue
        url = str(entry.get("webpage_url") or entry.get("original_url") or entry.get("url") or "").strip()
        extractor = str(entry.get("extractor_key") or entry.get("ie_key") or "").lower()
        if url and not url.startswith(("http://", "https://")) and "youtube" in extractor:
            url = "https://www.youtube.com/watch?v=" + url
        if not url.startswith("https://") or url in seen:
            continue
        seen.add(url)
        items.append({
            "url": url,
            "title": title,
            "creator": str(entry.get("channel") or entry.get("uploader") or "Unknown")[:120],
        })

    payload = {
        "channel_url": channel_url,
        "rights_confirmation": rights_confirmation,
        "items": items,
        "scanned": len(entries),
    }
    request = urllib.request.Request(
        callback_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; GTA6ShortsFactory/1.0; +https://github.com/alperengkhn-sys/gta6-shorts-factory)",
            "X-Render-Secret": secret,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8", "replace")
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Worker callback HTTP {response.status}: {body[:1200]}")
            print(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:1200]
        if exc.code == 403 and "1010" in body:
            raise RuntimeError(
                "Cloudflare blocked the GitHub Actions callback (Error 1010) before it reached the Worker. "
                "Allow this callback path in Cloudflare Security/WAF or disable Browser Integrity Check for the Worker hostname. "
                "Response: " + body
            ) from exc
        raise RuntimeError(f"Worker callback HTTP {exc.code}: {body}") from exc
    print(f"DISCOVERY_COMPLETE scanned={len(entries)} gta6_candidates={len(items)}")

if __name__ == "__main__":
    main()
