#!/usr/bin/env python3
"""Resume the full catalogs with timestamped native captions from Supadata.

Reads a key from the process environment or a secure-input file. Never logs it.
Already imported transcripts, including NotebookLM fallbacks, stay immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

import requests

from import_notebooklm import ROOT, ORDER, save


def stamp(seconds: float) -> str:
    value = int(seconds)
    return f"{value // 3600}:{value % 3600 // 60:02}:{value % 60:02}"


def render(video: dict, response: dict) -> str:
    segments = response.get("content")
    if not isinstance(segments, list) or not segments:
        raise ValueError("No timestamped native transcript returned")
    if response.get("lang") and not response["lang"].startswith("en"):
        raise ValueError("Provider returned a non-English transcript")
    paragraphs, words, start, previous = [], [], None, -1.0
    for row in segments:
        second = float(row["offset"]) / 1000
        if second < previous or second < 0:
            raise ValueError("Transcript timestamps are not ordered")
        previous = second
        text = re.sub(r"\s+", " ", row["text"]).strip()
        if not text:
            continue
        if start is None:
            start = second
        words.append(text)
        if sum(len(w.split()) for w in words) >= 50:
            paragraphs.append((start, " ".join(words)))
            words, start = [], None
    if words:
        paragraphs.append((start, " ".join(words)))
    if not paragraphs:
        raise ValueError("Transcript contains no text")
    metadata = {"type": "raw-transcript", "title": video["title"], "youtube_id": video["youtube_id"], "url": video["url"], "slug": video["slug"], "provider": "supadata-native", "timestamped": True, "immutable": True, "fetched_at": datetime.now(timezone.utc).isoformat()}
    body = "\n\n".join(f"**[{stamp(second)}]** {text}" for second, text in paragraphs)
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()) + "\n---\n\n## Transcript\n\n" + body + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--limit", type=int, help="Maximum pending videos to attempt")
    args = parser.parse_args()
    key = args.key_file.read_text().strip() if args.key_file else os.environ.get("SUPADATA_API_KEY", "")
    if not key:
        parser.error("Provide SUPADATA_API_KEY or --key-file through secure input")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    queues = []
    for slug in ORDER:
        folder = ROOT / slug
        imported = {v["youtube_id"] for v in json.loads((folder / "raw/manifest.json").read_text())["videos"]}
        selected = set(json.loads((folder / "selection.json").read_text())["videos"])
        queues.append([(folder, v) for v in json.loads((folder / "catalog.json").read_text())["videos"] if v["youtube_id"] in selected and v["youtube_id"] not in imported])
    candidates = [item for rank in zip_longest(*queues) for item in rank if item is not None]
    if args.limit:
        candidates = candidates[:args.limit]
    session = requests.Session()
    session.headers.update({"x-api-key": key, "User-Agent": "creator-knowledge-bases/1.0"})
    for number, (folder, video) in enumerate(candidates, 1):
        manifest_path = folder / "raw/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        print(f"[{number}/{len(candidates)}] {folder.name}/{video['youtube_id']}", flush=True)
        stop = False
        try:
            result = session.get("https://api.supadata.ai/v1/transcript", params={"url": video["url"], "lang": "en", "text": "false", "mode": "native"}, timeout=90)
            if not result.ok:
                stop = result.status_code in (401, 402, 403, 429)
                raise ValueError(f"Supadata HTTP {result.status_code}")
            response = result.json()
            content = render(video, response)
            path = folder / "raw" / f"{video['youtube_id']}.md"
            if path.exists():
                raise ValueError("Unregistered raw file exists; reconcile it before continuing")
            export_path = folder / "exports/supadata" / f"{video['youtube_id']}.json"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            if export_path.exists():
                raise ValueError("Unregistered provider export exists; reconcile before continuing")
            save(export_path, response)
            path.write_text(content)
            manifest["videos"].append({**video, "provider": "supadata-native", "timestamped": True, "sha256": hashlib.sha256(content.encode()).hexdigest(), "export_sha256": hashlib.sha256(export_path.read_bytes()).hexdigest()})
            manifest["failed_videos"] = [v for v in manifest.get("failed_videos", []) if v["youtube_id"] != video["youtube_id"]]
            print("  Imported timestamped native captions.", flush=True)
        except (ValueError, KeyError, TypeError, requests.RequestException) as error:
            reason = str(error) if isinstance(error, ValueError) else type(error).__name__
            manifest["failed_videos"] = [v for v in manifest.get("failed_videos", []) if v["youtube_id"] != video["youtube_id"]]
            manifest["failed_videos"].append({"youtube_id": video["youtube_id"], "reason": reason})
            print(f"  Failed: {reason}", flush=True)
        manifest.update({"transcripts_fetched": len(manifest["videos"]), "updated_at": datetime.now(timezone.utc).isoformat()})
        save(manifest_path, manifest)
        if stop:
            print("Stopped at an access, credit or rate limit; checkpoints retained.", flush=True)
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
