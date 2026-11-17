# Knowledge base

The source snapshot was collected on 2026-11-16. Later captures belong in the incremental updates layer, so a refresh does not redefine the original newest-40 selection.

## Start here

- [Five-creator homepage](creator-knowledge-bases/index.md), [comparison](creator-knowledge-bases/analysis/comparison.md), [deeper analysis](creator-knowledge-bases/analysis/deeper-analysis.md) and [topic index](creator-knowledge-bases/analysis/topics.md).
- [Sharran homepage](sharran-knowledge-base/index.md), [profile](sharran-knowledge-base/creator-profile.md) and [similar-creator research](sharran-knowledge-base/similar-creators.md).
- [New materials](updates/index.md): incremental sources captured after the snapshot.
- [People registry](people.json): canonical identities, collection locations and monitored accounts.

## Evidence structure

Each legacy collection retains its profiles, source summaries, concepts, entities, immutable transcripts, exports, extraction checkpoints and local validation tools. Their relative links continue to work because the two bundles remain siblings.

The five-creator structured exports are [individual insights](creator-knowledge-bases/analysis/insights.jsonl), [whole-video reviews](creator-knowledge-bases/analysis/video-reviews.jsonl) and [the video inventory](creator-knowledge-bases/analysis/videos.csv). Sharran's timestamped format remains separate from the five-creator NotebookLM exports that use character offsets. Do not merge timestamps or compare differently defined review counts.

## Working with the library

Start with a decision or research question. Use profiles to understand perspective, topics to find sources, then source notes and original text to assess support. Include new-material notes in searches: the original 854-insight export is a snapshot, not an automatic union with future updates.

Ask for the actual speaker, conditions, required resources, reported outcomes and counterexamples. A forecast, hypothetical calculation and observed result are different evidence types. A matching name is not proof of identity or endorsement.

See [MAINTENANCE.md](MAINTENANCE.md) before creating, importing, refreshing or rebuilding anything. The four workflows are available in [the repository skills](../.agents/skills/).
