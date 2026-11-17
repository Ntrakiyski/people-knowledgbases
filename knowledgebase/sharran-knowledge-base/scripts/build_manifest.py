#!/usr/bin/env python3
"""Freeze canonical concepts and entities from the reviewed extraction checkpoints."""
import json
from collections import defaultdict
from pathlib import Path

from validate import PARAGRAPH, normalized

ROOT = Path(__file__).resolve().parent.parent


def build() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text())
    rules = json.loads((ROOT / "scripts/canonicalization.json").read_text())
    concepts, entities, sources = {}, {}, []
    for video in catalog["videos"]:
        extraction_path = ROOT / "scripts/extractions" / f"{video['slug']}.json"
        if not extraction_path.exists():
            raise ValueError(f"Extraction is missing: {video['slug']}")
        extraction = json.loads(extraction_path.read_text())
        if extraction["slug"] != video["slug"]:
            raise ValueError(f"Extraction path does not match slug: {extraction_path}")
        raw = (ROOT / "raw" / f"{video['slug']}.md").read_text()
        paragraphs = {ts: normalized(text) for ts, text in PARAGRAPH.findall(raw)}
        for candidate in extraction["concepts"] + extraction["entities"]:
            if not candidate.get("quotes"):
                raise ValueError(f"Candidate has no quotes: {video['slug']}/{candidate['slug']}")
            for quote in candidate["quotes"]:
                if not quote["text"].strip() or normalized(quote["text"]) not in paragraphs.get(quote["ts"], ""):
                    raise ValueError(f"Quote not found at {quote['ts']}: {video['slug']}/{candidate['slug']}")
        for moment in extraction["key_moments"]:
            if moment["ts"] not in paragraphs:
                raise ValueError(f"Key moment is not a paragraph anchor: {video['slug']}/{moment['ts']}")
        linked = {}
        for kind, group in (("concept", concepts), ("entity", entities)):
            plural = "concepts" if kind == "concept" else "entities"
            slugs = []
            for candidate in extraction[plural]:
                slug = rules[f"{kind}_aliases"].get(candidate["slug"], candidate["slug"])
                if slug in rules[f"excluded_{plural}"]:
                    continue
                if slug not in group:
                    group[slug] = {"slug": slug, "title": candidate["name"],
                                   "description": candidate["one_liner"], "tags": [],
                                   "related": [], "members": [], "videos": []}
                    if kind == "entity":
                        group[slug].update({"subtype": candidate["subtype"],
                                            "resource": candidate.get("resource", "")})
                page = group[slug]
                if candidate["slug"] not in page["members"]:
                    page["members"].append(candidate["slug"])
                page["tags"] = sorted(set(page["tags"] + candidate.get("tags", [])))
                page["related"] += candidate.get("related", [])
                evidence = next((item for item in page["videos"] if item["slug"] == video["slug"]), None)
                if evidence:
                    evidence["quotes"] += candidate["quotes"]
                    evidence["explanation"] += "\n\n" + candidate["name"] + ": " + candidate.get("explanation", "")
                else:
                    page["videos"].append({"slug": video["slug"], "title": video["title"],
                                           "url": video["url"], "quotes": candidate["quotes"],
                                           "explanation": candidate.get("explanation", ""),
                                           "one_liner": candidate["one_liner"]})
                slugs.append(slug)
            linked[plural] = sorted(set(slugs))
        sources.append({**video, **{key: extraction[key] for key in
                                   ("thesis", "summary", "tags", "key_moments")}, **linked})
    all_pages = {**concepts, **entities}
    if len(all_pages) != len(concepts) + len(entities):
        raise ValueError("A slug is shared between a concept and an entity")
    aliases = {**rules["concept_aliases"], **rules["entity_aliases"]}
    for slug, page in all_pages.items():
        page.update(rules.get("page_overrides", {}).get(slug, {}))
        for video in page["videos"]:
            unique = {(quote["ts"], quote["text"]): quote for quote in video["quotes"]}
            video["quotes"] = list(unique.values())
        page["related"] = sorted({aliases.get(item, item) for item in page["related"]}
                                  & (all_pages.keys() - {slug}))
        page["theme"] = rules["concept_themes"].get(slug, "Other")
    # Recover reciprocal topic links before writers start.
    for slug, page in all_pages.items():
        for other in page["related"]:
            if slug not in all_pages[other]["related"]:
                all_pages[other]["related"].append(slug)
    manifest = {"concepts": list(concepts.values()), "entities": list(entities.values()),
                "sources": sources}
    (ROOT / "scripts/manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    themes, tools, clusters = defaultdict(list), defaultdict(list), defaultdict(list)
    for page in concepts.values():
        themes[page["theme"]].append(page["slug"])
    for page in entities.values():
        if page["subtype"] == "tool":
            tools["Products and services"].append(page["slug"])
    for source in sources:
        clusters[rules["source_themes"].get(source["slug"], "Videos")].append(source["slug"])
    taxonomy = {"concept_themes": list(themes.items()), "tool_themes": list(tools.items()),
                "source_clusters": list(clusters.items())}
    (ROOT / "scripts/taxonomy.json").write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2) + "\n")
    print(f"Frozen {len(concepts)} concepts, {len(entities)} entities, {len(sources)} sources.")


if __name__ == "__main__":
    build()
