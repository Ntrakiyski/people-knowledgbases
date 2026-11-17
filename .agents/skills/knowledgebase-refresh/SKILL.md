---
name: knowledgebase-refresh
description: Run a repeatable refresh of registered social accounts, discover new publications, collect accessible source text, review it and update cited knowledge-base synthesis with a run report.
---

# Refresh social materials

Read [MAINTENANCE.md](../../../knowledgebase/MAINTENANCE.md) and the [people registry](../../../knowledgebase/people.json). This is an end-to-end agent workflow, not just a discovery command. Run serially. A scheduler may invoke this skill, but creating or invoking it does not install a recurring job; only schedule when the user requests it and supplies or accepts a cadence.

## Discover and reconcile

- Honor any requested people, platforms, dates and batch limits. Otherwise check the registered accounts and process accessible new material within the run's available budget, explicitly carrying the remaining queue forward. Never treat a partial batch as a fully current library.
- Run `python3 knowledgebase/scripts/materials.py discover --creator all --limit 100` from the repository root, or choose one registered slug. This checks only the public YouTube Videos tab, validates channel identity, finds the prior metadata anchor and queues new IDs without changing the original catalogs. `--dry-run` leaves files unchanged. A missing anchor is a coverage gap: increase the limit until found or record the unresolved interval. Old baseline videos not in the original selection are not new publications.
- Inspect `updates/catalog.json` for existing pending items, not just newly queued counts. A discovery success means metadata was checked, not that transcripts were saved or reviewed.
- The helper intentionally reports X as `adapter-required`; it has no X client. Check configured X accounts with an available authenticated connector/API or complete export, preserving canonical post IDs, author, publication date, full text and a bounded lookback/pagination record. If a prior successful X check exists, resume with overlap and deduplicate. For a first check without a requested window, use the newest 40 accessible original posts as an explicitly bounded initial sample. Expand referenced thread context as needed and distinguish quoted/retweeted speech from the creator's own. Do not call inaccessible X “checked” or “no new posts.”
- Check other social platforms only when registered with a confirmed first-party URL and included in the requested scope. Do not send messages or interact with posts.

## Capture, review and synthesize

- Capture queued YouTube IDs with `materials.py capture --creator-slug <slug> --source-id <id> --provider auto`. It tries captions and then existing Supadata environment access. An available authenticated NotebookLM export is another intake path; pin its notebook explicitly. Preserve exports before any authorized task-source recycling. Never delete unrelated sources/notebooks.
- Ingest actual X/export text through `materials.py ingest`. Use the maintenance contract for provenance, immutability and idempotence. Titles and snippets stay discovered-only.
- Read complete captured sources and author qualified reviews using the `knowledgebase-update` workflow. The model performs the analysis; the helper only validates, saves and renders. Bring new findings into relevant authored profiles/comparisons with links. Preserve contradictions and source-specific limits.
- A 401/403/429, exhausted credits, sign-in challenge or unavailable session ends that provider's attempts for this run. Record the dependency, retain queued items and continue independent accessible work. Never loop around access failures, expose credentials, or mark an inaccessible platform current.

## Finish a run

Run incremental validation and the affected collection checks. Save `knowledgebase/updates/runs/<UTC-run-id>.json` with start/end time, people/accounts, actual platform windows and pagination/anchor coverage, discovered/captured/reviewed counts, pending IDs, access gaps, changed synthesis paths and validation outcomes. Discovery reports alone are not end-to-end run reports.

Advance a platform's collection/review checkpoint only for the interval actually captured/reviewed; keep metadata discovery checkpoints distinct. A zero-new-material result still needs evidence of a successful check and its window. Report partial success honestly. A scheduler must not commit/push or change platform scope merely because it invokes this skill; honor the user's existing authorization for those actions.
