#!/usr/bin/env python3
"""Render evidence-backed Markdown and a portable insight dataset from checkpoints."""
from __future__ import annotations

import hashlib
import csv
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from entities import build_entities

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now(timezone.utc).date().isoformat()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def write_page(path: Path, kind: str, title: str, body: str, **metadata: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = {"type": kind, "title": title, **metadata}
    text = "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()) + "\n---\n\n" + body.rstrip() + "\n"
    path.write_text(text)


def label(value: str) -> str:
    return value.replace("[", "(").replace("]", ")").replace("|", "&#124;").replace("\n", " ")


def transcript(folder: Path, video_id: str) -> str:
    raw = (folder / "raw" / f"{video_id}.md").read_text()
    return raw.split("\n## Transcript\n\n", 1)[1].rstrip("\n")


def locate_quote(text: str, quote: str) -> tuple[str, int, int] | None:
    """Match case and whitespace variants, then restore exact source characters."""
    quote = quote.strip()
    if len(quote.split()) < 6:
        return None
    # Do not silently strip punctuation or invent an approximate quote.
    pattern = r"\s+".join(re.escape(word) for word in quote.split())
    match = re.search(pattern, text, re.I)
    if not match:
        return None
    return text[match.start():match.end()], match.start(), match.end()


def review_scope(extraction: dict) -> str:
    method = extraction.get('synthesis_method', '')
    status = extraction.get('review_status', '')
    if 'selected original transcript passages' in method:
        return 'selected-passages'
    if 'complete local transcript' in method or 'complete transcript' in status:
        return 'complete-transcript-read-by-Codex'
    return 'NotebookLM-source-restricted-draft'


def main() -> None:
    dataset, creator_rows, all_topics = [], [], defaultdict(list)
    video_rows = []
    video_reviews = []
    entity_records = []
    failures = []
    for channel_path in sorted(ROOT.glob("*/channel.json")):
        folder = channel_path.parent
        config, catalog = load(channel_path), load(folder / "catalog.json")
        manifest = load(folder / "raw/manifest.json")
        selected = set(load(folder / "selection.json")["videos"])
        imported = {v["youtube_id"]: v for v in manifest["videos"]}
        videos = {v["youtube_id"]: v for v in catalog["videos"]}
        entity_by_video, mentions = build_entities(folder, config, imported, videos, write_page, transcript)
        entity_records.extend(mentions)
        source_links, concepts, source_count = [], defaultdict(list), 0
        for extraction_path in sorted((folder / "scripts/extractions").glob("*.json")):
            extraction = load(extraction_path)
            video_id = extraction["youtube_id"]
            if video_id not in imported or video_id not in videos:
                failures.append(f"Unknown extraction {config['slug']}/{video_id}")
                continue
            raw_path = folder / "raw" / f"{video_id}.md"
            if hashlib.sha256(raw_path.read_bytes()).hexdigest() != imported[video_id]["sha256"]:
                failures.append(f"Transcript hash changed: {config['slug']}/{video_id}")
                continue
            text = transcript(folder, video_id)
            video = videos[video_id]
            valid = []
            for item in extraction.get("insights", []):
                match = locate_quote(text, item.get("quote", ""))
                if not match:
                    failures.append(f"Unmatched quote: {config['slug']}/{video_id}/{item.get('title')}")
                    continue
                exact, start, end = match
                slug = re.sub(r"[^a-z0-9]+", "-", item["slug"].lower()).strip("-")
                evidence_id = hashlib.sha256(exact.encode()).hexdigest()[:10]
                # Channel association alone cannot establish who said a quote.
                speaker = item.get("speaker", "unresolved")
                record = {"id": f"{config['slug']}:{video_id}:{slug}:{evidence_id}", "creator": config["name"], "channel_creator": config["name"], "attributed_speaker": speaker, "speaker_attribution_status": "machine-suggested; review pending" if speaker != "unresolved" else "unresolved", "creator_slug": config["slug"], "youtube_id": video_id, "video_title": video["title"], "video_url": video["url"], "concept_slug": slug, "title": item["title"], "explanation": item["explanation"], "quote": exact, "character_start": start, "character_end": end, "timestamp_seconds": None, "tags": item.get("tags", []), "provider": imported[video_id].get("provider"), "notebook_id": imported[video_id].get("notebook_id"), "source_id": imported[video_id].get("source_id"), "raw_sha256": imported[video_id]["sha256"], "synthesis_method": extraction.get("synthesis_method", "NotebookLM source-restricted extraction; exact quotation checked locally"), "review_status": extraction.get("review_status", "machine-extracted"), "review_scope": review_scope(extraction)}
                dataset.append(record)
                concepts[slug].append(record)
                valid.append(record)
                for tag in record["tags"]:
                    all_topics[tag].append(record)
            if not valid:
                continue
            source_count += 1
            video_reviews.append({
                'creator_slug': config['slug'], 'youtube_id': video_id,
                'title': video['title'], 'url': video['url'],
                'review_scope': review_scope(extraction),
                'thesis': extraction['thesis'], 'summary': extraction['summary'],
                'context_and_limits': extraction.get('context_and_limits'),
                'review_changes': extraction.get('review_changes'),
                'previous_draft': extraction.get('previous_draft'),
                'previous_draft_sha256': extraction.get('previous_draft_sha256'),
                'raw_sha256': imported[video_id]['sha256'],
                'independent_factual_verification': False,
            })
            body = [f"# {video['title']}", "", "This page describes the selected source's claims and advice. The summary and interpretations are machine-extracted drafts; quotations have been matched against the exported transcript.", "", "Review scope: " + extraction.get("review_status", "machine-extracted draft; full-transcript editorial review not established") + ".", "", "Method: " + extraction.get("synthesis_method", "NotebookLM source-restricted extraction; exact quotations checked locally") + ".", "", extraction["summary"], "", "## Insights", ""]
            for item in valid:
                body += [f"### {item['title']}", "", item["explanation"], "", f"> {item['quote']}", "", f"Speaker attribution: {item['attributed_speaker']} ({item['speaker_attribution_status']}).", "", f"Evidence: [raw transcript](../raw/{video_id}.md), characters {item['character_start']}–{item['character_end']} (end exclusive).", ""]
            if extraction.get('context_and_limits'):
                body += ["## Context and limits", "", extraction['context_and_limits'], ""]
            if extraction.get('review_changes'):
                body += ["## What the complete reading adds", "", extraction['review_changes'], ""]
            body += ["## Concepts covered", ""] + [f"- [{label(item['title'])}](../concepts/{item['concept_slug']}.md)." for item in valid]
            body += ["", "## Entities", "", "Literal name mentions from the disclosed registry; identity and endorsement are not inferred.", ""]
            body += [f'- [{name}]({link}).' for name, link in entity_by_video[video_id]] or ['No registered names matched; this does not establish absence of other named subjects.']
            body += ["", "## Key moments", "", "NotebookLM exported no timestamps. Exact quotations and character offsets locate evidence; no timecodes have been inferred.", "", "## Transcript", "", f"Read the [raw transcript](../raw/{video_id}.md) or watch the [source video]({video['url']})."]
            write_page(folder / "sources" / f"{video_id}.md", "source", video["title"], "\n".join(body), youtube_id=video_id, url=video["url"], raw=f"../raw/{video_id}.md", synthesis_status="machine-extracted; quotations checked", timestamped=False)
            source_links.append(f"- [{label(video['title'])}]({video_id}.md): {extraction['thesis']}")
        concept_links = []
        for slug, records in sorted(concepts.items()):
            title = records[0]["title"]
            body = [f"# {title}", "", "These source notes collect the treatments found so far. They preserve differences between videos; a reviewed cross-video synthesis is pending.", ""]
            for item in records:
                body += [f"## In {label(item['video_title'])}", "", item["explanation"], "", f"> {item['quote']}", "", f"[Source summary](../sources/{item['youtube_id']}.md); [raw transcript](../raw/{item['youtube_id']}.md), characters {item['character_start']}–{item['character_end']}.", ""]
            body += ["## Sources", ""] + [f"- [{label(item['video_title'])}](../sources/{item['youtube_id']}.md) — exact quotation above, characters {item['character_start']}–{item['character_end']}." for item in records]
            write_page(folder / "concepts" / f"{slug}.md", "concept", title, "\n".join(body), videos=list(dict.fromkeys(i["youtube_id"] for i in records)), synthesis_status="source-notes; cross-video review pending")
            concept_links.append(f"- [{label(title)}]({slug}.md): {len(records)} cited treatment(s).")
        write_page(folder / "sources/index.md", "overview", "Source notes", "# Source notes\n\n" + "\n".join(source_links or ["No extracted source notes yet."]))
        # Retired generated pages otherwise keep superseded interpretations searchable.
        for stale in (folder / 'concepts').glob('*.md'):
            if stale.stem != 'index' and stale.stem not in concepts:
                if 'These source notes collect the treatments found so far.' in stale.read_text():
                    stale.unlink()
        write_page(folder / "concepts/index.md", "overview", "Concepts", "# Concepts\n\n" + "\n".join(concept_links or ["Concept extraction is pending."]))
        raw_links = [f"- [{label(videos[key]['title'])}]({key}.md)." for key in imported]
        write_page(folder / "raw/index.md", "overview", "Raw transcripts", "# Raw transcripts\n\n" + "\n".join(raw_links or ["No transcripts imported yet."]))
        total, fetched = len(videos), len(imported)
        selected_count = len(selected)
        selected_fetched = len(selected.intersection(imported))
        selected_sources = sum((folder / "sources" / f"{key}.md").exists() for key in selected)
        rows = ["| Video | Scope | Transcript | Source notes |", "| --- | --- | --- | --- |"]
        for video in catalog["videos"]:
            key = video["youtube_id"]
            raw_link = f"[Imported](raw/{key}.md)" if key in imported else "Pending"
            source_link = f"[Extracted](sources/{key}.md)" if (folder / "sources" / f"{key}.md").exists() else "Pending"
            scope = 'Selected' if key in selected else 'Optional archive'
            rows.append(f"| [{label(video['title'])}]({video['url']}) | {scope} | {raw_link} | {source_link} |")
            if key in selected:
                extraction_file = folder / 'scripts/extractions' / f'{key}.json'
                extraction_meta = load(extraction_file) if extraction_file.exists() else {}
                video_rows.append({'creator': config['name'], 'creator_slug': config['slug'],
                                   'recency_rank': video['recency_rank'], 'youtube_id': key,
                                   'title': video['title'], 'url': video['url'],
                                   'transcript_saved': key in imported,
                                   'source_notes_saved': (folder / 'sources' / f'{key}.md').exists(),
                                   'note_review_scope': review_scope(extraction_meta) if extraction_meta else 'pending',
                                   'insight_count': len(extraction_meta.get('insights', [])),
                                   'transcript_words': len(transcript(folder, key).split()) if key in imported else 0,
                                   'raw_sha256': imported.get(key, {}).get('sha256', '')})
        write_page(folder / "catalog.md", "overview", f"{config['name']} catalog", "# Video catalog\n\nAll public Videos-tab uploads discovered on 2026-11-16. Titles are metadata, not evidence for teachings.\n\n" + "\n".join(rows))
        status = f"# Build status\n\nSelected scope: newest {selected_count} public Videos-tab uploads. Imported: {selected_fetched}/{selected_count}. Source notes: {selected_sources}/{selected_count}. Concept evidence pages: {len(concepts)}.\n\nFull archive: {total} catalog entries retained for optional later expansion. Shorts and Streams are excluded. Missing or failed videos are never silently counted as covered.\n\nNotebookLM transcripts have exact text but no timestamps. All selected transcripts are saved locally. The account held at most 100 task sources at a time; authorized recycling preserved verified local evidence and an audit trail.\n\nExplanations are machine-extracted drafts. Exact quotation checks verify wording, not the truth or interpretation of a claim. See the creator profile for scoped cross-video synthesis and the named-mention guide for entity context. Source notes retain their individual review scope; none certify independent factual verification."
        source_scopes = Counter(row['note_review_scope'] for row in video_rows if row['creator_slug'] == config['slug'])
        status += '\n\nSource review scopes: ' + '; '.join(f'{name}: {count}' for name, count in sorted(source_scopes.items())) + '. See the [deeper-review tracker](../analysis/deep-review/progress.md) for completed and pending full readings.'
        write_page(folder / "status.md", "overview", "Build status", status, updated=TODAY)
        write_page(folder / "index.md", "overview", f"{config['name']} knowledge base", f"# {config['name']} knowledge base\n\nNewest-{selected_count} scope: {selected_fetched}/{selected_count} transcripts and {selected_sources}/{selected_count} source notes. Full archive: {total} catalog entries.\n\n- [Build status](status.md).\n- [Creator profile](creator-profile.md).\n- [Full catalog](catalog.md).\n- [Source notes](sources/index.md).\n- [Concepts](concepts/index.md).\n- [Raw transcripts](raw/index.md).\n- [Named mentions and context](entities/index.md).\n- [Shared collection](../index.md).")
        tags = Counter(tag for records in concepts.values() for record in records for tag in record["tags"])
        profile = [f"# Creator profile: {config['name']}", "", f"[YouTube]({config['url']}) · [X/Twitter]({config['x_url']})", "", f"This evolving channel-content profile is based on {selected_sources} extracted videos within the selected newest {selected_count}; the full catalog has {total} videos. Guest statements do not establish the channel owner's beliefs. Audience, personal attribution, and positioning need review after broader coverage. X posts have not been imported.", "", "## Themes in the imported evidence", ""]
        for tag, _ in tags.most_common(8):
            relevant = [record for records in concepts.values() for record in records if tag in record["tags"]]
            selected = list({item["concept_slug"]: item for item in relevant}.values())[:4]
            profile += [f"### {tag.replace('-', ' ').capitalize()}", ""]
            profile += [f"- [{label(item['title'])}](concepts/{item['concept_slug']}.md): {item['explanation']}" for item in selected]
            profile.append("")
        if not tags:
            profile += ["Transcript-grounded profile synthesis is pending.", ""]
        editorial_path = folder / 'profile-notes.md'
        if editorial_path.exists():
            editorial = editorial_path.read_text().split('\n---\n', 1)[1].strip()
            profile = profile[:6] + ['', editorial, '']
        profile += ["## Coverage and interpretation", "", "These are attributed source notes, not an independently verified biography or investment track record. The current batch is newest-first and may overrepresent recent topics. Refer to [build status](status.md) before generalizing to the full channel."]
        write_page(folder / "creator-profile.md", "overview", f"Creator profile: {config['name']}", "\n".join(profile), updated=TODAY)
        creator_rows.append({"slug": config["slug"], "name": config["name"], "catalog": total, "selected": selected_count, "selected_transcripts": selected_fetched, "selected_sources": selected_sources, "transcripts": fetched, "sources": source_count, "concepts": len(concepts)})
    (ROOT / "analysis").mkdir(exist_ok=True)
    csv_buffer = io.StringIO(newline='')
    if video_rows:
        csv_writer = csv.DictWriter(csv_buffer, fieldnames=list(video_rows[0]))
        csv_writer.writeheader()
        csv_writer.writerows(video_rows)
    (ROOT / 'analysis/videos.csv').write_text(csv_buffer.getvalue())
    (ROOT / 'analysis/video-reviews.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in video_reviews))
    (ROOT / 'analysis/entities.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in entity_records))
    (ROOT / "analysis/insights.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in dataset))
    complete = all(row["selected_transcripts"] == row["selected"] and row["selected_sources"] == row["selected"] and all(load(ROOT / row["slug"] / "review.json").get(k) is True for k in ("cross_video_synthesis_complete", "entity_synthesis_complete")) for row in creator_rows)
    deeper_review = None
    deeper_plan = ROOT / 'analysis/deep-review/plan.json'
    if deeper_plan.exists():
        targets = {(row['creator_slug'], row['youtube_id']) for row in load(deeper_plan)['videos']}
        done = sum((row['creator_slug'], row['youtube_id']) in targets and row['note_review_scope'] == 'complete-transcript-read-by-Codex' for row in video_rows)
        deeper_review = dict(target=len(targets), completed=done, remaining=len(targets) - done,
                             status='complete' if done == len(targets) else 'in-progress')
    (ROOT / "coverage.json").write_text(json.dumps({"updated": TODAY, "status": "selected-scope-complete; source notes remain editorial drafts" if complete else "incomplete", "creators": creator_rows, "source_review_scopes": dict(Counter(row['note_review_scope'] for row in video_rows)), "deeper_review": deeper_review, "validated_insights": len(dataset), "extraction_issues": failures}, indent=2) + "\n")
    write_page(ROOT / "index.md", "overview", "Creator knowledge bases", "# Creator knowledge bases\n\nFive separate, transcript-grounded collections for later analysis. Selected scope: newest 40 public Videos-tab uploads per creator, 200 total. All 200 selected transcripts and draft source notes are saved. Profiles and contextual guides synthesize the sampled evidence; individual notes disclose their review scope. The 99-source deeper pass is tracked separately below; its completion does not give the 64 NotebookLM drafts complete-transcript review. Full archives are cataloged for optional expansion.\n\n" + "\n".join(f"- [{row['name']}]({row['slug']}/index.md): {row['selected_transcripts']}/{row['selected']} selected transcripts; {row['selected_sources']}/{row['selected']} source notes; {row['catalog']} archive entries." for row in creator_rows) + "\n\n- [Deeper analysis findings](analysis/deeper-analysis.md) and [full-reading progress](analysis/deep-review/progress.md).\n- [Shared topic index](analysis/topics.md).\n- [Comparison and open questions](analysis/comparison.md).\n- [Analysis guide](analysis/README.md).\n- [Structured insights](analysis/insights.jsonl).\n- [Schema and provenance](SCHEMA.md).\n- [Original Sharran knowledge base](../sharran-knowledge-base/index.md).")
    topic_body = ["# Shared topic index", "", "Tags group related evidence for exploration. Sharing a tag does not establish that creators agree or discuss identical concepts.", ""]
    for tag, records in sorted(all_topics.items()):
        topic_body += [f"## {tag.replace('-', ' ').capitalize()}", ""]
        unique = {(i["creator_slug"], i["concept_slug"]): i for i in records}
        topic_body += [f"- {item['creator']}: [{label(item['title'])}](../{item['creator_slug']}/concepts/{item['concept_slug']}.md)." for item in unique.values()]
        topic_body.append("")
    write_page(ROOT / "analysis/topics.md", "overview", "Shared topic index", "\n".join(topic_body))
    print(f"Rendered {len(dataset)} quote-checked insights across {len(creator_rows)} creators; {len(failures)} extraction issues.")


if __name__ == "__main__":
    main()
