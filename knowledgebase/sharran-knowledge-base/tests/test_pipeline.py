"""Exercise checkpoint recovery, access failures, and citation validation."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ("raw", "sources", "concepts", "entities"):
            (self.root / directory).mkdir()
        self.video = {"youtube_id": "abcdefghijk", "title": "Evidence test",
                      "url": "https://www.youtube.com/watch?v=abcdefghijk",
                      "slug": "evidence-test-abcdefghijk", "duration_seconds": 120}
        self.save("channel.json", {"channel_id": "UCtest"})
        self.save("catalog.json", {"channel_id": "UCtest", "total_videos": 1,
                                    "videos": [self.video]})
        self.save("raw/manifest.json", {"total_videos": 1, "transcripts_fetched": 0,
                                        "videos": [], "failed_videos": []})
        self.fetch = load("fetch_transcripts")
        self.fetch.ROOT = self.root
        self.validator = load("validate")
        self.validator.ROOT = self.root

    def save(self, path, data):
        (self.root / path).write_text(json.dumps(data))

    def run_import(self, provider):
        with patch.dict(os.environ, {"SUPADATA_API_KEY": "test-only-key"}), \
             patch("sys.argv", ["fetch_transcripts.py", "--provider", "supadata", "--delay", "0"]), \
             patch.object(self.fetch, "supadata", side_effect=provider), \
             contextlib.redirect_stdout(io.StringIO()):
            return self.fetch.main()

    def test_import_writes_timestamped_evidence_and_skips_it_on_resume(self):
        segments = [{"start": 12, "text": "Cash flow funds the next investment."}]
        self.assertEqual(self.run_import(lambda *_: segments), 0)
        target = self.root / "raw" / f"{self.video['slug']}.md"
        before = target.read_bytes()
        self.assertIn(b"**[0:00:12]** Cash flow funds the next investment.", before)
        manifest = json.loads((self.root / "raw/manifest.json").read_text())
        self.assertEqual(manifest["videos"][0]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(self.run_import(lambda *_: self.fail("Imported video was fetched again")), 0)
        self.assertEqual(target.read_bytes(), before)

    def test_access_error_is_not_recorded_as_missing_captions_and_can_resume(self):
        def blocked(*_):
            raise RuntimeError("Supadata HTTP 429")
        self.assertEqual(self.run_import(blocked), 1)
        manifest = json.loads((self.root / "raw/manifest.json").read_text())
        self.assertEqual(manifest["transcripts_fetched"], 0)
        self.assertEqual(manifest["failed_videos"][0]["reason"], "Supadata HTTP 429")
        self.assertEqual(list((self.root / "raw").glob("*.md")), [])
        self.assertEqual(self.run_import(lambda *_: [{"start": 0, "text": "Recovered caption."}]), 0)
        manifest = json.loads((self.root / "raw/manifest.json").read_text())
        self.assertEqual(manifest["transcripts_fetched"], 1)
        self.assertEqual(manifest["failed_videos"], [])

    def test_validator_rejects_modified_raw_invented_quotes_and_missing_pages(self):
        self.run_import(lambda *_: [{"start": 12, "text": "Cash flow funds the next investment."}])
        slug = self.video["slug"]
        (self.root / "sources" / f"{slug}.md").write_text(
            '---\ntype: source\nyoutube_id: "abcdefghijk"\n---\n'
            '## Concepts covered\n\n## Entities\n\n## Key moments\n\n## Transcript\n')
        concept = self.root / "concepts/cash-flow.md"
        prefix = '---\ntype: concept\n---\n\n## Sources\n\n'
        citation = f'- [Evidence test](../sources/{slug}.md) - "[0:00:12] '
        concept.write_text(prefix + citation + 'Cash flow funds the next investment."\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.validator.validate(require_complete=True), [])
            (self.root / "scripts").mkdir()
            self.save("scripts/manifest.json", {"concepts": [{"slug": "cash-flow"},
                                                          {"slug": "missing-topic"}],
                                                "entities": []})
            incomplete = self.validator.validate(require_complete=True)
            self.assertIn("Canonical page is missing: concepts/missing-topic.md", incomplete)
            self.assertIn("Channel corpus is incomplete", incomplete)
            (self.root / "scripts/manifest.json").unlink()
            concept.write_text(prefix + citation + 'An invented quote about guaranteed returns."\n')
            self.assertTrue(any("Quote not found" in error for error in self.validator.validate()))
            target = self.root / "raw" / f"{slug}.md"
            target.write_text(target.read_text() + "\nChanged evidence.\n")
            self.assertTrue(any("hash mismatch" in error for error in self.validator.validate()))

    def test_incomplete_corpus_fails_release_check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIn("Channel corpus is incomplete", self.validator.validate(require_complete=True))


if __name__ == "__main__":
    unittest.main()
