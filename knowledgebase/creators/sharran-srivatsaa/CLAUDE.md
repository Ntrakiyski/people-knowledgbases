---
type: overview
title: "Agent instructions"
description: "How agents navigate and maintain the Sharran Srivatsaa knowledge base."
---

# Agent instructions

Read [index.md](index.md), [SCHEMA.md](SCHEMA.md), and [status.md](status.md) first.
This project covers Sharran Srivatsaa's channel, not the template author's channel.

Open only pages relevant to the question. Cite the knowledge page and source
video with a timestamp. Check quotes against raw transcripts. If evidence is
missing, say the topic is not covered.

For ingestion, follow [the workflow](docs/ingestion-workflow.md). Save extraction
checkpoints, canonicalize before writing, and never overwrite raw transcripts.
Rerun the index builders and validators after changes. Keep coverage claims tied
to the actual catalog and files. Never commit credentials or session cookies.
