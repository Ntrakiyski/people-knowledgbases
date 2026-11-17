#!/usr/bin/env python3
"""Publish reviewed synthesis bodies with manifest-owned metadata and citations."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBTYPES = {"tool": "tools", "person": "people", "organization": "organizations"}


def location(page: dict) -> Path:
    if "subtype" in page:
        return Path("entities") / SUBTYPES[page["subtype"]] / f"{page['slug']}.md"
    return Path("concepts") / f"{page['slug']}.md"


def main() -> None:
    import os
    manifest = json.loads((ROOT / "scripts/manifest.json").read_text())
    pages = manifest["concepts"] + manifest["entities"]
    by_slug = {page["slug"]: page for page in pages}
    today = datetime.now(timezone.utc).date().isoformat()
    for page in pages:
        path = location(page)
        body_path = (ROOT / "scripts/pages" / path).with_suffix(".txt")
        if not body_path.exists():
            raise ValueError(f"Reviewed body is missing: {body_path}")
        body = body_path.read_text().strip()
        if not body:
            raise ValueError(f"Reviewed body is empty: {body_path}")
        metadata = {"type": "entity" if "subtype" in page else "concept", "title": page["title"],
                    "description": page["description"], "tags": page["tags"],
                    "videos": [video["slug"] for video in page["videos"]],
                    "created": today, "updated": today}
        if "subtype" in page:
            metadata.update({"subtype": page["subtype"], "resource": page.get("resource", "")})
        lines = ["---"] + [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()]
        lines += ["---", "", f"# {page['title']}", ""]
        first_video = page["videos"][0]
        first_quote = first_video["quotes"][0]
        rel_source = os.path.relpath(ROOT / "sources" / f"{first_video['slug']}.md", (ROOT / path).parent)
        lines += [f"> {first_quote['text']}", "",
                  f"[{first_video['title']}]({rel_source}), {first_quote['ts']}.", "", body, ""]
        if page["related"]:
            lines += ["## Related", ""]
            for slug in sorted(page["related"]):
                other = by_slug[slug]
                link = os.path.relpath(ROOT / location(other), (ROOT / path).parent)
                lines.append(f"- [{other['title']}]({link}): {other['description']}")
            lines.append("")
        lines += ["## Sources", ""]
        for video in page["videos"]:
            link = os.path.relpath(ROOT / "sources" / f"{video['slug']}.md", (ROOT / path).parent)
            for quote in video["quotes"]:
                lines.append(f'- [{video["title"]}]({link}) - "[{quote["ts"]}] {quote["text"]}"')
        lines.append("")
        (ROOT / path).write_text("\n".join(lines))
    print(f"Published {len(pages)} concept and entity pages.")


if __name__ == "__main__":
    main()
