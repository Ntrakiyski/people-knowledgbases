#!/usr/bin/env python3
"""Report progress on the frozen deeper-review selection, checking prior drafts."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from render import ROOT, review_scope


def main():
    plan = json.loads((ROOT / 'analysis/deep-review/plan.json').read_text())
    inventory = {(r['creator_slug'], r['youtube_id']): r
                 for r in csv.DictReader((ROOT / 'analysis/videos.csv').open())}
    completed, pending = [], []
    for target in plan['videos']:
        slug, key = target['creator_slug'], target['youtube_id']
        data = json.loads((ROOT / slug / 'scripts/extractions' / f'{key}.json').read_text())
        row = dict(inventory[slug, key])
        if review_scope(data) == 'complete-transcript-read-by-Codex':
            previous = ROOT / data['previous_draft']
            if hashlib.sha256(previous.read_bytes()).hexdigest() != data['previous_draft_sha256']:
                raise ValueError(f'Previous draft changed: {previous}')
            if review_scope(json.loads(previous.read_text())) != 'selected-passages':
                raise ValueError(f'Wrong prior scope: {previous}')
            if not all(data.get(k) for k in ('context_and_limits', 'review_changes', 'deep_review_date')):
                raise ValueError(f'Incomplete deep review: {slug}/{key}')
            row['review_changes'] = data['review_changes']
            completed.append(row)
        else:
            pending.append(row)
    order = lambda r: (r['creator_slug'], int(r['recency_rank']))
    completed.sort(key=order)
    pending.sort(key=order)
    result = {'status': 'complete' if not pending else 'in-progress',
              'target_videos': len(plan['videos']), 'completed': len(completed),
              'remaining': len(pending),
              'complete_transcripts_read_words': sum(int(r['transcript_words']) for r in completed),
              'by_creator': {slug: {'completed': sum(r['creator_slug'] == slug for r in completed),
                                   'remaining': sum(r['creator_slug'] == slug for r in pending)}
                             for slug in sorted({r['creator_slug'] for r in plan['videos']})},
              'completed_videos': completed, 'remaining_videos': pending,
              'limits': ['Full reading is not exhaustive interpretation or independent factual verification.',
                         'The 64 NotebookLM drafts are outside this 99-video deepening selection.']}
    directory = ROOT / 'analysis/deep-review'
    (directory / 'progress.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    body = ['---', 'type: overview', 'title: "Deeper transcript review progress"', '---', '',
            '# Deeper transcript review progress', '',
            f"Status: **{len(completed)}/{len(plan['videos'])} complete-transcript reviews saved; {len(pending)} remain.**",
            '', f"Completed readings cover {result['complete_transcripts_read_words']:,} transcript words. No parallel agents were used for this deeper-review pass.", '',
            'The target is the 99 sources previously reviewed through selected passages. Earlier drafts are preserved in `previous/`; current source pages include context, limits, and what the full reading adds. The other 64 NotebookLM extraction drafts remain outside this pass. Reading a complete transcript does not certify every interpretation, resolve every speaker, or verify its factual claims.', '',
            '| Creator | Deepened in this pass | Still pending |', '| --- | ---: | ---: |']
    for slug, counts in result['by_creator'].items():
        name = next(r['creator'] for r in inventory.values() if r['creator_slug'] == slug)
        body.append(f"| {name} | {counts['completed']} | {counts['remaining']} |")
    body += ['', '## Findings and interpretation changes', '',
             'Read the [deeper analysis findings](../deeper-analysis.md) and [cross-creator comparison](../comparison.md). Full summaries and limits are exported in [video-reviews.jsonl](../video-reviews.jsonl); exact insight quotations remain in [insights.jsonl](../insights.jsonl).', '',
             '## Completed readings', '']
    for row in completed:
        title = row['title'].replace('[', '(').replace(']', ')')
        body += [f"- {row['creator']}: [{title}](../../{row['creator_slug']}/sources/{row['youtube_id']}.md). {row['review_changes']}"]
    remaining_text = ('Ordered by creator and original recency rank. These remain selected-passage reviews; none are silently counted as complete.'
                      if pending else 'None remain in the frozen 99-source target. The 64 NotebookLM drafts are outside this pass.')
    body += ['', '## Remaining full readings', '', remaining_text, '']
    for row in pending:
        title = row['title'].replace('[', '(').replace(']', ')')
        body.append(f"- {row['creator']} #{row['recency_rank']}: [{title}](../../{row['creator_slug']}/sources/{row['youtube_id']}.md) ({int(row['transcript_words']):,} words).")
    (directory / 'progress.md').write_text('\n'.join(body) + '\n')
    print(f"Deeper review: {len(completed)} complete, {len(pending)} pending; previous-draft hashes verified.")


if __name__ == '__main__':
    main()
