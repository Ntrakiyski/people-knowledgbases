#!/usr/bin/env python3
"""Discover new YouTube uploads and maintain immutable incremental social evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SAFE = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
SCOPES = {'complete-source-read-by-agent', 'selected-passages', 'provider-draft'}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
        temporary = Path(f.name)
    temporary.replace(path)


def registry(root):
    rows = read(root / 'people.json')['people']
    if len({p['slug'] for p in rows}) != len(rows):
        raise ValueError('Duplicate person slug')
    for person in rows:
        if not SAFE.fullmatch(person['slug']):
            raise ValueError('Invalid person slug')
    return {p['slug']: p for p in rows}


def catalog(root):
    path = root / 'updates/catalog.json'
    return read(path) if path.exists() else {'schema_version': 1, 'items': []}


def material_key(row):
    return ':'.join(row[k] for k in ('creator_slug', 'platform', 'source_id'))


def folder_for(root, row):
    for name in ('creator_slug', 'platform', 'source_id'):
        if not isinstance(row.get(name), str) or not SAFE.fullmatch(row[name]):
            raise ValueError(f'Invalid {name}')
    if row['creator_slug'] not in registry(root):
        raise ValueError('Register this creator before importing material')
    return root / 'updates/materials' / row['creator_slug'] / row['platform'] / row['source_id']


def upsert(data, row):
    key = material_key(row)
    prior = next((i for i in data['items'] if material_key(i) == key), None)
    if prior:
        prior.update(row)
    else:
        data['items'].append(row)


def queue(root, supplied):
    rows = supplied if isinstance(supplied, list) else [supplied]
    data = catalog(root)
    existing = {material_key(i) for i in data['items']}
    for row in rows:
        folder_for(root, row)
        validate_url(row)
        if not isinstance(row.get('title'), str) or not row['title'].strip():
            raise ValueError('Title required for discovered material')
        if material_key(row) not in existing:
            upsert(data, {k: row[k] for k in ('creator_slug', 'platform', 'source_id', 'url', 'title')} |
                   {'status': 'discovered', 'published_at': row.get('published_at'), 'discovered_at': now()})
            existing.add(material_key(row))
    save(root / 'updates/catalog.json', data)


def validate_url(row):
    parsed = urlparse(row['url'])
    host = parsed.hostname
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        raise ValueError('Source URL must be an HTTPS URL without embedded credentials')
    if row['platform'] == 'youtube':
        if host not in {'www.youtube.com', 'youtube.com', 'youtu.be'}:
            raise ValueError('YouTube source has a different host')
        actual = parsed.path.lstrip('/') if host == 'youtu.be' else parse_qs(parsed.query).get('v', [''])[0]
        if actual != row['source_id']:
            raise ValueError('YouTube URL and source ID differ')
    if row['platform'] == 'x':
        if host not in {'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com'}:
            raise ValueError('X source has a different host')
        if not re.fullmatch(r'/[^/]+/status/' + re.escape(row['source_id']), parsed.path.rstrip('/')):
            raise ValueError('X URL and source ID differ')


def select_new(entries, known):
    """Stop at a previously enumerated anchor, keeping older excluded uploads out."""
    found, seen = [], set()
    for entry in entries:
        if not entry:
            continue
        key = entry['id']
        if key in known:
            return found, True
        if key not in seen:
            found.append(entry)
            seen.add(key)
    return found, False


def discover(root, creator, limit, dry_run=False):
    people = registry(root)
    if creator != 'all' and creator not in people:
        raise ValueError('Unknown creator')
    data = catalog(root)
    report = {'checked_at': now(), 'youtube': [], 'x': []}
    for slug, person in people.items():
        if creator not in ('all', slug):
            continue
        account = person.get('youtube')
        if account:
            try:
                baseline = read(root / person['baseline_catalog'])
                known = {v['youtube_id'] for v in baseline['videos']}
                known.update(data.get('discovery_anchors', {}).get(slug, []))
                result = subprocess.run(['yt-dlp', '--flat-playlist', '--dump-single-json',
                    '--skip-download', '--no-warnings', '--socket-timeout', '20', '--retries', '0',
                    '--playlist-end', str(limit), account['url'].rstrip('/') + '/videos'],
                    capture_output=True, text=True, timeout=55)
                if result.returncode:
                    raise RuntimeError('metadata access failed')
                info = json.loads(result.stdout)
                if info.get('channel_id') != account['channel_id']:
                    raise ValueError('channel identity mismatch')
                entries = [e for e in info.get('entries', []) if e]
                if not entries:
                    raise ValueError('empty feed')
                candidates, anchored = select_new(entries, known)
                count = 0
                existing = {material_key(i) for i in data['items']}
                for e in candidates:
                    row = {'creator_slug': slug, 'platform': 'youtube', 'source_id': e['id'],
                           'url': 'https://www.youtube.com/watch?v=' + e['id'],
                           'title': e['title'], 'published_at': None, 'status': 'discovered',
                           'discovered_at': report['checked_at']}
                    folder_for(root, row)
                    validate_url(row)
                    if material_key(row) not in existing:
                        upsert(data, row)
                        count += 1
                if anchored:
                    data.setdefault('discovery_anchors', {})[slug] = list(dict.fromkeys(
                        data.get('discovery_anchors', {}).get(slug, []) + [e['id'] for e in entries]))
                report['youtube'].append({'creator_slug': slug, 'status': 'checked' if anchored else 'gap',
                    'newly_queued': count, 'anchor_found': anchored,
                    'note': 'Older baseline uploads remain excluded.' if anchored else
                    'No known anchor within limit; rerun with a larger --limit. Do not claim a complete interval.'})
            except (ValueError, KeyError, RuntimeError, OSError, subprocess.SubprocessError) as error:
                report['youtube'].append({'creator_slug': slug, 'status': 'blocked',
                    'reason': str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__})
        report['x'].append({'creator_slug': slug, 'url': person.get('x', {}).get('url'),
            'status': 'adapter-required' if person.get('x', {}).get('url') else 'not-configured',
            'note': 'This helper does not query X. Use an authenticated connector/API or supplied export; record its actual result in the run report.'})
    if not dry_run:
        save(root / 'updates/catalog.json', data)
        save(root / 'updates/runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-discovery.json'), report)
    return report


def ingest(root, supplied):
    row = dict(supplied)
    folder = folder_for(root, row)
    validate_url(row)
    for field in ('title', 'provider', 'text', 'attribution'):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f'Nonempty {field} is required; metadata alone is not evidence')
    if row.get('published_at') is not None:
        datetime.fromisoformat(row['published_at'].replace('Z', '+00:00'))
    row.setdefault('published_at', None)
    row.setdefault('captured_at', now())
    row.update(immutable=True, text_sha256=digest(row['text'].encode()))
    raw = folder / 'raw.json'
    if raw.exists():
        old = read(raw)
        if any(old.get(k) != row.get(k) for k in ('creator_slug', 'platform', 'source_id', 'url', 'text', 'attribution')):
            raise ValueError('Existing evidence differs; immutable original retained')
        row = old
    else:
        save(raw, row)
    data = catalog(root)
    status = 'reviewed' if (folder / 'review.json').exists() else 'captured'
    upsert(data, {k: row[k] for k in ('creator_slug', 'platform', 'source_id', 'url', 'title', 'published_at')} |
           {'status': status, 'raw_sha256': digest(raw.read_bytes())})
    save(root / 'updates/catalog.json', data)
    return folder


def capture(root, creator_slug, source_id, provider):
    identity = {'creator_slug': creator_slug, 'platform': 'youtube', 'source_id': source_id}
    folder = folder_for(root, identity)
    if (folder / 'raw.json').exists():
        return folder
    queued = next((row for row in catalog(root)['items'] if material_key(row) == material_key(identity)), None)
    if queued is None:
        raise ValueError('Discover or explicitly queue this video before capturing it')
    spec = importlib.util.spec_from_file_location('caption_backend', root / 'sharran-knowledge-base/scripts/fetch_transcripts.py')
    backend = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend)
    if provider == 'supadata':
        key = os.environ.get('SUPADATA_API_KEY')
        if not key:
            raise ValueError('SUPADATA_API_KEY is unavailable; use existing secure environment access')
        segments = backend.supadata(source_id, key)
        actual_provider = 'supadata-native'
    else:
        try:
            segments = backend.ytdlp(source_id)
            actual_provider = 'yt-dlp-captions'
        except (RuntimeError, OSError, subprocess.SubprocessError):
            if provider != 'auto' or not os.environ.get('SUPADATA_API_KEY'):
                raise ValueError('Caption access blocked; source remains pending. Use available Supadata or pinned NotebookLM access.') from None
            segments = backend.supadata(source_id, os.environ['SUPADATA_API_KEY'])
            actual_provider = 'supadata-native'
    previous = -1
    for row in segments:
        start = float(row['start'])
        if not math.isfinite(start) or start < 0 or start < previous or not isinstance(row['text'], str):
            raise ValueError('Invalid native caption segments')
        previous = start
    person = registry(root)[creator_slug]
    return ingest(root, {**identity, 'url': queued['url'], 'title': queued['title'],
        'published_at': queued.get('published_at'), 'provider': actual_provider,
        'attribution': person['name'] + ' channel; guest speakers require review',
        'text': '\n'.join(row['text'] for row in segments), 'native_segments': segments})


def prepare_review(raw, review):
    if review.get('review_scope') not in SCOPES:
        raise ValueError('Invalid or missing review_scope')
    for field in ('summary', 'context_and_limits'):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise ValueError(f'Missing {field}')
    if not review.get('insights'):
        raise ValueError('A reviewed note needs at least one evidenced insight')
    for insight in review['insights']:
        for field in ('title', 'explanation', 'quote', 'speaker'):
            if not isinstance(insight.get(field), str) or not insight[field].strip():
                raise ValueError(f'Missing insight {field}')
        quote = insight['quote'].strip()
        if len(quote.split()) < 6:
            raise ValueError('Quote must contain at least six source words')
        match = re.search(r'\s+'.join(re.escape(w) for w in quote.split()), raw['text'], re.I)
        if not match:
            raise ValueError('Quotation not present in the captured source')
        insight.update(quote=match[0], character_start=match.start(), character_end=match.end())
    review.update(independent_factual_verification=False, reviewed_at=now())
    return review


def review_source(root, identity, supplied):
    folder = folder_for(root, identity)
    raw = read(folder / 'raw.json')
    review = prepare_review(raw, supplied)
    review['raw_sha256'] = digest((folder / 'raw.json').read_bytes())
    path = folder / 'review.json'
    if path.exists():
        previous = path.read_bytes()
        archive = folder / 'history' / (digest(previous) + '.json')
        if not archive.exists():
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_bytes(previous)
    save(path, review)
    data = catalog(root)
    upsert(data, {k: raw[k] for k in ('creator_slug', 'platform', 'source_id', 'url', 'title', 'published_at')} |
           {'status': 'reviewed', 'raw_sha256': review['raw_sha256']})
    save(root / 'updates/catalog.json', data)
    rebuild(root)


def rebuild(root):
    data = catalog(root)
    lines = ['# Incremental materials', '',
        'New source supplements are separate from the original newest-40 snapshot. Discovery is metadata; captured and reviewed are different stages.', '',
        '| Person | Platform | Material | Status |', '| --- | --- | --- | --- |']
    for item in sorted(data['items'], key=material_key):
        folder = folder_for(root, item)
        label = item['title'].replace('|', '/').replace('[', '(').replace(']', ')').replace('\n', ' ')
        target = item['url']
        if (folder / 'raw.json').exists():
            raw = read(folder / 'raw.json')
            review_path = folder / 'review.json'
            body = ['---', 'type: source', 'title: ' + json.dumps(raw['title']), '---', '',
                '# ' + raw['title'], '', f"Original: {raw['url']}", '',
                f"Attribution: {raw['attribution']}", '', '[Captured original text and provenance](raw.json).', '']
            if review_path.exists():
                review = read(review_path)
                body += ['Review scope: ' + review['review_scope'] + '. Claims are not independently verified.', '',
                    review['summary'], '', '## Context and limits', '', review['context_and_limits'], '', '## Insights', '']
                for insight in review['insights']:
                    body += ['### ' + insight['title'], '', insight['explanation'], '',
                        'Speaker: ' + insight['speaker'], '',
                        f"Exact source quote (characters {insight['character_start']}–{insight['character_end']}, end exclusive):", '',
                        '> ' + insight['quote'].replace('\n', '\n> '), '']
            else:
                body += ['Captured only. Editorial review pending.', '']
            (folder / 'source.md').write_text('\n'.join(body))
            target = str((folder / 'source.md').relative_to(root / 'updates'))
        lines.append(f"| {item['creator_slug']} | {item['platform']} | [{label}]({target}) | {item['status']} |")
    (root / 'updates/index.md').write_text('---\ntype: overview\ntitle: Incremental materials\n---\n\n' + '\n'.join(lines) + '\n')


def validate(root):
    data, errors, seen = catalog(root), [], set()
    for item in data['items']:
        try:
            key = material_key(item)
            if key in seen:
                raise ValueError('Duplicate catalog identity')
            seen.add(key)
            folder = folder_for(root, item)
            validate_url(item)
            if item['status'] not in {'discovered', 'captured', 'reviewed'}:
                raise ValueError('Invalid catalog status')
            if item['status'] == 'discovered':
                if (folder / 'raw.json').exists():
                    raise ValueError('Captured evidence is still marked discovered; rerun ingest to reconcile it')
                continue
            raw = read(folder / 'raw.json')
            if material_key(raw) != key or raw['url'] != item['url']:
                raise ValueError('Source identity differs from catalog')
            if raw.get('immutable') is not True or digest(raw['text'].encode()) != raw['text_sha256']:
                raise ValueError('Captured source text changed')
            if digest((folder / 'raw.json').read_bytes()) != item['raw_sha256']:
                raise ValueError('Raw file hash differs from catalog')
            if item['status'] == 'reviewed':
                rev = read(folder / 'review.json')
                if rev['raw_sha256'] != item['raw_sha256']:
                    raise ValueError('Review refers to changed evidence')
                checked = prepare_review(raw, json.loads(json.dumps(rev)))
                if rev['insights'] != checked['insights'] or rev.get('independent_factual_verification') is not False:
                    raise ValueError('Review evidence or scope flags are inconsistent')
        except (ValueError, KeyError, OSError, TypeError) as error:
            errors.append(f"{item.get('creator_slug')}/{item.get('source_id')}: {error}")
    for raw_path in (root / 'updates/materials').glob('*/*/*/raw.json'):
        if material_key(read(raw_path)) not in seen:
            errors.append(f'Captured evidence missing from catalog: {raw_path.relative_to(root)}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    d = commands.add_parser('discover')
    d.add_argument('--creator', default='all')
    d.add_argument('--limit', type=int, default=100)
    d.add_argument('--dry-run', action='store_true')
    i = commands.add_parser('ingest'); i.add_argument('--input', type=Path, required=True)
    q = commands.add_parser('queue'); q.add_argument('--input', type=Path, required=True)
    cap = commands.add_parser('capture')
    cap.add_argument('--creator-slug', required=True)
    cap.add_argument('--source-id', required=True)
    cap.add_argument('--provider', choices=['auto', 'yt-dlp', 'supadata'], default='auto')
    rev = commands.add_parser('review')
    for name in ('creator-slug', 'platform', 'source-id'):
        rev.add_argument('--' + name, required=True)
    rev.add_argument('--input', type=Path, required=True)
    commands.add_parser('rebuild'); commands.add_parser('validate')
    args = parser.parse_args()
    try:
        if args.command == 'discover':
            if args.limit < 1:
                raise ValueError('--limit must be positive')
            print(json.dumps(discover(ROOT, args.creator, args.limit, args.dry_run), indent=2))
        elif args.command == 'ingest':
            print(ingest(ROOT, read(args.input)).relative_to(ROOT)); rebuild(ROOT)
        elif args.command == 'queue':
            queue(ROOT, read(args.input)); rebuild(ROOT)
        elif args.command == 'capture':
            print(capture(ROOT, args.creator_slug, args.source_id, args.provider).relative_to(ROOT)); rebuild(ROOT)
        elif args.command == 'review':
            review_source(ROOT, vars(args), read(args.input))
        elif args.command == 'rebuild':
            rebuild(ROOT)
        else:
            errors = validate(ROOT)
            print('\n'.join(errors) if errors else 'Incremental evidence and quote checks passed.')
            return int(bool(errors))
    except (ValueError, KeyError, OSError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{type(error).__name__}: {error}\n')
    return 0


if __name__ == '__main__':
    import fcntl
    # A scheduler and an interactive refresh must not overwrite each other's catalog.
    with (ROOT / 'updates/.writer.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another material command is active; retry after it finishes.')
        raise SystemExit(main())
