#!/usr/bin/env python3
"""Check source identity, integrity, exact evidence, links, and honest coverage."""
from __future__ import annotations
from layout import CREATORS, peer_glob

import argparse
import hashlib
import json
import re
from pathlib import Path

from render import ROOT, locate_quote, transcript


def validate(root: Path = ROOT, require_complete: bool = False, require_full_archive: bool = False) -> list[str]:
    creators = CREATORS if root == ROOT else root
    configs = peer_glob("*/channel.json") if root == ROOT else root.glob("*/channel.json")
    errors = []
    counts = {"catalog": 0, "transcripts": 0, "sources": 0, "insights": 0}
    expected_ids = set()
    for config_path in sorted(configs):
        folder = config_path.parent
        config = json.loads(config_path.read_text())
        catalog = json.loads((folder / "catalog.json").read_text())
        manifest = json.loads((folder / "raw/manifest.json").read_text())
        if catalog["channel_id"] != config["channel_id"]:
            errors.append(f"Channel identity mismatch: {folder.name}")
        by_id = {v["youtube_id"]: v for v in catalog["videos"]}
        if len(by_id) != len(catalog["videos"]) or len(by_id) != catalog["total_videos"]:
            errors.append(f"Catalog duplicate or incorrect total: {folder.name}")
        selection_path = folder / "selection.json"
        selected_list = json.loads(selection_path.read_text())["videos"] if selection_path.exists() else list(by_id)
        selected = set(selected_list)
        if len(selected) != len(selected_list) or not selected.issubset(by_id):
            errors.append(f"Invalid selection: {folder.name}")
        if selection_path.exists() and selected_list != [v["youtube_id"] for v in catalog["videos"][:len(selected_list)]]:
            errors.append(f"Selection is not newest-first: {folder.name}")
        imported = {v["youtube_id"]: v for v in manifest["videos"]}
        if len(imported) != len(manifest["videos"]):
            errors.append(f"Duplicate manifest entry: {folder.name}")
        if manifest.get("transcripts_fetched", 0) != len(imported):
            errors.append(f"Incorrect transcript count: {folder.name}")
        for key, record in imported.items():
            if key not in by_id:
                errors.append(f"Video absent from catalog: {folder.name}/{key}")
                continue
            path = folder / "raw" / f"{key}.md"
            if not path.exists():
                errors.append(f"Missing transcript: {folder.name}/{key}")
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
                errors.append(f"Transcript hash mismatch: {folder.name}/{key}")
            content = path.read_text()
            for expected in [f'youtube_id: "{key}"', 'immutable: true']:
                if expected not in content.split("\n---", 1)[0]:
                    errors.append(f"Incorrect raw metadata: {folder.name}/{key}")
            exported = folder / "exports/notebooklm" / f"{key}.md"
            if record.get("provider") == "notebooklm":
                if not exported.exists():
                    errors.append(f"Missing export: {folder.name}/{key}")
                else:
                    if hashlib.sha256(exported.read_bytes()).hexdigest() != record["export_sha256"]:
                        errors.append(f"Export hash mismatch: {folder.name}/{key}")
                    lines = exported.read_text().splitlines()
                    if not lines[0].startswith("# ") or lines[2] != by_id[key]["url"]:
                        errors.append(f"Invalid export header: {folder.name}/{key}")
                    if "\n".join(lines[4:]).rstrip("\n") != transcript(folder, key):
                        errors.append(f"Raw differs from export: {folder.name}/{key}")
        raw_ids = {p.stem for p in (folder / "raw").glob("*.md") if p.name != "index.md"}
        if raw_ids != set(imported):
            errors.append(f"Raw/manifest mismatch: {folder.name}")
        source_ids = {p.stem for p in (folder / "sources").glob("*.md") if p.name != "index.md"}
        for key in source_ids:
            if key not in imported or not (folder / "scripts/extractions" / f"{key}.json").exists():
                errors.append(f"Source lacks transcript/extraction: {folder.name}/{key}")
            else:
                item = json.loads((folder / "scripts/extractions" / f"{key}.json").read_text())
                if not item.get('insights') or not item.get('summary') or not item.get('thesis'):
                    errors.append(f"Source extraction is empty: {folder.name}/{key}")
                for insight in item["insights"]:
                    slug = re.sub(r"[^a-z0-9]+", "-", insight["slug"].lower()).strip("-")
                    match = locate_quote(transcript(folder, key), insight["quote"])
                    if match:
                        evidence_id = hashlib.sha256(match[0].encode()).hexdigest()[:10]
                        expected_ids.add(f"{folder.name}:{key}:{slug}:{evidence_id}")
                    else:
                        errors.append(f"Unmatched extraction quote: {folder.name}/{key}")
        counts["catalog"] += len(by_id)
        counts["transcripts"] += len(imported)
        counts["sources"] += len(source_ids)
        if require_complete and (not selected.issubset(imported) or not selected.issubset(source_ids)):
            errors.append(f"Selected scope incomplete: {folder.name}")
        if require_full_archive and (set(by_id) != set(imported) or set(by_id) != source_ids):
            errors.append(f"Archive incomplete: {folder.name}")
        review_path = folder / "review.json"
        review = json.loads(review_path.read_text()) if review_path.exists() else {}
        for relative, expected_hash in review.get('artifacts', {}).items():
            artifact = folder / relative
            if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected_hash:
                errors.append(f"Reviewed artifact changed or missing: {folder.name}/{relative}")
        if (require_complete or require_full_archive) and not all(review.get(k) is True for k in ("cross_video_synthesis_complete", "entity_synthesis_complete")):
            errors.append(f"Reviewed synthesis incomplete: {folder.name}")
    dataset_path = root / "analysis/insights.jsonl"
    seen = set()
    if dataset_path.exists():
        for line in dataset_path.read_text().splitlines():
            item = json.loads(line)
            if item["id"] in seen:
                errors.append(f"Duplicate insight ID: {item['id']}")
            seen.add(item["id"])
            folder = creators / item["creator_slug"]
            text = transcript(folder, item["youtube_id"])
            if text[item["character_start"]:item["character_end"]] != item["quote"]:
                errors.append(f"Quote/offset mismatch: {item['id']}")
            if item["timestamp_seconds"] is not None and item["provider"] == "notebooklm":
                errors.append(f"Fabricated timestamp: {item['id']}")
            if hashlib.sha256((folder / "raw" / f"{item['youtube_id']}.md").read_bytes()).hexdigest() != item["raw_sha256"]:
                errors.append(f"Insight references changed transcript: {item['id']}")
            counts["insights"] += 1
    if seen != expected_ids:
        errors.append("Insight dataset and published source extractions differ")
    entities_path = root / 'analysis/entities.jsonl'
    if entities_path.exists():
        for line in entities_path.read_text().splitlines():
            item = json.loads(line)
            folder = creators / item['creator_slug']
            text = transcript(folder, item['youtube_id'])
            if text[item['character_start']:item['character_end']] != item['quote']:
                errors.append(f"Entity context/offset mismatch: {item['entity']}/{item['youtube_id']}")
            if text[item['name_start']:item['name_end']] != item['matched_name']:
                errors.append(f"Entity name/offset mismatch: {item['entity']}/{item['youtube_id']}")
            raw = folder / 'raw' / f"{item['youtube_id']}.md"
            if hashlib.sha256(raw.read_bytes()).hexdigest() != item['raw_sha256']:
                errors.append(f"Entity references changed transcript: {item['entity']}/{item['youtube_id']}")
    pages = list(root.rglob("*.md"))
    if root == ROOT:
        for config in peer_glob("*/channel.json"):
            pages.extend(config.parent.rglob("*.md"))
    for path in pages:
        if "exports" in path.parts:
            continue
        text = path.read_text()
        if not text.startswith("---\n") or not re.search(r"^type:\s*\S", text.split("\n---", 1)[0], re.M):
            errors.append(f"Missing frontmatter type: {path}")
        # Transcript content is immutable source data, not authored navigation.
        if "raw" in path.parts and path.name != "index.md":
            continue
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not (path.parent / link.split("#", 1)[0]).exists():
                errors.append(f"Broken link {link}: {path}")
    coverage_path = root / "coverage.json"
    if coverage_path.exists():
        coverage = json.loads(coverage_path.read_text())
        if coverage.get("extraction_issues"):
            errors.append("Renderer reported unmatched extraction evidence")
        for key, metric in [("catalog", "catalog"), ("transcripts", "transcripts"), ("sources", "sources")]:
            if sum(row[metric] for row in coverage["creators"]) != counts[key]:
                errors.append(f"Coverage report is stale: {key}")
        if coverage["validated_insights"] != counts["insights"]:
            errors.append("Coverage insight count is stale")
        for row in coverage['creators']:
            folder = creators / row['slug']
            selection_path = folder / 'selection.json'
            if not selection_path.exists():
                continue
            selected = set(json.loads(selection_path.read_text())['videos'])
            imported = {v['youtube_id'] for v in json.loads((folder / 'raw/manifest.json').read_text())['videos']}
            sources = {p.stem for p in (folder / 'sources').glob('*.md') if p.name != 'index.md'}
            for name, actual in [('selected', len(selected)), ('selected_transcripts', len(selected & imported)), ('selected_sources', len(selected & sources))]:
                if row.get(name) != actual:
                    errors.append(f"Selected coverage report is stale: {row['slug']}/{name}")
        selection_path = root / 'selection.json'
        if selection_path.exists():
            selection = json.loads(selection_path.read_text())
            if sum(row['selected'] for row in coverage['creators']) != selection['total_selected']:
                errors.append('Selected collection count differs from confirmed scope')
    print(f"Catalog {counts['catalog']}; transcripts {counts['transcripts']}; source notes {counts['sources']}; exact-quote insights {counts['insights']}.")
    print("Integrity checks do not certify scope completion, factual accuracy or reviewed synthesis.")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--require-full-archive", action="store_true")
    args = parser.parse_args()
    issues = validate(require_complete=args.require_complete, require_full_archive=args.require_full_archive)
    for issue in issues:
        print("ERROR:", issue)
    raise SystemExit(bool(issues))
