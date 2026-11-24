#!/usr/bin/env python3
"""Discover recent public GTA VI videos from an operator-supplied channel/feed URL."""
import json
import os
import re
import subprocess
import urllib.error
import urllib.request

GTA6 = re.compile(r"\\b(gta\\s*6|gta\\s*vi|grand theft auto\\s*(vi|6))\\b", re.I)

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
        "--flat-playlist", "--dump-single-json", "--playlist-end", str(limit),
        channel_url,
    ]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=600)
    if not result.stdout.strip():
        raise RuntimeError("No public video entries were returned by yt-dlp: " + result.stderr[-1200:])
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("yt-dlp returned invalid playlist metadata.") from exc

    entries = data.get("entries") or [data]
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
            "creator": str(entry.get("channel") or entry.get("uploader") or data.get("uploader") or data.get("channel") or "Unknown")[:120],
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
