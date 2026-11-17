---
type: overview
title: "Knowledge-base schema"
description: "Page types, evidence rules, and linking conventions for this channel."
---

# Knowledge-base schema

This bundle follows the upstream repository's OKF 0.1 layout. Its canonical knowledge corpus contains only
content sourced from channel `UCzpl_gT1bVB1iNZl9yQbWuA`. The root
`creator-profile.md` synthesizes that corpus; `similar-creators.md` is supplemental
external research with its own sources and is not transcript evidence. The declared version
describes this bundle; it does not claim conformance to later OKF versions.

## Layout

- `raw/<slug>.md`: immutable, timestamped transcript with `type: raw-transcript`.
- `sources/<slug>.md`: synthesized video summary with `type: source`.
- `concepts/<slug>.md`: one durable idea synthesized across relevant videos, with `type: concept`.
- `entities/{tools,people,organizations}/<slug>.md`: named subject with `type: entity` and the matching singular `subtype`.
- `scripts/extractions/<slug>.json`: durable extraction checkpoints for the next synthesis pass.
- `scripts/manifest.json`: frozen canonical page manifest after extraction.
- `scripts/taxonomy.json`: thematic index groupings.
- `scripts/canonicalization.json`: reviewed aliases, display names, and topic assignments.
- `scripts/pages/**/*.txt`: reviewed synthesis bodies used to regenerate published pages.
- `catalog.json`: enumerated video metadata, including videos not yet imported.
- `raw/manifest.json`: successfully imported videos, hashes, and failed attempts.

Every non-reserved Markdown file has YAML frontmatter with a nonempty `type`.
The reserved files are `index.md` and `log.md`. Root `index.md` declares
`okf_version: "0.1"`. Each content directory has an `index.md`.

## Shared metadata

Authored pages carry `title`, `description`, `tags`, `created`, and `updated`.
Dates use `YYYY-MM-DD`. Concept and entity pages carry `videos`, a list of source
slugs. Entity pages also carry `subtype` and a canonical `resource` URL when known.

Source pages carry `youtube_id`, `url`, `slug`, `published`, `duration`, and a `raw`
relative path. `published` stays empty when no reliable date is available.
Raw pages carry `youtube_id`, `url`, `slug`, `provider`, `fetched_at`, and
`immutable: true`. `raw/manifest.json` records a SHA-256 hash of every imported file.

## Evidence

Read the complete transcript before writing its extraction. Never infer teachings,
quotes, dates, or timestamps from video titles. Keep the speaker's claims distinct
from independently verified facts. Flag contradictions with links to both sources.

A source page has a summary, `## Concepts covered`, `## Entities`, `## Key moments`,
and `## Transcript`. Key moments link directly to the video with `&t=<seconds>s`.

Every concept and entity ends with `## Sources`. Use a source-page link followed
by an exact quote from one timestamped paragraph in its raw transcript:

```markdown
- [Video title](../sources/video-slug.md) - "[0:01:23] Exact words from the transcript."
```

Entity citations use `../../sources/`. Preserve the quoted words exactly, allowing
only whitespace normalization. Use the timestamp at the start of the paragraph
that contains the quote. The quote validator rejects paraphrases inside quotes.

## Synthesis and relationships

Create one canonical page per concept. Merge duplicate names before writing.
A topic earns a page when it recurs across videos or receives a substantial
deep dive. A page synthesizes all imported videos that substantively discuss it.

Links are ordinary relative Markdown paths. Use relationship headings such as
`## Builds on`, `## Contrasts with`, `## Tools`, `## Related`, and `## Sources`.
Add reciprocal links between related knowledge pages and their video summaries.
Avoid unsupported stubs and wiki-style double-bracket links.

## Validation

`python3 lint.py` checks frontmatter, links, index coverage, source/raw parity,
and orphan pages. `python3 scripts/validate.py` checks the saved catalog, channel
membership, transcript hashes, and exact citation text. Its `--require-complete`
option also requires every catalog video to have a transcript and summary, plus
at least one concept page. When a canonical manifest exists, its entire set of
concept and entity pages must match the published pages. Structural validity
does not establish semantic quality.
