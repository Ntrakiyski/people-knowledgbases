---
type: overview
title: "Project provenance"
description: "Source channel, upstream template, and reuse boundaries."
---

# Project provenance

The source is [Sharran Srivatsaa](https://www.youtube.com/channel/UCzpl_gT1bVB1iNZl9yQbWuA),
handle `@sharran`, channel ID `UCzpl_gT1bVB1iNZl9yQbWuA`. The channel identity was
verified from YouTube channel metadata on 2026-11-16. The Videos tab returned
40 uploads. [catalog.json](../catalog.json) records the enumeration and scope.

The project derives its Markdown layout, OKF 0.1 conventions, linter, index
builder, and three import skills from
[coleam00/cole-medin-knowledge-base](https://github.com/coleam00/cole-medin-knowledge-base)
at commit `eba5e31bc628280c546d4828491051c308d550dc`. Git history preserves
the upstream state, and the `upstream` remote points to that repository.

The working corpus excludes the template's Cole Medin transcripts and synthesized
pages. Newly imported transcripts retain source-video URLs and timestamped text.
Raw-file hashes record import integrity. All 40 catalog transcripts were imported
through Supadata's native-caption mode on 2026-11-16. No NotebookLM fallback was needed.

## Synthesis

The saved extraction checkpoints were canonicalized into 76 concepts and 45
named subjects, then used to write 40 video summaries and the linked knowledge
pages. Related subtopics share a parent page where they explain one coherent
process; the alias map preserves the original extraction names. The manifest
retains each contributing video's explanation and exact supporting quotes.

The wiki records the speaker's teachings and anecdotes. It does not independently
verify reported deal terms, returns, historical figures, or tax outcomes.
Contradictory numerical examples and differing descriptions of family investing
remain attributed rather than silently reconciled. Native captions contain
recognition errors: canonical names may be normalized while quotations and raw
transcripts preserve the imported wording. Unknown publication dates stay empty.

The upstream repository has no root license file at the referenced commit.
Attribution does not grant additional rights to its code or the videos. This
project adds no license for upstream material. No public repository or deployment
has been created as part of this setup.
