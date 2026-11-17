---
type: overview
title: "Import and synthesize channel videos"
description: "Resume transcript import and build cited knowledge pages."
---

# Import and synthesize channel videos

1. Read [the schema](../SCHEMA.md) and [build status](../status.md).
2. Run `python3 scripts/refresh_catalog.py` to discover uploads in the Videos tab.
3. Run `python3 scripts/fetch_transcripts.py --provider yt-dlp --limit 1` to test caption access.
4. If YouTube blocks the server, supply `SUPADATA_API_KEY` through the process environment and run `python3 scripts/fetch_transcripts.py --provider supadata`.
5. Check `raw/manifest.json` for import failures. Rerun the importer to resume.
6. Follow the [upstream pipeline guide](../.claude/references/pipeline-guide.md) for extraction, canonicalization, and writing.
7. Save one extraction JSON per raw transcript under `scripts/extractions/`. Read each full transcript and copy timestamped quotes exactly.
8. Record duplicate-name mappings and theme assignments in `scripts/canonicalization.json`. Run `python3 scripts/build_manifest.py` to verify extraction quotes and freeze `scripts/manifest.json` and `scripts/taxonomy.json`.
9. Run `python3 scripts/write_sources.py` to render the reviewed video summaries. Write reviewed synthesis bodies under `scripts/pages/concepts/<slug>.txt` and `scripts/pages/entities/<kind>/<slug>.txt`. Run `python3 scripts/write_pages.py` to publish metadata, reciprocal topic links, and exact citations from the manifest.
10. Run `python3 scripts/build_indexes.py` and `python3 scripts/update_status.py`.
11. Run `python3 lint.py` and `python3 scripts/validate.py`. Resolve every error and warning.
12. Run `python3 scripts/validate.py --require-complete` before describing the channel corpus as complete.

The saved catalog currently includes a 63-second announcement in the Videos tab.
Tab membership defines scope; the importer does not silently apply a duration cutoff.
Shorts and the separate Streams tab are excluded. Deleted, private, and unlisted
videos unavailable in the public tab are outside the discovered catalog.

The three original import skills remain under `.claude/skills/` for portability.
Their generic importers do not provide this project's checkpoints and raw-file
hashes. Use `scripts/fetch_transcripts.py` for routine imports here.
