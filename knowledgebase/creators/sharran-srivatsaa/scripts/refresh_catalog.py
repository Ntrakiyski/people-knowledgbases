#!/usr/bin/env python3
"""Refresh the public Videos-tab catalog without downloading media."""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def save(info: dict) -> None:
    config = json.loads((ROOT / "channel.json").read_text())
    if info.get("channel_id") != config["channel_id"]:
        raise ValueError("YouTube returned a different channel")
    previous_path = ROOT / "catalog.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    old_slugs = {row["youtube_id"]: row["slug"] for row in previous.get("videos", [])}
    videos = []
    for rank, entry in enumerate(info.get("entries", []), 1):
        if not entry:
            continue
        video_id = entry["id"]
        slug = re.sub(r"[^a-z0-9]+", "-", entry["title"].lower()).strip("-")
        # A video ID keeps paths stable when titles collide or punctuation changes.
        published = (datetime.fromtimestamp(entry["timestamp"], timezone.utc).date().isoformat()
                     if entry.get("timestamp") else "")
        videos.append({"youtube_id": video_id, "title": entry["title"],
                       "url": f"https://www.youtube.com/watch?v={video_id}",
                       "slug": old_slugs.get(video_id, f"{slug[:100]}-{video_id}"),
                       "duration_seconds": entry.get("duration"),
                       "published": published, "recency_rank": rank})
    if not videos:
        raise ValueError("YouTube returned an empty catalog; kept the previous catalog")
    catalog = {"channel": config["url"], "channel_id": config["channel_id"],
               "channel_name": config["name"], "scope": config["scope"],
               "enumerated_at": datetime.now(timezone.utc).isoformat(),
               "total_videos": len(videos), "videos": videos}
    target = ROOT / "catalog.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(target)
    print(f"Saved {len(videos)} video records to catalog.json")


if __name__ == "__main__":
    config = json.loads((ROOT / "channel.json").read_text())
    result = subprocess.run(["yt-dlp", "--flat-playlist", "--dump-single-json",
                             "--skip-download", "--no-warnings", config["url"] + "/videos"],
                            capture_output=True, text=True, check=True, timeout=180)
    save(json.loads(result.stdout))
