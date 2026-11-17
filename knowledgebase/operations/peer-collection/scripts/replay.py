#!/usr/bin/env python3
"""Recover fully valid per-video drafts from cached multi-source responses."""
from layout import peer_glob
import json

from extract import parse_answer
from render import ROOT, locate_quote, transcript


def main():
    inventory = {}
    for path in peer_glob('*/raw/manifest.json'):
        for record in json.loads(path.read_text())['videos']:
            inventory[record['youtube_id']] = (path.parents[1], record)
    saved = 0
    for path in sorted((ROOT / 'extraction-responses').glob('*.json')):
        if path.name.endswith('.error.json'):
            continue
        try:
            data = parse_answer(json.loads(path.read_text())['answer'])
        except (ValueError, KeyError):
            continue
        for item in data.get('videos', []):
            key = item.get('youtube_id')
            if key not in inventory:
                continue
            folder, record = inventory[key]
            target = folder / 'scripts/extractions' / f'{key}.json'
            if target.exists() or not all(item.get(k) for k in ('summary', 'thesis', 'insights')):
                continue
            text = transcript(folder, key)
            valid = True
            for insight in item['insights']:
                if not all(insight.get(k) for k in ('slug', 'title', 'explanation', 'quote', 'tags')):
                    valid = False
                    break
                match = locate_quote(text, insight['quote'])
                if not match:
                    valid = False
                    break
                insight['quote'], insight['character_start'], insight['character_end'] = match
            if not valid:
                continue
            item.update({'review_status': 'machine-extracted', 'notebook_id': record['notebook_id'],
                         'source_id': record['source_id'], 'extraction_response': str(path.relative_to(ROOT))})
            target.write_text(json.dumps(item, ensure_ascii=False, indent=2) + '\n')
            saved += 1
    print(f'Recovered {saved} fully quote-checked per-video drafts.')


if __name__ == '__main__':
    main()
