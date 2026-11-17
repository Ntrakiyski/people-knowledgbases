#!/usr/bin/env python3
"""Preserve automatic NotebookLM source guides for remaining source-note work."""
from layout import peer_glob
import json
import time

from import_notebooklm import ROOT, cli, save


def main():
    tasks = []
    for path in peer_glob('*/raw/manifest.json'):
        folder = path.parents[1]
        for record in json.loads(path.read_text())['videos']:
            key = record['youtube_id']
            target = folder / 'exports/source-guides' / f'{key}.json'
            if (folder / 'scripts/extractions' / f'{key}.json').exists() or target.exists():
                continue
            tasks.append((folder, record, target))
    # Short sources first; complete creator batches remain newest-first.
    order = {'nick-huber': 0, 'sahil-bloom': 1, 'alex-hormozi': 2, 'codie-sanchez': 3, 'dan-martell': 4}
    tasks.sort(key=lambda t: (order[t[0].name], t[1]['recency_rank']))
    for folder, record, target in tasks:
        try:
            data = cli('source', 'guide', record['source_id'], '--notebook', record['notebook_id'], timeout=90)
            if not data.get('summary'):
                raise ValueError('No source guide summary')
            target.parent.mkdir(parents=True, exist_ok=True)
            save(target, data)
            print(f"Saved {folder.name}/{record['youtube_id']}", flush=True)
        except Exception as error:
            print(f"Guide unavailable: {folder.name}/{record['youtube_id']} ({type(error).__name__})", flush=True)
        time.sleep(2)


if __name__ == '__main__':
    main()
