---
type: overview
title: "Codex project instructions"
description: "Evidence and maintenance rules for agents working in this project."
---

# Project instructions

Read `index.md`, `SCHEMA.md`, and `status.md` before answering knowledge questions.
This project covers Sharran Srivatsaa's channel `UCzpl_gT1bVB1iNZl9yQbWuA`.

- Use only imported transcripts as evidence for the speaker's teachings.
- Keep video metadata separate from synthesized knowledge.
- Cite source videos and timestamps, and preserve exact wording inside quotes.
- Never overwrite raw transcripts or commit credentials.
- Save extraction checkpoints and canonicalize topics before writing pages.
- Run `python3 scripts/build_indexes.py` and `python3 scripts/update_status.py` after corpus changes.
- Run `python3 lint.py`, `python3 scripts/validate.py`, and `python3 -m unittest discover -s tests` before committing.
- Require `python3 scripts/validate.py --require-complete` to pass before claiming full channel coverage.

See `docs/ingestion-workflow.md` to resume imports and synthesis. No permission
is needed to continue the user's authorized knowledge-base build. A missing
transcript credential is an access dependency, not an approval gate.
