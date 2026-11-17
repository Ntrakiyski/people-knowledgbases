#!/usr/bin/env python3
"""Save authored complete-transcript reviews and preserve the preceding draft."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from layout import CREATORS
from render import ROOT, locate_quote, transcript, review_scope


def apply(batch):
    prepared = []
    for row in json.loads(batch.read_text()):
        if isinstance(row, list):
            slug, key, thesis, summary, limits, changes, insights = row
            row = dict(creator_slug=slug, youtube_id=key, thesis=thesis,
                       summary=summary, context_and_limits=limits, review_changes=changes,
                       insights=[dict(slug=s, title=t, explanation=e, quote=q, tags=tags)
                                 for s, t, e, q, tags in insights])
        folder = CREATORS / row['creator_slug']
        key = row['youtube_id']
        dest = folder / 'scripts/extractions' / f'{key}.json'
        old = json.loads(dest.read_text())
        if review_scope(old) != 'selected-passages':
            raise ValueError(f'Not a selected-passage draft: {dest}')
        text = transcript(folder, key)
        for item in row['insights']:
            match = locate_quote(text, item['quote'])
            if not match:
                raise ValueError(f"Quote not found: {key}: {item['quote']}")
            item['quote'], item['character_start'], item['character_end'] = match
            item.setdefault('speaker', 'unresolved')
        data = {**old, **{k: v for k, v in row.items() if k != 'creator_slug'},
                'review_status': 'Codex editorial draft; complete local transcript read; claims not independently verified',
                'synthesis_method': 'Direct Codex extraction from complete local transcript; exact quotations verified locally',
                'deep_review_date': datetime.now(timezone.utc).isoformat()}
        archive = ROOT / 'analysis/deep-review/previous' / folder.name / dest.name
        if archive.exists():
            raise ValueError(f'Previous draft already archived: {archive}')
        prepared.append((dest, archive, data))
    for dest, archive, data in prepared:
        archive.parent.mkdir(parents=True, exist_ok=True)
        previous = dest.read_bytes()
        archive.write_bytes(previous)
        data['previous_draft'] = str(archive.relative_to(ROOT))
        data['previous_draft_sha256'] = hashlib.sha256(previous).hexdigest()
        dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f"Deepened {dest.parent.parent.parent.name}/{dest.stem}: {len(data['insights'])} insights")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    apply(parser.parse_args().batch)
