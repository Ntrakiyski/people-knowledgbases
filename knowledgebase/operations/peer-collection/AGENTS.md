---
type: overview
title: "Collection maintenance instructions"
---

# Collection maintenance instructions

Read `SCHEMA.md`, `coverage.json`, and each creator's `status.md` before answering knowledge questions. The five creators live at `../../creators/<slug>/`; Sharran is their sibling at `../../creators/sharran-srivatsaa/` and uses its own citation format. Commands below run from this operational directory.

- Treat catalog titles as metadata. Use imported transcripts for teachings.
- Preserve immutable exports and raw-file hashes. Never overwrite raw transcripts.
- Never invent timestamps for NotebookLM fulltext exports.
- Keep machine-extracted summaries distinct from reviewed synthesis.
- Keep speakers and creators distinct, especially interviews and quoted advice.
- Pin NotebookLM commands to explicit notebook IDs. Never delete unrelated notebooks or sources. User explicitly authorized recycling sources in the two task-created notebooks on 2026-11-16, only after each transcript and cited source note is saved and locally verified; preserve an audit trail.
- Keep secrets out of files and logs in this collection.
- Run `python3 scripts/render.py` and `python3 scripts/validate.py` after changes.
- Only claim selected-scope completion after `python3 scripts/validate.py --require-complete` passes. Full-archive claims additionally require `--require-full-archive`.
