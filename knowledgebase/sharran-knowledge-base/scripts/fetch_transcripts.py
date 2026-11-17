#!/usr/bin/env python3
"""Import timestamped captions from the saved channel catalog, with checkpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def write_json(path: Path, data: object) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def stamp(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds % 3600 // 60:02}:{seconds % 60:02}"


def supadata(video_id: str, api_key: str) -> list[dict]:
    query = urllib.parse.urlencode({
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "lang": "en", "text": "false", "mode": "native",
    })
    request = urllib.request.Request(
        "https://api.supadata.ai/v1/transcript?" + query,
        headers={"x-api-key": api_key, "User-Agent": "sharran-knowledge-base/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        # Never include request headers, keys, or the provider's raw error body.
        raise RuntimeError(f"Supadata HTTP {error.code}") from None
    content = data.get("content")
    if not isinstance(content, list) or not content:
        raise RuntimeError("Supadata did not return a timestamped native transcript")
    return [{"start": float(row["offset"]) / 1000, "text": row["text"]}
            for row in content]


def ytdlp(video_id: str) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="sharran-captions-") as temporary:
        result = subprocess.run([
            "yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
            "--sub-langs", "en.*,en", "--sub-format", "json3", "--no-warnings",
            "--socket-timeout", "30", "--retries", "1", "--no-playlist",
            "-o", str(Path(temporary) / "captions.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ], capture_output=True, text=True, timeout=150)
        if result.returncode:
            if "not a bot" in result.stderr or "confirm you" in result.stderr:
                raise RuntimeError("YouTube blocked this server with a sign-in challenge")
            raise RuntimeError("yt-dlp could not fetch captions; retry or use Supadata")
        files = sorted(Path(temporary).glob("*.json3"))
        if not files:
            raise RuntimeError("No English captions returned")
        data = json.loads(files[0].read_text())
        return [{"start": event.get("tStartMs", 0) / 1000,
                 "text": "".join(seg.get("utf8", "") for seg in event["segs"]).strip()}
                for event in data.get("events", []) if event.get("segs")]


def render(video: dict, segments: list[dict], provider: str) -> str:
    paragraphs, buffer, start = [], [], None
    previous = -1.0
    for segment in segments:
        seconds = float(segment["start"])
        if seconds < previous or seconds < 0:
            raise ValueError("Caption timestamps must be nonnegative and ordered")
        previous = seconds
        text = re.sub(r"\s+", " ", segment["text"]).strip()
        if not text:
            continue
        if start is None:
            start = seconds
        buffer.append(text)
        if sum(len(item.split()) for item in buffer) >= 50:
            paragraphs.append((start, " ".join(buffer)))
            buffer, start = [], None
    if buffer:
        paragraphs.append((start, " ".join(buffer)))
    if not paragraphs:
        raise ValueError("Caption response contains no text")
    metadata = {
        "type": "raw-transcript", "title": video["title"],
        "youtube_id": video["youtube_id"], "url": video["url"],
        "slug": video["slug"], "published": video.get("published", ""),
        "duration": stamp(video.get("duration_seconds") or previous),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider, "immutable": True,
    }
    frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}"
                            for key, value in metadata.items())
    body = "\n\n".join(f"**[{stamp(seconds)}]** {text}" for seconds, text in paragraphs)
    return f"---\n{frontmatter}\n---\n\n## Transcript\n\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["yt-dlp", "supadata"], default="yt-dlp")
    parser.add_argument("--limit", type=int, help="Maximum pending videos to attempt")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()
    if args.delay < 0 or (args.limit is not None and args.limit < 1):
        parser.error("--delay must be nonnegative; --limit must be positive")
    api_key = os.environ.get("SUPADATA_API_KEY", "")
    if args.provider == "supadata" and not api_key:
        parser.error("Set SUPADATA_API_KEY in the process environment")
    catalog = json.loads((ROOT / "catalog.json").read_text())
    manifest_path = ROOT / "raw" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    imported = {row["youtube_id"]: row for row in manifest["videos"]}
    failures = {row["youtube_id"]: row for row in manifest.get("failed_videos", [])}
    candidates = [row for row in catalog["videos"] if row["youtube_id"] not in imported]
    if args.limit:
        candidates = candidates[:args.limit]
    failed = False
    for index, video in enumerate(candidates, 1):
        video_id = video["youtube_id"]
        print(f"[{index}/{len(candidates)}] {video['title']}", flush=True)
        stop = False
        try:
            target = ROOT / "raw" / f"{video['slug']}.md"
            if not target.exists():
                segments = supadata(video_id, api_key) if args.provider == "supadata" else ytdlp(video_id)
                content = render(video, segments, args.provider)
                temporary = target.with_suffix(".tmp")
                temporary.write_text(content, encoding="utf-8")
                temporary.replace(target)
            else:
                # Recover a transcript written just before a previous process stopped.
                content = target.read_text(encoding="utf-8")
                if f'youtube_id: "{video_id}"' not in content or "**[" not in content:
                    raise ValueError("Existing raw file does not match this video")
            imported[video_id] = {**video, "sha256": hashlib.sha256(content.encode()).hexdigest()}
            failures.pop(video_id, None)
            print("  Imported", flush=True)
        except (RuntimeError, ValueError, KeyError, TypeError, OSError,
                subprocess.SubprocessError) as error:
            failed = True
            # Only known, sanitized errors are persisted.
            reason = str(error) if isinstance(error, (RuntimeError, ValueError)) else type(error).__name__
            failures[video_id] = {"youtube_id": video_id, "title": video["title"],
                                  "reason": reason}
            print(f"  Failed: {reason}", flush=True)
            stop = "blocked this server" in reason or any(
                f"HTTP {code}" in reason for code in (401, 402, 403, 429))
        manifest.update({"updated_at": datetime.now(timezone.utc).isoformat(),
                         "total_videos": len(catalog["videos"]),
                         "transcripts_fetched": len(imported), "videos": list(imported.values()),
                         "failed_videos": list(failures.values())})
        write_json(manifest_path, manifest)
        if stop:
            print("Stopped after an access or rate-limit error. Rerun to resume.", flush=True)
            break
        if index < len(candidates):
            time.sleep(args.delay)
    print(f"{len(imported)}/{len(catalog['videos'])} transcripts imported.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
