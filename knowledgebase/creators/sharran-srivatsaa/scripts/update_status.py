#!/usr/bin/env python3
"""Regenerate the root navigation, catalog listing, and honest coverage report."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text())
    manifest = json.loads((ROOT / "raw" / "manifest.json").read_text())
    videos = catalog["videos"]
    raw = {p.stem for p in (ROOT / "raw").glob("*.md") if p.name != "index.md"}
    sources = {p.stem for p in (ROOT / "sources").glob("*.md") if p.name != "index.md"}
    concepts = len([p for p in (ROOT / "concepts").glob("*.md") if p.name != "index.md"])
    entities = len([p for p in (ROOT / "entities").rglob("*.md") if p.name != "index.md"])
    imported = sum(video["slug"] in raw for video in videos)
    summarized = sum(video["slug"] in sources for video in videos)
    total = len(videos)
    today = datetime.now(timezone.utc).date().isoformat()
    complete = imported == summarized == total and concepts > 0
    frozen_path = ROOT / "scripts/manifest.json"
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text())
        subtypes = {"tool": "tools", "person": "people", "organization": "organizations"}
        expected = [ROOT / "concepts" / f"{page['slug']}.md" for page in frozen["concepts"]]
        expected += [ROOT / "entities" / subtypes[page["subtype"]] / f"{page['slug']}.md"
                     for page in frozen["entities"]]
        complete = complete and all(path.exists() for path in expected)
    state = "Imported and synthesized" if complete else "Incomplete"
    failures = {row["youtube_id"]: row["reason"] for row in manifest.get("failed_videos", [])}
    header = f"""---
type: overview
title: "Build status"
description: "Measured catalog, transcript, and synthesis coverage."
updated: {today}
---

# Build status

{state}. Catalog enumeration ran at {catalog['enumerated_at']}.

- Videos discovered: {total}.
- Transcripts imported: {imported}.
- Video summaries written: {summarized}.
- Concept pages: {concepts}.
- Entity pages: {entities}.

Scope: {catalog['scope']}

Unknown publication dates remain empty. A catalog title is metadata, not evidence
for a video's teachings. Only imported transcripts can support knowledge pages.

## Remaining work

"""
    remaining = []
    for video in videos:
        if video["slug"] not in raw:
            reason = failures.get(video["youtube_id"], "Not attempted")
            remaining.append(f"- `{video['youtube_id']}`: transcript pending. {reason}.")
        elif video["slug"] not in sources:
            remaining.append(f"- `{video['youtube_id']}`: transcript imported; synthesis pending.")
    if imported == summarized == total and not complete:
        remaining.append("- Canonical synthesis pages remain pending.")
    (ROOT / "status.md").write_text(header + "\n".join(remaining or ["No catalog videos or canonical pages remain pending."]) + "\n")
    rows = ["---", "type: overview", 'title: "Video catalog"',
            'description: "Public upload metadata and per-video ingestion status."', "---", "",
            "# Video catalog", "", f"{total} videos in the channel's Videos tab. "
            "These titles are metadata, not synthesized knowledge.", "",
            "| Video | Duration | Status |", "| --- | --- | --- |"]
    for video in videos:
        seconds = int(video.get("duration_seconds") or 0)
        title = video["title"].replace("|", "&#124;").replace("[", "(").replace("]", ")")
        slug = video["slug"]
        status = (f"[Summary](sources/{slug}.md)" if slug in sources else
                  f"[Transcript](raw/{slug}.md), synthesis pending" if slug in raw else "Transcript pending")
        rows.append(f"| [{title}]({video['url']}) | {seconds // 60}:{seconds % 60:02} | {status} |")
    (ROOT / "catalog.md").write_text("\n".join(rows) + "\n")
    (ROOT / "index.md").write_text(f"""---
okf_version: "0.1"
title: "Sharran Srivatsaa knowledge base"
---

# Sharran Srivatsaa knowledge base

{state}: {imported}/{total} transcripts and {summarized}/{total} video summaries.
{concepts} concept pages and {entities} entity pages.

Read [build status](status.md) before answering questions. Pending videos cannot
support answers. The [video catalog](catalog.md) lists every discovered upload.

## Knowledge

- [Concepts](concepts/index.md): ideas synthesized from transcripts.
- [Entities](entities/index.md): people, organizations, tools, and products.
- [Sources](sources/index.md): video summaries and key moments.
- [Raw transcripts](raw/index.md): immutable evidence with timestamps.

## Creator research

- [Creator profile](creator-profile.md): Sharran’s themes, audience, teaching style, and evidence.
- [Similar creators](similar-creators.md): five matches with YouTube and X accounts.
- [Expanded creator collection](../../operations/peer-collection/index.md): transcripts and source notes for the five recommended creators.

## Project

- [README](README.md): project overview and commands.
- [Schema](SCHEMA.md): page contracts and citation rules.
- [Import guide](docs/ingestion-workflow.md): fetch and synthesize missing videos.
- [Query guide](docs/query-guide.md): answer questions with citations.
- [Provenance](docs/provenance.md): upstream repository and channel scope.
- [History](log.md): build events.
""")
    frozen_path = ROOT / "scripts/manifest.json"
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text())
        taxonomy = json.loads((ROOT / "scripts/taxonomy.json").read_text())
        pages = {page["slug"]: page for page in frozen["concepts"]}
        lines = ["", "## Browse by topic", ""]
        for theme, slugs in taxonomy.get("concept_themes", []):
            lines += [f"### {theme}", ""]
            # Start with the concepts supported by the most videos.
            ordered = sorted(slugs, key=lambda slug: (-len(pages[slug]["videos"]), slug))
            for slug in ordered[:5]:
                page = pages[slug]
                if (ROOT / "concepts" / f"{slug}.md").exists():
                    lines.append(f"- [{page['title']}](concepts/{slug}.md): {page['description']}")
            lines.append("")
        with (ROOT / "index.md").open("a") as output:
            output.write("\n".join(lines))
    print(f"Coverage: {imported}/{total} transcripts, {summarized}/{total} summaries; {state.lower()}.")


if __name__ == "__main__":
    main()
