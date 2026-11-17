---
type: overview
title: "Analyze the creator collections"
---

# Analyze the creator collections

Start with each creator's build status. The selected scope is the newest 40 Videos-tab uploads per creator (200 total). Complete archive catalogs are also available for optional expansion. All 200 selected transcripts and draft source notes are saved, with scoped profiles and entity-context guides. This is a completed first analysis pass, not an exhaustive or independently verified interpretation of every transcript. The newest-first batch can overrepresent recent interests.

Use [the topic index](topics.md) to find related evidence across creators. Keep the creator, video, and quoted evidence attached when comparing ideas.

The [video inventory CSV](videos.csv) lists all 200 selected videos, their recency ranks, import/note status, review scope, insight count, transcript word count, URLs and transcript hashes.

The [JSONL dataset](insights.jsonl) is suitable for later analysis in Python, a database, or an AI tool. Each line contains a stable insight ID, creator, concept slug, tags, explanation, video URL, exact quotation, character offsets, transcript provenance, integrity hash and review status. The `review_scope` field separates 64 NotebookLM source-restricted drafts and 136 complete-transcript readings by Codex. No current source remains at selected-passage scope; the 99 earlier selected-passage checkpoints are preserved as historical drafts. Full reading does not establish exhaustive interpretation or factual verification.

Character offsets are zero-based and end-exclusive. No timestamps were supplied by the fallback export; `timestamp_seconds` remains null. Exact quotation verification does not mean an explanation has received human review or that a creator's claims are true.

Use the [comparison guide](comparison.md) for cited starting questions across all five creators. Each creator also has a contextual entity guide alongside the literal index.

The [named-mention dataset](entities.jsonl) groups a disclosed registry of people, organizations and products with exact surrounding passages. It records the first match per video, not every occurrence. Ambiguous names, caption errors and names outside the registry require separate review. A mention does not imply endorsement.

Useful later questions include where creators agree on ownership, how acquisition criteria differ, which business systems they recommend, and where advice depends on business size or personal circumstances. Cite underlying source notes when answering. Silence in a partial corpus is not evidence that a creator disagrees or never discusses a subject.

The [original Sharran collection](../../sharran-knowledge-base/index.md) remains separate and can supply the sixth perspective. It has timestamped evidence; preserve the distinction between those citations and these character-based citations.

The requested [deeper analysis](deeper-analysis.md) is complete for the frozen target: all 99 original selected-passage sources now have complete readings and expanded notes, with none pending. The [progress tracker](deep-review/progress.md) lists all completed sources. The collection contains 854 exact-quote insights across all 200 source notes; the 64 NotebookLM drafts are outside the completed deeper pass. [video-reviews.jsonl](video-reviews.jsonl) exports whole-video theses, summaries, context and limits, revision notes, and previous-draft hashes; this complements the individual-quote insight dataset. Earlier extraction drafts are preserved in `deep-review/previous/`. Run `python3 scripts/deep_review_status.py` after rendering to refresh the progress report and check those archive hashes.
