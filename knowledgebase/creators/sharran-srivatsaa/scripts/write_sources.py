#!/usr/bin/env python3
"""Render video source pages from the reviewed summaries in the frozen manifest."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def seconds(timestamp: str) -> int:
    hour, minute, second = map(int, timestamp.split(":"))
    return hour * 3600 + minute * 60 + second


def main() -> None:
    manifest = json.loads((ROOT / "scripts/manifest.json").read_text())
    concepts = {page["slug"]: page for page in manifest["concepts"]}
    entities = {page["slug"]: page for page in manifest["entities"]}
    today = datetime.now(timezone.utc).date().isoformat()
    subtypes = {"tool": "tools", "person": "people", "organization": "organizations"}
    for source in manifest["sources"]:
        duration_seconds = int(source.get("duration_seconds") or 0)
        duration = f"{duration_seconds // 3600}:{duration_seconds % 3600 // 60:02}:{duration_seconds % 60:02}"
        metadata = {"type": "source", "title": source["title"], "description": source["thesis"],
                    "youtube_id": source["youtube_id"], "url": source["url"], "slug": source["slug"],
                    "published": source.get("published", ""), "duration": duration,
                    "recency_rank": source["recency_rank"], "raw": f"../raw/{source['slug']}.md",
                    "tags": source["tags"], "created": today, "updated": today}
        lines = ["---"] + [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()]
        lines += ["---", "", f"# {source['title']}", "", source["summary"], "", "## Concepts covered", ""]
        for slug in source["concepts"]:
            page = concepts[slug]
            lines.append(f"- [{page['title']}](../concepts/{slug}.md): {page['description']}")
        if not source["concepts"]:
            lines.append("This upload does not teach a standalone concept in the canonical taxonomy.")
        lines += ["", "## Entities", ""]
        for slug in source["entities"]:
            page = entities[slug]
            directory = subtypes[page["subtype"]]
            lines.append(f"- [{page['title']}](../entities/{directory}/{slug}.md): {page['description']}")
        if not source["entities"]:
            lines.append("No named entity receives substantive treatment in this upload.")
        lines += ["", "## Key moments", ""]
        for moment in source["key_moments"]:
            lines.append(f"- [{moment['ts']}]({source['url']}&t={seconds(moment['ts'])}s): {moment['note']}")
        lines += ["", "## Transcript", "",
                  f"Read the [timestamped raw transcript](../raw/{source['slug']}.md).", ""]
        (ROOT / "sources" / f"{source['slug']}.md").write_text("\n".join(lines))
    print(f"Wrote {len(manifest['sources'])} video source pages.")


if __name__ == "__main__":
    main()
