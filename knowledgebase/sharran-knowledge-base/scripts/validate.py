#!/usr/bin/env python3
"""Validate channel membership, transcript integrity, quotes, and coverage."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAGRAPH = re.compile(r"\*\*\[(\d+:\d{2}:\d{2})\]\*\*\s*(.*?)(?=\n\n|\Z)", re.S)
CITATION = re.compile(
    r'^- \[[^\n]+?\]\((?:\.\./)+sources/([^/)]+)\.md\) - "\[(\d+:\d{2}:\d{2})\] (.+)"$',
    re.M,
)


def normalized(text: str) -> str:
    return " ".join(text.split())


def field(text: str, name: str) -> object:
    frontmatter = text.split("\n---", 1)[0]
    match = re.search(rf"^{name}:\s*(.+)$", frontmatter, re.M)
    if not match:
        return None
    try:
        return json.loads(match[1])
    except json.JSONDecodeError:
        return match[1].strip().strip('"').strip("'")


def validate(require_complete: bool = False) -> list[str]:
    config = json.loads((ROOT / "channel.json").read_text())
    catalog = json.loads((ROOT / "catalog.json").read_text())
    manifest = json.loads((ROOT / "raw" / "manifest.json").read_text())
    errors = []
    if catalog["channel_id"] != config["channel_id"]:
        errors.append("Catalog belongs to a different channel")
    videos = catalog["videos"]
    by_id = {video["youtube_id"]: video for video in videos}
    by_slug = {video["slug"]: video for video in videos}
    if len(by_id) != len(videos) or len(by_slug) != len(videos):
        errors.append("Catalog contains duplicate video IDs or paths")
    if catalog["total_videos"] != len(videos):
        errors.append("Catalog total does not match video records")
    imported = {video["youtube_id"]: video for video in manifest["videos"]}
    if manifest["transcripts_fetched"] != len(imported):
        errors.append("Manifest transcript count does not match video records")
    if len(imported) != len(manifest["videos"]):
        errors.append("Manifest contains duplicate video records")
    evidence = {}
    raw_files = [path for path in (ROOT / "raw").glob("*.md") if path.name != "index.md"]
    for path in raw_files:
        text = path.read_text()
        video_id = field(text, "youtube_id")
        if video_id not in by_id or by_id[video_id]["slug"] != path.stem:
            errors.append(f"Unknown video or incorrect path: {path.relative_to(ROOT)}")
            continue
        record = imported.get(video_id)
        if not record:
            errors.append(f"Transcript absent from manifest: {path.name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != record.get("sha256"):
            errors.append(f"Raw transcript hash mismatch: {path.name}")
        if field(text, "immutable") is not True:
            errors.append(f"Transcript is not marked immutable: {path.name}")
        paragraphs = PARAGRAPH.findall(text)
        if not paragraphs:
            errors.append(f"Transcript contains no timestamped text: {path.name}")
        evidence[path.stem] = {ts: normalized(body) for ts, body in paragraphs}
    for video_id, video in imported.items():
        if video_id not in by_id:
            errors.append(f"Imported video is absent from catalog: {video_id}")
        if not (ROOT / "raw" / f"{video['slug']}.md").exists():
            errors.append(f"Manifest references a missing transcript: {video_id}")
    source_files = [path for path in (ROOT / "sources").glob("*.md") if path.name != "index.md"]
    for path in source_files:
        text = path.read_text()
        video = by_slug.get(path.stem)
        if not video or field(text, "youtube_id") != video["youtube_id"]:
            errors.append(f"Source is not from this channel catalog: {path.name}")
        if path.stem not in evidence:
            errors.append(f"Source has no imported transcript: {path.name}")
        for heading in ("## Concepts covered", "## Entities", "## Key moments", "## Transcript"):
            if heading not in text:
                errors.append(f"Missing {heading} in {path.name}")
    pages = [path for path in (ROOT / "concepts").glob("*.md") if path.name != "index.md"]
    concepts = len(pages)
    pages += [path for path in (ROOT / "entities").rglob("*.md") if path.name != "index.md"]
    synthesis_complete = True
    frozen_path = ROOT / "scripts/manifest.json"
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text())
        subtypes = {"tool": "tools", "person": "people", "organization": "organizations"}
        expected = {f"concepts/{page['slug']}.md" for page in frozen["concepts"]}
        expected.update(f"entities/{subtypes[page['subtype']]}/{page['slug']}.md"
                        for page in frozen["entities"])
        actual = {str(path.relative_to(ROOT)) for path in pages}
        synthesis_complete = expected == actual
        for missing in sorted(expected - actual):
            errors.append(f"Canonical page is missing: {missing}")
        for extra in sorted(actual - expected):
            errors.append(f"Page is absent from canonical manifest: {extra}")
    quotes = 0
    for path in pages:
        text = path.read_text()
        source_section = text.split("\n## Sources\n", 1)
        citations = CITATION.findall(source_section[1]) if len(source_section) == 2 else []
        if not citations:
            errors.append(f"No verifiable source citations: {path.relative_to(ROOT)}")
        for slug, ts, quote in citations:
            quotes += 1
            if normalized(quote) not in evidence.get(slug, {}).get(ts, ""):
                errors.append(f"Quote not found at {slug} [{ts}] in {path.relative_to(ROOT)}")
            if not (ROOT / "sources" / f"{slug}.md").exists():
                errors.append(f"Cited video has no source summary: {slug}")
    complete = len(evidence) == len(source_files) == len(videos) and concepts > 0 and synthesis_complete
    if require_complete and not complete:
        errors.append("Channel corpus is incomplete")
    print(f"Coverage: {len(evidence)}/{len(videos)} transcripts, "
          f"{len(source_files)}/{len(videos)} summaries, {concepts} concepts.")
    print(f"Checked {quotes} exact quotations. Corpus {'complete' if complete else 'INCOMPLETE'}.")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    errors = validate(args.require_complete)
    for error in errors:
        print(f"ERROR: {error}")
    sys.exit(bool(errors))
