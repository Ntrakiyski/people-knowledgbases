---
name: knowledgebase-update
description: Add supplied materials, correct synthesis or deepen existing reviews in the people knowledge base while preserving original evidence, citations and review scope.
---

# Update the knowledge base

All people live under `knowledgebase/creators/<slug>/`, including Sharran. Shared five-creator tools and analysis live under `knowledgebase/operations/peer-collection/`; incremental tools remain under `knowledgebase/scripts/`.

Read [MAINTENANCE.md](../../../knowledgebase/MAINTENANCE.md), the affected collection's `AGENTS.md`, schema and status. Find identity and collection paths in `knowledgebase/people.json`. Use `knowledgebase-refresh` when the task is to discover new publications; this workflow handles the actual evidence and synthesis changes.

## New material

1. Verify the source belongs to the registered person/account and has not already been captured in either a legacy manifest or incremental catalog. Key by person, platform and stable material ID; URL variants are not new sources.
2. Add metadata to the incremental queue. Capture YouTube captions with `knowledgebase/scripts/materials.py capture`; use an accessible authenticated NotebookLM session when needed, pinning notebook IDs and saving the actual export. For X or other supported public/user-authorized materials, capture the complete actual text through an available connector/API/export and use `ingest`. Search snippets, title text and AI source guides are not full source text.
3. Follow the input and review contracts in maintenance. Originals are immutable; different content for an existing ID needs a separately documented revision, never an overwrite. Preserve native segments and provider exports when available; character quotes never justify invented timestamps.
4. Read the captured material, author a qualified summary and exact-quote insights, and submit `review`. Use `complete-source-read-by-agent` only after a full reading; selected passages and provider drafts have distinct labels. For short posts, quote the full relevant sentence; if a post has fewer than six words, retain it as captured-only and describe the limitation instead of padding its quote.
5. Update the person's authored synthesis with links to the new notes. In the five-creator bundle edit `profile-notes.md`, then render and refresh the artifact hashes as documented. For Sharran preserve the canonical page/checkpoint workflow. Add cross-creator conclusions only when both sides have evidence. Keep disagreements and uncertainty explicit.

## Existing reviews

Preserve the previous checkpoint and the raw evidence. The legacy `deepen.py` accepts only the 99 historically selected-passage sources; it is not a generic review command and that pass is already complete. To review one of the remaining 64 NotebookLM drafts, archive the prior extraction, read its entire local transcript, author evidence in the existing checkpoint schema, and record the actual review method. Rebuild and recompute scope counts from checkpoints; never upgrade status merely because a script ran.

The original newest-40 catalogs and selection files are frozen snapshots. New social publications use `updates/`; do not redefine a snapshot to make counts look current. New sources are not automatically included in the old 854-insight dataset. Search both layers and disclose their boundaries.

Run the affected corpus checks plus incremental validation. Report newly captured, reviewed, changed and blocked sources separately, with links. Do not label reported creator outcomes as independently verified facts.
