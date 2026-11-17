#!/usr/bin/env python3
"""Recycle only locally preserved task sources, explicitly authorized 2026-11-16."""
import argparse
import hashlib
import json
from datetime import datetime, timezone

from import_notebooklm import ROOT, NOTEBOOKS, cli, save
from render import locate_quote, transcript


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    registry_path = ROOT / 'notebook-sources.json'
    registry = json.loads(registry_path.read_text())
    audit_path = ROOT / 'analysis/recycling-audit.json'
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else []
    already = {r['source_id'] for r in audit if r.get('removed')}
    candidates = []
    for manifest_path in sorted(ROOT.glob('*/raw/manifest.json')):
        folder = manifest_path.parents[1]
        for record in json.loads(manifest_path.read_text())['videos']:
            key = record['youtube_id']
            if record.get('notebook_id') not in NOTEBOOKS or record.get('source_id') in already:
                continue
            extraction = folder / 'scripts/extractions' / f'{key}.json'
            source = folder / 'sources' / f'{key}.md'
            if not extraction.exists() or not source.exists():
                continue
            raw = folder / 'raw' / f'{key}.md'
            exported = folder / 'exports/notebooklm' / f'{key}.md'
            assert hashlib.sha256(raw.read_bytes()).hexdigest() == record['sha256']
            assert hashlib.sha256(exported.read_bytes()).hexdigest() == record['export_sha256']
            text = transcript(folder, key)
            data = json.loads(extraction.read_text())
            assert data['insights'] and data['summary']
            assert all(locate_quote(text, i['quote']) for i in data['insights'])
            candidates.append((folder, record, extraction, source))
    print(f'{len(candidates)} sources have verified transcripts and saved cited notes.', flush=True)
    if not args.execute:
        return
    remote = {n: {s['id'] for s in cli('source', 'list', '--notebook', n, '--limit', '100')['sources']} for n in NOTEBOOKS}
    for folder, record, extraction, source in candidates:
        sid, notebook = record['source_id'], record['notebook_id']
        entry = {'creator': folder.name, 'youtube_id': record['youtube_id'], 'source_id': sid,
                 'notebook_id': notebook, 'raw_sha256': record['sha256'],
                 'export_sha256': record['export_sha256'],
                 'extraction_sha256': hashlib.sha256(extraction.read_bytes()).hexdigest(),
                 'source_notes_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                 'authorization': 'User explicitly approved reuse of these two task notebooks, 2026-11-16',
                 'removed': False, 'attempted_at': datetime.now(timezone.utc).isoformat()}
        audit.append(entry)
        save(audit_path, audit)
        if sid in remote[notebook]:
            cli('source', 'delete', sid, '--notebook', notebook, '--yes')
        entry['removed'] = True
        entry['completed_at'] = datetime.now(timezone.utc).isoformat()
        save(audit_path, audit)
        if record['url'] in registry:
            registry[record['url']]['status'] = 'exported-and-recycled'
        save(registry_path, registry)
        print(f"Recycled {folder.name}/{record['youtube_id']}; local evidence retained.", flush=True)


if __name__ == '__main__':
    main()
