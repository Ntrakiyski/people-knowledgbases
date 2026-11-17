# Knowledge base

The source snapshot was collected on 2026-11-16. Later captures belong in the incremental updates layer, so a refresh does not redefine the original newest-40 selection.

## Start here

All six creator knowledge bases live together in [creators/](creators/index.md):

- [Alex Hormozi](creators/alex-hormozi/index.md)
- [Codie Sanchez](creators/codie-sanchez/index.md)
- [Dan Martell](creators/dan-martell/index.md)
- [Nick Huber](creators/nick-huber/index.md)
- [Sahil Bloom](creators/sahil-bloom/index.md)
- [Sharran Srivatsaa](creators/sharran-srivatsaa/index.md)

Shared research and operations sit alongside the creators folder:

- [Shared analysis](operations/peer-collection/analysis/README.md): [comparison](operations/peer-collection/analysis/comparison.md), [deeper analysis](operations/peer-collection/analysis/deeper-analysis.md) and [topics](operations/peer-collection/analysis/topics.md).
- [Snapshot operations](operations/peer-collection/index.md): shared scripts, tests, coverage, schema and provider audit files for the five-creator snapshot.
- [New materials](updates/index.md): incremental evidence and refresh run reports.
- `scripts/` and `tests/`: shared incremental maintenance tools and their checks.
- [People registry](people.json): canonical identities, creator locations and monitored accounts.

## Evidence structure

Each legacy collection retains its profiles, source summaries, concepts, entities, immutable transcripts, exports, extraction checkpoints and local validation tools. Creator-specific tools remain with their collection; shared snapshot operations are outside the creators folder.

The five-creator structured exports are [individual insights](operations/peer-collection/analysis/insights.jsonl), [whole-video reviews](operations/peer-collection/analysis/video-reviews.jsonl) and [the video inventory](operations/peer-collection/analysis/videos.csv). Sharran's timestamped format remains separate from the five-creator NotebookLM exports that use character offsets. Do not merge timestamps or compare differently defined review counts.

## Working with the library

Start with a decision or research question. Use profiles to understand perspective, topics to find sources, then source notes and original text to assess support. Include new-material notes in searches: the original 854-insight export is a snapshot, not an automatic union with future updates.

Ask for the actual speaker, conditions, required resources, reported outcomes and counterexamples. A forecast, hypothetical calculation and observed result are different evidence types. A matching name is not proof of identity or endorsement.

See [MAINTENANCE.md](MAINTENANCE.md) before creating, importing, refreshing or rebuilding anything. The four workflows are available in [the repository skills](../.agents/skills).
