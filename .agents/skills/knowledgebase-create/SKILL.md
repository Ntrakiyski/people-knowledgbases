---
name: knowledgebase-create
description: Create an evidence-backed collection for a new person in this repository, including confirmed social accounts, an initial material scope, cited source notes and a creator profile.
---

# Create a people knowledge base

Read [the repository guide](../../../knowledgebase/README.md) and [maintenance contract](../../../knowledgebase/MAINTENANCE.md). Resolve paths from the repository root, not from an old `/home` location. This workflow creates a person's collection; use `knowledgebase-update` for an existing person and `knowledgebase-refresh` for new-material discovery.

- Check `knowledgebase/people.json` for an existing identity. Confirm the person's official channel ID and any social accounts from first-party links; similar names and handles are insufficient. Preserve separate people even when they discuss the same ideas.
- Honor the requested source scope. For a request with no initial size, use the existing convention of the newest 40 public YouTube Videos-tab uploads, disclosing that bounded choice. Shorts, livestream tabs and an entire X archive are separate scope decisions. Do not silently include them.
- Create `knowledgebase/people/<slug>/` with `channel.json`, `catalog.json`, `selection.json`, `status.md`, `creator-profile.md` and `profile-notes.md`. Record the enumeration date, channel ID, stable material IDs and canonical URLs. Use null for unknown publication dates. Register the person with a relative `collection` path and `baseline_catalog` in `people.json`; retain unavailable social accounts as unconfigured rather than inventing them.
- Enumerate the initial list without modifying existing people's catalogs. Queue explicitly selected source metadata with `materials.py queue --input ...`, then capture and review through the incremental intake contract. A new person's initial selection needs explicit queueing because normal discovery deliberately skips baseline material.
- Read each complete captured source before declaring complete-source review. Write exact-quote insights, separate guest speech and retain context, commercial interests, counterexamples and limits. Pending captions or inaccessible accounts stay pending.
- Synthesize a profile only from captured evidence. Cover positioning, likely audience as inference, recurring frameworks, teaching style and tensions. Link the actual source notes. Catalog titles alone do not support beliefs, biography or recommendations.
- Record imported/reviewed counts honestly and run the applicable maintenance checks. Leave original snapshot bundles intact. Report collection location, achieved scope and access gaps. Creating a collection does not itself install a timer or authorize unrelated account changes.
