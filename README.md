# People knowledge bases

Evidence-backed research on Sharran Srivatsaa, Alex Hormozi, Codie Sanchez, Dan Martell, Nick Huber and Sahil Bloom.

The repository has two main folders:

- [`.agents/skills/`](.agents/skills/): skills to create, update, research and refresh the collections.
- [`knowledgebase/`](knowledgebase/README.md): all six people's collections, source evidence, analysis, datasets and maintenance scripts.

The original snapshot contains 240 YouTube transcripts: 40 Sharran videos plus 40 videos for each of five related creators. In the five-creator collection, 136 of 200 source notes have complete-transcript readings and 64 retain NotebookLM drafts. The 99-source deeper pass is complete. Source wording is checked; creator claims are not independently verified. X account links do not mean X posts were imported.

## Use the skills

Open this repository in an agent that supports project skills under `.agents/skills/`:

- `$knowledgebase-create` — create a collection for another person, confirm identity and define the initial source scope.
- `$knowledgebase-update` — add supplied material or deepen an existing review and update relevant synthesis.
- `$knowledgebase-use` — answer questions, compare teachings, or build an evidence-backed research brief.
- `$knowledgebase-refresh` — check registered social accounts, collect new accessible material, review it and update the collection.

For example: “Use $knowledgebase-use to compare their advice on delegation. Cite the videos, explain the conditions and preserve disagreements.”

The refresh skill can be invoked manually or by a scheduler calling an agent. This repository does not install a recurring job. YouTube metadata discovery uses `yt-dlp`; caption collection can use it, Supadata or an authenticated NotebookLM session. X requires a working authenticated connector/API or a user-supplied export. Missing access must be reported.

Read the [knowledge-base guide](knowledgebase/README.md) for navigation and the [maintenance contract](knowledgebase/MAINTENANCE.md) for commands, source formats and validation.
