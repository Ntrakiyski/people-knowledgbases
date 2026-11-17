# Maintenance contract

Run commands from the repository root unless a working directory is shown. Python 3.10+ and the standard library support the incremental tools; existing legacy importers have their own provider dependencies. Install `yt-dlp` for YouTube discovery/captions. `requests` is required by some legacy Supadata importers. NotebookLM requires a separately authenticated CLI session. Credentials belong in secure process environment/input, never this repository.

## Storage and scope

`people.json` maps stable person slugs to official accounts and relative collection paths. All six collections are peers under `creators/<slug>/`. Shared five-creator scripts, tests, schema, coverage, analysis and provider audit files live under `operations/peer-collection/`. Sharran retains its local schema and tools inside `creators/sharran-srivatsaa/`; preserve the two citation formats. A new person's authored collection lives under `creators/<slug>/` and is registered using the same metadata contract. Its baseline catalog uses `channel_id` and `videos` rows containing `youtube_id`, `title` and `url`.

Preserve original catalogs, raw/manifest files and newest-40 selections. They describe the 2026-11-16 snapshot. A normal refresh adds material in `updates/`, including material for existing people, rather than redefining historical coverage. To expand the old archive selection, treat that as a separate explicit task.

The incremental layout is:

```text
updates/
  catalog.json                         # discovered, captured and reviewed states
  index.md                             # generated material navigation
  runs/<UTC-run-id>.json                # coverage, failures and completed work
  materials/<person>/<platform>/<id>/
    raw.json                           # immutable exact source text/provenance
    review.json                        # authored summary, scope and exact insights
    source.md                          # generated reading page
    history/<previous-review-hash>.json # archived earlier reviews
```

This layer is searchable alongside legacy sources. Legacy JSONL datasets remain snapshot exports; do not describe them as containing new incremental sources. Capture records and run reports preserve the actual author, provider, publication date when known, capture time, canonical URL and stable source ID. If source content changes, retain the original and record a separately identified revision with its relationship; do not modify `raw.json`.

## Discovery and caption capture

```bash
python3 knowledgebase/scripts/materials.py discover --creator all --limit 100 --dry-run
python3 knowledgebase/scripts/materials.py discover --creator alex-hormozi --limit 100
python3 knowledgebase/scripts/materials.py capture --creator-slug alex-hormozi --source-id VIDEO_ID --provider auto
```

`discover` uses `yt-dlp` to inspect the Videos tab. It checks the returned channel ID and stops at known metadata. Only a scan reaching an existing anchor can extend discovery anchors. A gap or empty/blocked response never advances them. Increase `--limit` when the previous known upload is farther back. The default 100 is a discovery bound, not a promise that 100 uploads cover every interval. Existing queued items keep their state and are never silently dropped.

`capture --provider auto` uses the shipped Sharran caption backend: yt-dlp, then existing `SUPADATA_API_KEY` access if available. `--provider yt-dlp` and `--provider supadata` choose one. Native caption segments are preserved alongside text. Stop using a provider on access/credit/rate errors rather than retrying every remaining item. NotebookLM exports may be supplied through `ingest`; the helper does not create, reuse or delete notebooks. Keep notebook IDs explicit in external CLI commands.

The helper has no X client. Use an available authenticated connector/API or complete export for X, then ingest its actual text. Record a bounded lookback, pagination completeness, known gaps and author identity. A linked account is not proof of imported posts. Sharran's X account is deliberately unconfigured until first-party identity is confirmed. Other platforms require a registered confirmed URL before recurring monitoring.

All material commands take a nonblocking local writer lock so a scheduled run cannot overwrite an interactive catalog update. If another command owns it, retry after that command ends. Do not start competing refresh agents/controllers.

## Manual queue and exact-text intake

`queue --input /secure-or-temporary-path/metadata.json` accepts one metadata object or an array. It requires `creator_slug`, `platform`, `source_id`, `url` and `title`, with optional `published_at`. Use it for explicitly supplied URLs, initial selections and external discovery. Validate account membership first; the helper validates IDs/URL consistency, not a person's ownership of the source. It never downgrades an existing captured/reviewed item.

To ingest text already obtained through an authorized provider, write a temporary JSON object with:

```json
{
  "creator_slug": "registered-person-slug",
  "platform": "youtube",
  "source_id": "VIDEO_ID",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "title": "Actual source title",
  "published_at": null,
  "provider": "actual-provider-or-user-export",
  "attribution": "Actual author or channel; identify guests when established",
  "text": "The complete exact captured text belongs here."
}
```

Use platform `x` and its actual canonical `https://x.com/HANDLE/status/POST_ID` URL for posts. An X ID is the post ID, not its author's handle. `published_at` is an ISO timestamp/date or null; never infer it from enumeration order. Preserve a fetched provider export separately when useful and record its location/hash as extra provenance fields. Do not include authentication response bodies, headers or cookies.

```bash
python3 knowledgebase/scripts/materials.py queue --input /tmp/material-metadata.json
python3 knowledgebase/scripts/materials.py ingest --input /tmp/captured-material.json
```

Reimporting identical evidence is idempotent and preserves the first capture. Changed text or attribution for the same ID is rejected. If interrupted after saving `raw.json` but before updating the catalog, rerun the same intake to reconcile; do not delete the original.

## Authored review and synthesis

Read the source before writing a review. A review JSON contains:

```json
{
  "review_scope": "complete-source-read-by-agent",
  "summary": "An attributed summary based on the actual source.",
  "context_and_limits": "Speaker identity, commercial context, uncertainty and evidence limits.",
  "insights": [{
    "title": "A supported idea",
    "explanation": "A qualified interpretation of the exact evidence.",
    "quote": "An exact passage of at least six source words.",
    "speaker": "Established speaker name, or unresolved",
    "tags": ["relevant-topic"]
  }]
}
```

The other supported scopes are `selected-passages` and `provider-draft`. Do not claim a complete reading if only excerpts were inspected. The helper is an evidence validator/renderer, not an automatic analyst. Its six-word minimum means a shorter post remains captured-only; never pad or join unrelated wording to satisfy it. Native timestamps are preserved as input data, but new notes cite exact character positions. Do not infer timestamps from text offsets.

```bash
python3 knowledgebase/scripts/materials.py review --creator-slug registered-person-slug --platform youtube --source-id VIDEO_ID --input /tmp/authored-review.json
python3 knowledgebase/scripts/materials.py rebuild
python3 knowledgebase/scripts/materials.py validate
```

Quotes are matched for case/whitespace and restored to the exact source characters. Punctuation and wording are not repaired. Offsets are zero-based Unicode string positions and end-exclusive. A previous review is archived by hash before replacement. Independent factual verification is false; wording integrity does not prove a claim.

Update authored synthesis after review, linking incremental notes with paths relative to the profile. For five-creator profiles, edit the creator's `profile-notes.md`, run the legacy renderer, and refresh that creator's reviewed artifact hashes. Keep existing review scope counts based on legacy checkpoints; incremental sources have their own counts. For Sharran canonical pages follow its local schema/checkpoint pipeline. New people's profiles are authored directly in their registered collection. Preserve evidence for contradictory teachings and actual speakers.

After a legacy render changes reviewed artifacts, refresh hashes from the actual files; do not set factual verification, human review or exhaustive interpretation to true. For the existing five-creator layout:

```python
import hashlib, json
from pathlib import Path
root = Path('knowledgebase/creators')
for path in root.glob('*/review.json'):
    review = json.loads(path.read_text())
    for relative in review['artifacts']:
        review['artifacts'][relative] = hashlib.sha256((path.parent / relative).read_bytes()).hexdigest()
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
```

Only refresh a review manifest after checking the relevant authored changes; a new hash alone is not a review.

## Run reports and recurring execution

For each refresh, save an end-to-end report under `updates/runs/`. Include `started_at`, `finished_at`, per-person/platform `status`, checked window, pagination/anchor completeness, discovered/captured/reviewed counts and IDs, pending IDs, access gaps, changed synthesis paths and validation outcomes. Distinguish a metadata discovery checkpoint from a successful capture/review checkpoint. Discovery helpers write `*-discovery.json`; those reports do not establish end-to-end completion.

The refresh skill is callable by an agent on a schedule. No cron entry, external automation or timer is installed in this repository. When scheduling is requested, configure the user's chosen scheduler to invoke `$knowledgebase-refresh` in this checkout, set a bounded run budget and preserve credentials in that scheduler's secure environment. Do not bypass an access failure or authorize publishing merely through a timer prompt.

## Checks

From the repository root:

```bash
python3 knowledgebase/scripts/materials.py validate
python3 -m unittest discover -s knowledgebase/tests
```

For the five-creator bundle, from `knowledgebase/operations/peer-collection/`:

```bash
python3 scripts/render.py
python3 scripts/deep_review_status.py
# Review generated changes and refresh the artifact hashes as above, from repo root.
python3 scripts/validate.py --require-complete
python3 -m unittest discover -s tests
python3 -m py_compile scripts/*.py
```

`--require-complete` is the frozen selected scope, not the full 2,394-video archive or later social updates. All 99 target deeper reviews are complete, but 64 original NotebookLM drafts have not received complete direct readings. The `deepen.py` command is specific to the already finished selected-passage pass.

For the Sharran bundle, from `knowledgebase/creators/sharran-srivatsaa/`:

```bash
# After corpus changes, rebuild indexes/status using its local instructions.
python3 lint.py
python3 scripts/validate.py --require-complete
python3 -m unittest discover -s tests
```

Skill checks use the installed skill-creator `scripts/quick_validate.py` against each folder under `.agents/skills/`. That validator is a development tool, not a runtime dependency of these skills.
