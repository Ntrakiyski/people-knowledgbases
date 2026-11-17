---
name: knowledgebase-use
description: Answer questions, compare creators and create research or decision briefs from the saved people knowledge bases with cited source evidence and explicit limitations.
---

# Use the people knowledge base

Start with [the library guide](../../../knowledgebase/README.md) and `knowledgebase/people.json`. This skill researches saved material; it does not fetch new posts or change the corpus unless the user also requests an update.

Read applicable collection-local instructions, schema and current status. For the five-creator bundle read `coverage.json`; for Sharran read its `index.md`, `SCHEMA.md` and `status.md`. Include `knowledgebase/updates/index.md` and relevant incremental reviews: the legacy exports are snapshot datasets.

Use profiles and cross-creator comparison as navigation, then support conclusions from source notes and captured original text. Search with `rg` before loading whole corpora. The five-creator `analysis/insights.jsonl` supports quoted-idea analysis; `analysis/video-reviews.jsonl` preserves whole-source context and limits. Sharran has a separate timestamped schema. Check the `review_scope` of the evidence you use.

When answering:

- Lead with the answer to the user's actual question, then cite the underlying source notes/videos. Retain the actual speaker; an interview guest does not establish the channel owner's belief.
- Distinguish a proposal, hypothetical calculation, personal retrospective, reported follow-up and forecast. Exact quotation checking verifies wording, not factual truth. Keep revenue, profit, cash, debt and valuation separate.
- Compare advice at the same business/life stage and objective. Explain meaningful prerequisites and disagreements without inventing a reconciliation. Label your own practical recommendation as an interpretation or experiment.
- Do not use insight frequency as an expertise ranking. Unequal review depth and newest-first sampling affect counts. A missing coded idea is not evidence that a creator never discusses it.
- Books/tools indexes are curated mentions, not automatic endorsements. X account links are identities, not evidence that X posts were analyzed. Check incremental source records before claiming social-platform coverage.
- Reuse native timestamps only where supplied. For the untimestamped exports cite the canonical video and exact passage/character offsets; never manufacture a timecode.

For research briefs, useful outputs include the conclusion, source-backed points of agreement/disagreement, conditions, uncertainty and a small next experiment. Do not force that format onto a simple factual question. State when the saved corpus cannot answer the question; use the update/refresh workflow only when further collection is requested.
