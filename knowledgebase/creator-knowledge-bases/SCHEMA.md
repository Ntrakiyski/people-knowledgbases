---
type: overview
title: "Schema and provenance"
---

# Schema and provenance

This collection extends the Sharran knowledge-base workflow derived from [coleam00/cole-medin-knowledge-base](https://github.com/coleam00/cole-medin-knowledge-base), upstream commit `eba5e31bc628280c546d4828491051c308d550dc`. It uses separate creator folders, source transcripts, evidence-backed concept notes, and ordinary Markdown links. It does not claim that incomplete source notes are a finished wiki.

## Collection scope

All public uploads returned by each channel's Videos tab on 2026-11-16 are cataloged. Shorts, livestream tabs, private videos and deleted videos are excluded. Publication dates remain empty when enumeration supplies no reliable date. The confirmed target is the newest 40 Videos-tab uploads per creator (200 total), recorded in root and per-creator selection.json files. Full catalogs are retained for optional expansion. The initial NotebookLM batch contained 20 videos per creator; the completed first pass contains all 40 selected videos per creator. No X/Twitter posts have been imported.

## Evidence files

- `<creator>/channel.json` records channel identity and platform URLs.
- `<creator>/youtube-catalog.json` preserves the enumeration response; `catalog.json` contains normalized video metadata.
- `<creator>/exports/notebooklm/<video-id>.md` preserves the exported transcript beneath its title and canonical URL.
- `<creator>/raw/<video-id>.md` wraps the unchanged transcript text with provenance metadata. Raw files are immutable and SHA-256 checked against `raw/manifest.json`.
- `notebook-sources.json` maps canonical URLs to task-owned notebooks and source IDs, allowing imports to resume without duplicates.
- `<creator>/scripts/extractions/<video-id>.json` contains source-restricted extraction checkpoints. Their explanations remain editorial drafts, with review scope recorded separately from quotation integrity.
- `<creator>/sources/<video-id>.md` presents the source summary and quoted insights.
- `<creator>/concepts/<slug>.md` groups same-slug treatments within one creator. These pages remain source notes until cross-video synthesis is reviewed.
- `analysis/insights.jsonl` contains one structured insight per line, preserving creator identity, video URL, exact quote, text offsets, tags, extraction status and raw-file hash.

## Citation rules

NotebookLM exports do not include timestamps. Do not fabricate timecodes. For NotebookLM exports, character offsets use zero-based Unicode string positions in the original transcript content, excluding Markdown headings and metadata; the end position is exclusive. A quote must equal that exact character slice. A case or whitespace variant from extraction is accepted only when the original exact source characters are restored before publication. Punctuation is not silently repaired.

Quote checks establish wording and source identity, not factual accuracy. Speaker claims, anecdotes and estimated outcomes remain attributed. Sources may feature guests; do not assume every voice is the channel owner. Similar tags across creators do not establish agreement. Do not merge creator identities or treat X account links as evidence that X posts were analyzed.

## Processing

The confirmed newest-40 selection is fully imported. For a deliberately authorized refresh of that scope, the importer is `python3 scripts/import_notebooklm.py --per-creator 40`. The CLI pins every request to its notebook and paces source additions. The user explicitly authorized recycling sources in the two task-created notebooks after transcript exports and cited notes are saved and hash/quote-verified locally. The source-ID history and recycling audit are retained; unrelated notebooks and sources are never changed.

If a Supadata key is supplied through secure input, run `python3 scripts/import_supadata.py --key-file <secure-path>` to continue the selected 200 videos with native timestamped captions. Existing raw transcripts are kept. Native imports will need a separate synthesis intake; the current extractor uses registered NotebookLM source IDs.

The initial controller, `scripts/run_collection.py`, coordinates import, extraction, checks and recycling. It is not currently needed: all selected sources and notes are saved, and NotebookLM chat rejected later analysis requests. Do not restart a failing chat loop without testing access first. Do not run competing import/recycling controllers. Run `python3 scripts/extract.py` to process currently imported sources manually, then `python3 scripts/render.py` to rebuild navigation, source notes, concept evidence and the analysis dataset. New imports require another extraction pass. NotebookLM account limits can prevent further imports or generation; saved catalogs and checkpoints remain usable.

Run `python3 scripts/validate.py` to verify local artifacts. Use `--require-complete` to test selected-scope completion, including reviewed synthesis. Use `--require-full-archive` for the optional full archive. A clean integrity report with pending catalog entries does not establish complete coverage.

## Review scope of the completed first pass

At the end of the initial pass, all 200 selected transcripts had draft source notes: 64 NotebookLM source-restricted drafts, 37 complete-transcript readings by Codex, and 99 Codex reviews of selected original passages with automatic source guides used for navigation. Those selected-passage reviews were deliberately nonexhaustive and have since been replaced in the deeper pass described below. The source pages and analysis exports disclose the distinction. Automatic guide claims were not treated as verified facts. Exact quotations remain checked against immutable original transcript text.

Each creator's `profile-notes.md` supplies scoped cross-video interpretation. `entities/review.md` interprets selected entity roles while the literal registry index remains curated and nonexhaustive. Books are indexed separately from people, organizations, and tools. A matching name is not a resolved identity or endorsement.

The completion flags in `review.json` refer to these scoped profile and entity-context artifacts. They do not signify human review, exhaustive interpretation, or independent fact checking. Artifact hashes make a later edit visible to validation. Historical recycling hashes describe the files when deletion was authorized and checked; source notes may subsequently evolve while raw transcripts remain immutable.

## Deeper-review pass

The user subsequently requested deeper analysis without parallel agents. The frozen target in `analysis/deep-review/plan.json` contains the 99 sources whose initial review covered selected passages. All 99 now have complete local readings, covering 285,079 transcript words in this pass. The collection therefore has 136 complete-transcript readings, zero remaining selected-passage reviews, and 64 NotebookLM drafts. This frozen deeper pass is complete; the 64 NotebookLM drafts remain outside it. All 200 have transcripts and source notes, but not all 200 have the same direct-reading scope.

Revised checkpoints include `context_and_limits`, `review_changes`, `deep_review_date`, and a hashed `previous_draft` reference. Earlier checkpoints are preserved under `analysis/deep-review/previous/`; raw transcripts and exact exports remain unchanged. `scripts/deepen.py` validates authored quotes before saving revised checkpoints. It does not read or analyze transcripts automatically. `scripts/deep_review_status.py` checks archived checkpoint hashes and refreshes the completed/pending inventory after rendering.

`analysis/video-reviews.jsonl` exports whole-video summaries and qualifications alongside the individual insight dataset. Generated concept pages no longer represented by current insights are removed when they carry the renderer's source-note marker; the original checkpoint still preserves the previous interpretation. Source-page context, full-read status, exact quotation integrity, exhaustive interpretation, and independent factual verification remain distinct.
