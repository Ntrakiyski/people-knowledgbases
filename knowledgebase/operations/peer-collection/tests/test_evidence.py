"""Behavior checks for exact evidence and missing archive coverage."""
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from render import locate_quote
from validate import validate


class EvidenceTests(unittest.TestCase):
    def test_quote_restores_source_case_and_whitespace(self):
        text = 'Intro. A REAL customer\nvalues steady service over flashy promises. End.'
        result = locate_quote(text, 'a real customer values steady service over flashy promises.')
        self.assertIsNotNone(result)
        quote, start, end = result
        self.assertEqual(quote, 'A REAL customer\nvalues steady service over flashy promises.')
        self.assertEqual(text[start:end], quote)

    def test_quote_rejects_changed_meaning_and_punctuation(self):
        text = 'Risk is real and business ownership never guarantees future cash flow.'
        self.assertIsNone(locate_quote(text, 'Risk is real and business ownership guarantees future cash flow.'))
        self.assertIsNone(locate_quote(text, 'Risk is real, and business ownership never guarantees future cash flow.'))

    def test_pending_archive_passes_integrity_but_fails_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            creator = root / 'test-creator'
            for name in ['raw', 'sources']:
                (creator / name).mkdir(parents=True, exist_ok=True)
            (creator / 'channel.json').write_text(json.dumps({'channel_id': 'channel-1'}))
            (creator / 'catalog.json').write_text(json.dumps({'channel_id': 'channel-1', 'total_videos': 1, 'videos': [{'youtube_id': 'video-1'}]}))
            (creator / 'raw/manifest.json').write_text(json.dumps({'videos': [], 'transcripts_fetched': 0}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate(root), [])
                errors = validate(root, require_complete=True)
            self.assertIn('Selected scope incomplete: test-creator', errors)
            self.assertIn('Reviewed synthesis incomplete: test-creator', errors)

    def test_tampered_transcript_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            creator = root / 'test-creator'
            for name in ['raw', 'sources']:
                (creator / name).mkdir(parents=True, exist_ok=True)
            (creator / 'channel.json').write_text(json.dumps({'channel_id': 'channel-1'}))
            (creator / 'catalog.json').write_text(json.dumps({'channel_id': 'channel-1', 'total_videos': 1, 'videos': [{'youtube_id': 'video-1'}]}))
            text = '---\ntype: raw-transcript\nyoutube_id: "video-1"\nimmutable: true\n---\n\n## Transcript\n\nOriginal text.\n'
            path = creator / 'raw/video-1.md'
            path.write_text(text.replace('Original', 'Changed'))
            (creator / 'raw/manifest.json').write_text(json.dumps({'transcripts_fetched': 1, 'videos': [{'youtube_id': 'video-1', 'sha256': hashlib.sha256(text.encode()).hexdigest()}]}))
            with contextlib.redirect_stdout(io.StringIO()):
                errors = validate(root)
            self.assertIn('Transcript hash mismatch: test-creator/video-1', errors)

    def test_selected_completion_does_not_require_optional_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            creator = root / 'test-creator'
            for name in ['raw', 'sources', 'scripts/extractions']:
                (creator / name).mkdir(parents=True, exist_ok=True)
            (root / 'analysis').mkdir()
            (creator / 'channel.json').write_text(json.dumps({'channel_id': 'channel-1'}))
            (creator / 'catalog.json').write_text(json.dumps({'channel_id': 'channel-1', 'total_videos': 2, 'videos': [{'youtube_id': 'video-1'}, {'youtube_id': 'older-video'}]}))
            (creator / 'selection.json').write_text(json.dumps({'videos': ['video-1']}))
            quote = 'A careful buyer checks cash flow before signing any binding business agreement.'
            raw = '---\ntype: raw-transcript\nyoutube_id: "video-1"\nimmutable: true\n---\n\n## Transcript\n\n' + quote + '\n'
            (creator / 'raw/video-1.md').write_text(raw)
            digest = hashlib.sha256(raw.encode()).hexdigest()
            (creator / 'raw/manifest.json').write_text(json.dumps({'transcripts_fetched': 1, 'videos': [{'youtube_id': 'video-1', 'sha256': digest}]}))
            (creator / 'sources/video-1.md').write_text('---\ntype: source\n---\n\nA cited source note.\n')
            (creator / 'scripts/extractions/video-1.json').write_text(json.dumps({'thesis': 'Check before signing.', 'summary': 'A buyer checks cash flow.', 'insights': [{'slug': 'due-diligence', 'quote': quote}]}))
            (creator / 'review.json').write_text(json.dumps({'cross_video_synthesis_complete': True, 'entity_synthesis_complete': True}))
            insight = {'id': 'test-creator:video-1:due-diligence:' + hashlib.sha256(quote.encode()).hexdigest()[:10], 'creator_slug': 'test-creator', 'youtube_id': 'video-1', 'character_start': 0, 'character_end': len(quote), 'quote': quote, 'timestamp_seconds': None, 'provider': 'local', 'raw_sha256': digest}
            (root / 'analysis/insights.jsonl').write_text(json.dumps(insight) + '\n')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate(root, require_complete=True), [])
                archive_errors = validate(root, require_full_archive=True)
            self.assertIn('Archive incomplete: test-creator', archive_errors)


if __name__ == '__main__':
    unittest.main()
