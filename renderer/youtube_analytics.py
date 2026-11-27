#!/usr/bin/env python3
"""Fetch channel-owned Shorts analytics using an explicitly authorized YouTube OAuth token."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


TOKEN_URL = "https://oauth2.googleapis.com/token"
REPORT_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
REQUIRED_SCOPES = {
    "https://www.googleapis.com/auth/yt-analytics.readonly",
}
METRICS = (
    "engagedViews,views,estimatedMinutesWatched,averageViewDuration,"
    "averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost"
)


def request_json(url: str, *, data: bytes | None = None, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1200]
        raise RuntimeError(f"YouTube API HTTP {exc.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("YouTube Analytics request failed: " + str(exc)[:500]) from None


def refresh_access_token() -> tuple[str, set[str]]:
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
    payload = request_json(TOKEN_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    token = str(payload.get("access_token") or "")
    if not token:
        raise RuntimeError("Google OAuth returned no access token.")
    return token, set(str(payload.get("scope", "")).split())


def query_report(access_token: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    return request_json(REPORT_URL + "?" + query, headers={"Authorization": "Bearer " + access_token})


def as_number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fmt(value, digits=1) -> str:
    number = as_number(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows returned for this date range._"
    esc = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    top = "| " + " | ".join(esc(x) for x in headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(esc(x) for x in row) + " |" for row in rows]
    return "\n".join([top, sep, *body])


def published_shorts(marker_dir: Path | None = None) -> dict[str, str]:
    """Return published Shorts IDs/titles from the factory's upload markers."""
    root = marker_dir or Path(".github/published-clips")
    found: dict[str, str] = {}
    for path in sorted(root.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        url = str(item.get("video_url") or item.get("youtube_url") or "").strip()
        parsed = urllib.parse.urlparse(url)
        video_id = ""
        if parsed.hostname in {"youtu.be", "www.youtu.be"}:
            video_id = parsed.path.strip("/").split("/")[0]
        elif parsed.hostname and parsed.hostname.endswith("youtube.com"):
            video_id = (urllib.parse.parse_qs(parsed.query).get("v") or [""])[0]
            if not video_id:
                parts = [part for part in parsed.path.split("/") if part]
                if len(parts) >= 2 and parts[0] in {"shorts", "embed"}:
                    video_id = parts[1]
        if video_id:
            found[video_id] = str(item.get("title") or video_id)
    return found


def build_video_report_params(common: dict[str, str], video_ids: list[str]) -> dict[str, str] | None:
    """Google permits video dimension if the query filters on multiple video IDs."""
    ids = [value for value in video_ids if value]
    if not ids:
        return None
    return {
        **common,
        "dimensions": "video",
        "filters": "video==" + ",".join(ids[:500]),
        "maxResults": "200",
    }


def append_summary(markdown: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if path:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(markdown.rstrip() + "\n")
    print(markdown)


def main() -> int:
    token, scopes = refresh_access_token()
    missing = REQUIRED_SCOPES - scopes
    if missing:
        append_summary(
            "# VI RUSH — YouTube Analytics\n\n"
            "**REAUTHORIZATION REQUIRED**\n\n"
            "The current refresh token can publish videos but cannot read private channel analytics. "
            "Reauthorize the YouTube account with the read-only scope below, then replace the "
            "`YOUTUBE_REFRESH_TOKEN` GitHub Actions secret.\n\n"
            + "\n".join("- `" + scope + "`" for scope in sorted(missing))
            + "\n\nNo analytics values were available to this run."
        )
        return 0

    today = dt.datetime.now(dt.timezone.utc).date()
    end_date = today - dt.timedelta(days=1)
    start_date = end_date - dt.timedelta(days=27)
    common = {
        "ids": "channel==MINE",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "metrics": METRICS,
    }

    shorts = published_shorts()
    top_params = build_video_report_params(common, list(shorts))
    top = query_report(token, top_params) if top_params else {"columnHeaders": [], "rows": []}
    top_headers = [item.get("name", "") for item in top.get("columnHeaders", [])]
    top_rows = []
    for values in top.get("rows", []):
        row = dict(zip(top_headers, values))
        video_id = str(row.get("video", ""))
        top_rows.append([
            shorts.get(video_id, video_id),
            video_id,
            fmt(row.get("views")),
            fmt(row.get("engagedViews")),
            fmt(row.get("likes")),
            fmt(row.get("comments")),
            fmt(row.get("shares")),
            fmt(row.get("subscribersGained")),
            fmt(row.get("subscribersLost")),
            fmt(row.get("estimatedMinutesWatched")),
            fmt(row.get("averageViewDuration"), 2),
            fmt(row.get("averageViewPercentage"), 1) + "%",
        ])
    top_rows.sort(key=lambda row: as_number(row[2].replace(",", "")), reverse=True)

    daily = query_report(token, {
        **common,
        "dimensions": "day,creatorContentType",
        "sort": "day",
        "maxResults": "200",
    })
    daily_headers = [item.get("name", "") for item in daily.get("columnHeaders", [])]
    daily_rows = []
    for values in daily.get("rows", []):
        row = dict(zip(daily_headers, values))
        if str(row.get("creatorContentType", "")).upper() != "SHORTS":
            continue
        daily_rows.append([
            str(row.get("day", "")),
            fmt(row.get("views")),
            fmt(row.get("likes")),
            fmt(row.get("comments")),
            fmt(row.get("shares")),
            fmt(row.get("subscribersGained")),
            fmt(row.get("subscribersLost")),
            fmt(row.get("estimatedMinutesWatched")),
        ])

    append_summary(
        "# VI RUSH — YouTube Shorts Analytics\n\n"
        f"**Period:** {start_date.isoformat()} to {end_date.isoformat()} (UTC; latest complete day only)\n\n"
        "## Best-performing Shorts\n\n"
        + markdown_table(
            ["Short title", "Video ID", "Views", "Engaged", "Likes", "Comments", "Shares", "Subs +", "Subs −", "Watch min", "Avg sec", "Avg viewed"],
            top_rows,
        )
        + "\n\n## Daily Shorts activity\n\n"
        + markdown_table(["Date", "Views", "Likes", "Comments", "Shares", "Subs +", "Subs −", "Watch min"], daily_rows)
        + "\n\n**Interpretation:** zero views means no measured views in this report window; it does not by itself identify the reason for low distribution. YouTube Studio separately shows Shorts Feed appearances and viewed-versus-swiped-away metrics; these feed metrics are not returned by this Analytics API report."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("YOUTUBE_ANALYTICS_FAILED: " + str(exc), file=sys.stderr)
        sys.exit(1)
