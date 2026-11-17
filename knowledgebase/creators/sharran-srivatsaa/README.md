---
type: overview
title: "Sharran Srivatsaa knowledge base"
description: "A channel-specific OKF wiki based on the Cole Medin knowledge-base pipeline."
---

# Sharran Srivatsaa knowledge base

A Markdown knowledge base for [Sharran Srivatsaa's YouTube channel](https://www.youtube.com/channel/UCzpl_gT1bVB1iNZl9yQbWuA),
built with the structure and import skills from
[coleam00/cole-medin-knowledge-base](https://github.com/coleam00/cole-medin-knowledge-base).

Start at [index.md](index.md). [Build status](status.md) reports actual coverage.
The [catalog](catalog.md) contains 40 discovered uploads, all imported as timestamped
English transcripts through Supadata. Knowledge pages are synthesized from those
transcripts. The original Cole Medin corpus has been removed from this branch.

The initial build contains 40 video summaries, 76 canonical concept pages, and
45 pages for people, organizations, and products. Browse by topic from the root
index, or follow a page's sources through to the timestamped transcript.
Coverage is the public Videos tab enumerated on 2026-11-16; Shorts and the
separate Streams tab are outside this catalog.

The intended output is a linked wiki of concepts, entities, and video summaries,
with immutable timestamped transcripts as evidence. It requires no database,
embeddings, or API key to read. A Supadata key is an optional import credential
when YouTube blocks free caption downloads.

## Import transcripts

Requirements: Python 3.10+ and `yt-dlp`. Run commands from this project directory.

```bash
python3 scripts/refresh_catalog.py
python3 scripts/fetch_transcripts.py --provider yt-dlp
```

For the managed provider, load `SUPADATA_API_KEY` into the process environment
through your secret manager, then run:

```bash
python3 scripts/fetch_transcripts.py --provider supadata
```

The importer checkpoints after each video. Rerunning skips imported videos and
retries pending ones. Access and rate-limit errors stop the run without discarding
progress. Supadata uses native captions; it does not request AI transcription.

After import, follow the [ingestion guide](docs/ingestion-workflow.md) to synthesize
the knowledge pages. Transcript import alone does not produce a completed wiki.

## Rebuild and validate

```bash
python3 scripts/build_indexes.py
python3 scripts/update_status.py
python3 lint.py
python3 scripts/validate.py
```

The first validator checks Markdown structure. The second checks corpus membership,
raw-file hashes, and exact quotes at cited timestamps. It reports incomplete
coverage. To require every catalog video to be imported and summarized, run:

```bash
python3 scripts/validate.py --require-complete
```

To reproduce the published wiki from saved extraction and synthesis files:

```bash
python3 scripts/build_manifest.py
python3 scripts/write_sources.py
python3 scripts/write_pages.py
python3 scripts/build_indexes.py
python3 scripts/update_status.py
```

Run importer and validator regression checks with `python3 -m unittest discover -s tests`.

## Use with an agent

```text
Read index.md and SCHEMA.md from the knowledgebase/creators/sharran-srivatsaa collection.
Check status.md for coverage. Navigate only the pages my question needs.
Answer from concepts, entities, and source summaries, and verify claims against
raw transcripts. Cite the source video and timestamp. Say when a question is
not covered. Do not treat video titles as evidence of what the speaker teaches.
```

See [provenance](docs/provenance.md) for channel scope and upstream attribution.
