#!/usr/bin/env python3
"""Backfill visual fingerprints for earlier public Shorts and annotate duplicates."""
from __future__ import annotations
import concurrent.futures
import json
import subprocess
import tempfile
from pathlib import Path

try:
    from .visual_quality import compute_content_fingerprint, compare_content_fingerprints
except ImportError:
    from visual_quality import compute_content_fingerprint, compare_content_fingerprints

ROOT = Path(".github/published-clips")


def download_and_fingerprint(marker_path: Path):
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        existing = marker.get("content_fingerprint")
        if isinstance(existing, dict) and existing.get("version"):
            return marker_path.name, existing, None
        urls = [str(marker.get(key) or "").strip() for key in ("video_url", "source_url")]
        urls = [url for url in urls if url]
        last_error = "No public video/source URL recorded."
        with tempfile.TemporaryDirectory(prefix="gta6-fingerprint-") as temp:
            folder = Path(temp)
            for number, url in enumerate(urls):
                output = folder / f"source-{number}.%(ext)s"
                command = [
                    "yt-dlp", "--no-playlist", "--no-progress", "--retries", "3",
                    "--socket-timeout", "30", "-f", "best[height<=720]/best",
                    "--merge-output-format", "mp4", "-o", str(output), url
                ]
                result = subprocess.run(
                    command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=600
                )
                media = next((path for path in folder.glob(f"source-{number}.*")
                              if path.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")), None)
                if result.returncode == 0 and media is not None:
                    return marker_path.name, compute_content_fingerprint(media), None
                last_error = (result.stdout or "Download failed.")[-600:]
            return marker_path.name, None, last_error
    except Exception as exc:
        return marker_path.name, None, str(exc)[:600]


def main() -> int:
    paths = sorted(ROOT.glob("*.json"))
    if not paths:
        raise SystemExit("No earlier publication markers were found.")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results.extend(executor.map(download_and_fingerprint, paths))

    fingerprints = {}
    failures = []
    for name, fingerprint, error in results:
        if fingerprint:
            path = ROOT / name
            marker = json.loads(path.read_text(encoding="utf-8"))
            marker["content_fingerprint"] = fingerprint
            path.write_text(json.dumps(marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            fingerprints[name] = fingerprint
        else:
            failures.append({"marker": name, "error": error})

    duplicate_pairs = []
    names = sorted(fingerprints)
    for index, first_name in enumerate(names):
        for second_name in names[index + 1:]:
            match = compare_content_fingerprints(fingerprints[first_name], fingerprints[second_name])
            if not match["duplicate"]:
                continue
            first_path, second_path = ROOT / first_name, ROOT / second_name
            first = json.loads(first_path.read_text(encoding="utf-8"))
            second = json.loads(second_path.read_text(encoding="utf-8"))
            first_video = first.get("video_url", first_name)
            second_video = second.get("video_url", second_name)
            second["duplicate_content_of"] = first_video
            second["duplicate_similarity"] = match
            second_path.write_text(json.dumps(second, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            duplicate_pairs.append({
                "first": first_video,
                "second": second_video,
                "matched_frames": match["matched_frames"],
                "coverage": match["coverage"]
            })

    summary = {
        "markers_total": len(paths),
        "fingerprints_added_or_existing": len(fingerprints),
        "download_or_analysis_failures": len(failures),
        "existing_duplicate_pairs": duplicate_pairs,
        "failures": failures
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    Path("fingerprint-backfill-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Partial success is useful: unavailable/deleted uploads are listed in the
    # summary and do not prevent the available historical clips from being checked.
    return 0 if fingerprints else 1


if __name__ == "__main__":
    raise SystemExit(main())
