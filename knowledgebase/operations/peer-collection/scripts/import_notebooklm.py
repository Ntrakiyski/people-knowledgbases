#!/usr/bin/env python3
"""Import an initial balanced batch using two task-owned NotebookLM notebooks.

Every command pins the notebook. Source creation is serial and paced. Existing
source IDs are reconciled on restart, including after an ambiguous CLI timeout.
No source or notebook is deleted.
"""
from __future__ import annotations
from layout import CREATORS

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from layout import ROOT
NOTEBOOKS = ["3fbc2cd7-c4fa-4d66-af45-c63f5edeb34b", "d365d84e-d246-4769-9937-d336cf2d0d63"]
ORDER = ["codie-sanchez", "alex-hormozi", "dan-martell", "nick-huber", "sahil-bloom"]


def save(path: Path, data: object) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def cli(*args: str, timeout: int = 100) -> dict:
    result = subprocess.run(["notebooklm", *args, "--json"], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # Do not persist raw CLI diagnostic bodies, which may contain auth data.
        raise RuntimeError(f"NotebookLM command failed ({args[0]}, exit {result.returncode})")
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-creator", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.per_creator <= 40:
        parser.error("Selected scope supports 1–40 videos per creator; capacity is checked before each addition")
    registry_path = ROOT / "notebook-sources.json"
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    counts = {}
    for notebook in NOTEBOOKS:
        rows = cli("source", "list", "--notebook", notebook, "--limit", "100")["sources"]
        counts[notebook] = len(rows)
        for source in rows:
            if source.get("url"):
                registry[source["url"]] = {"notebook_id": notebook, "source_id": source["id"], "status": source["status"]}
    save(registry_path, registry)
    catalogs = {slug: json.loads((CREATORS / slug / "catalog.json").read_text())["videos"] for slug in ORDER}
    selected = [(slug, catalogs[slug][rank]) for rank in range(args.per_creator) for slug in ORDER]
    for number, (slug, video) in enumerate(selected, 1):
        folder = CREATORS / slug
        manifest_path = folder / "raw/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        if any(v["youtube_id"] == video["youtube_id"] for v in manifest["videos"]):
            continue
        print(f"[{number}/{len(selected)}] {slug}: {video['title']}", flush=True)
        try:
            record = registry.get(video["url"])
            if record is None:
                notebook = next((n for n in NOTEBOOKS if counts[n] < 50), None)
                if notebook is None:
                    print("STOP: task-owned notebooks are full; no existing data was deleted.", flush=True)
                    break
                response = cli("source", "add", "--notebook", notebook, video["url"], "--type", "youtube")
                source = response["source"]
                record = {"notebook_id": notebook, "source_id": source["id"], "status": "processing"}
                registry[video["url"]] = record
                counts[notebook] += 1
                save(registry_path, registry)
                time.sleep(2)
            notebook, source_id = record["notebook_id"], record["source_id"]
            source = cli("source", "list", "--notebook", notebook, "--limit", "100")
            match = next(v for v in source["sources"] if v["id"] == source_id)
            record["status"] = match["status"]
            if match["status"] != "ready":
                manifest.setdefault("failed_videos", []).append({"youtube_id": video["youtube_id"], "reason": "NotebookLM source is not ready"})
                save(manifest_path, manifest)
                continue
            data = cli("source", "fulltext", source_id, "--notebook", notebook)
            text = data.get("content", "")
            if len(text.split()) < 20:
                raise ValueError("Fulltext export is empty or implausibly short")
            export_dir = folder / "exports/notebooklm"
            export_dir.mkdir(parents=True, exist_ok=True)
            exported = f"# {data['title']}\n\n{video['url']}\n\n{text}\n"
            export_path = export_dir / f"{video['youtube_id']}.md"
            if export_path.exists() and export_path.read_text() != exported:
                raise ValueError("Existing export differs; kept immutable original")
            export_path.write_text(exported)
            raw_path = folder / "raw" / f"{video['slug']}.md"
            metadata = {"type": "raw-transcript", "title": data["title"], "youtube_id": video["youtube_id"], "url": video["url"], "slug": video["slug"], "provider": "notebooklm", "timestamped": False, "immutable": True, "fetched_at": datetime.now(timezone.utc).isoformat(), "notebook_id": notebook, "source_id": source_id}
            content = "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()) + "\n---\n\n## Transcript\n\n" + text + "\n"
            if raw_path.exists():
                original = raw_path.read_text()
                if f'youtube_id: "{video["youtube_id"]}"' not in original.split("\n---", 1)[0] or original.split("\n## Transcript\n\n", 1)[-1] != text + "\n":
                    raise ValueError("Unregistered raw transcript differs; kept immutable original")
                content = original
            else:
                raw_path.write_text(content)
            manifest["videos"].append({**video, **record, "provider": "notebooklm", "timestamped": False, "sha256": hashlib.sha256(content.encode()).hexdigest(), "export_sha256": hashlib.sha256(exported.encode()).hexdigest()})
            manifest["failed_videos"] = [v for v in manifest.get("failed_videos", []) if v["youtube_id"] != video["youtube_id"]]
            manifest.update({"transcripts_fetched": len(manifest["videos"]), "total_videos": len(catalogs[slug]), "updated_at": datetime.now(timezone.utc).isoformat()})
            save(manifest_path, manifest)
            save(registry_path, registry)
            print(f"  Saved {len(text.split())} words; exact-text citations available, timestamps unavailable.", flush=True)
        except (RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as error:
            manifest.setdefault("failed_videos", []).append({"youtube_id": video["youtube_id"], "reason": str(error) if isinstance(error, (RuntimeError, ValueError)) else type(error).__name__})
            save(manifest_path, manifest)
            print(f"  STOP: {type(error).__name__}; checkpoint saved. Reconcile source list before retry.", flush=True)
            break


if __name__ == "__main__":
    main()
