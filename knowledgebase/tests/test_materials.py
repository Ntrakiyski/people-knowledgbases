"""Exercise discovery boundaries and actual intake/review results with local evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('materials', Path(__file__).resolve().parents[1] / 'scripts/materials.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MaterialsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        m.save(self.root / 'people.json', {'people': [{
            'slug': 'test-person', 'name': 'Test Person',
            'youtube': {'channel_id': 'UC-example', 'url': 'https://www.youtube.com/@example'},
            'x': {'url': 'https://x.com/example'}, 'baseline_catalog': 'baseline.json'}]})
        m.save(self.root / 'baseline.json', {'videos': [{'youtube_id': 'old'}]})
        (self.root / 'updates').mkdir()
        self.source = {'creator_slug': 'test-person', 'platform': 'youtube', 'source_id': 'new',
            'url': 'https://www.youtube.com/watch?v=new', 'title': 'Fixture only',
            'provider': 'local-fixture', 'attribution': 'Fictional test author',
            'text': 'A careful operator checks the original evidence before making a decision. A second sentence adds context.'}

    def review(self, quote='a careful operator checks the original evidence before making a decision.'):
        return {'review_scope': 'complete-source-read-by-agent', 'summary': 'A fixture about checking evidence.',
            'context_and_limits': 'Fictional fixture; not a creator claim.', 'insights': [{
                'title': 'Check evidence', 'explanation': 'The fixture recommends checking original evidence.',
                'quote': quote, 'speaker': 'Fictional test author', 'tags': ['evidence']}]}

    def test_new_discovery_stops_before_old_excluded_archive(self):
        entries = [{'id': key} for key in ['new', 'old', 'older-unselected']]
        found, anchored = m.select_new(entries, {'old', 'older-unselected'})
        self.assertEqual(found, [{'id': 'new'}])
        self.assertTrue(anchored)

    def test_discovery_gap_does_not_claim_coverage(self):
        found, anchored = m.select_new([{'id': 'new'}, {'id': 'new'}], {'old'})
        self.assertEqual(found, [{'id': 'new'}])
        self.assertFalse(anchored)

    def mock_discovery(self, ids, channel='UC-example', dry_run=False):
        result = SimpleNamespace(returncode=0, stdout=json.dumps({'channel_id': channel,
            'entries': [{'id': key, 'title': 'Title ' + key} for key in ids]}))
        with patch.object(m.subprocess, 'run', return_value=result):
            return m.discover(self.root, 'test-person', 100, dry_run)

    def test_repeated_discovery_keeps_captured_and_new_queue(self):
        report = self.mock_discovery(['new', 'old'])
        self.assertEqual(report['youtube'][0]['newly_queued'], 1)
        self.assertEqual(report['x'][0]['status'], 'adapter-required')
        m.ingest(self.root, self.source)
        self.mock_discovery(['newer', 'new', 'old'])
        items = {r['source_id']: r for r in m.catalog(self.root)['items']}
        self.assertEqual(items['new']['status'], 'captured')
        self.assertEqual(items['newer']['status'], 'discovered')
        self.assertNotIn('old', items)

    def test_gap_and_wrong_channel_do_not_advance_anchor(self):
        report = self.mock_discovery(['new'])
        self.assertEqual(report['youtube'][0]['status'], 'gap')
        self.assertNotIn('discovery_anchors', m.catalog(self.root))
        report = self.mock_discovery(['new', 'old'], channel='other')
        self.assertEqual(report['youtube'][0]['status'], 'blocked')
        self.assertNotIn('discovery_anchors', m.catalog(self.root))

    def test_dry_run_leaves_no_queue_or_run_files(self):
        report = self.mock_discovery(['new', 'old'], dry_run=True)
        self.assertEqual(report['youtube'][0]['status'], 'checked')
        self.assertEqual(list((self.root / 'updates').iterdir()), [])

    def test_reimport_is_idempotent_and_changed_evidence_rejected(self):
        folder = m.ingest(self.root, self.source)
        original = (folder / 'raw.json').read_bytes()
        m.ingest(self.root, dict(self.source, captured_at='2099-01-01T00:00:00Z'))
        self.assertEqual((folder / 'raw.json').read_bytes(), original)
        self.assertEqual(len(m.catalog(self.root)['items']), 1)
        with self.assertRaisesRegex(ValueError, 'immutable original'):
            m.ingest(self.root, dict(self.source, text='Changed text that must not overwrite the original.'))
        self.assertEqual((folder / 'raw.json').read_bytes(), original)

    def test_review_publishes_exact_wording_offsets_and_scope(self):
        folder = m.ingest(self.root, self.source)
        m.review_source(self.root, self.source, self.review())
        result = m.read(folder / 'review.json')
        insight = result['insights'][0]
        self.assertEqual(self.source['text'][insight['character_start']:insight['character_end']], insight['quote'])
        self.assertTrue(insight['quote'].startswith('A careful'))
        self.assertIn('complete-source-read-by-agent', (folder / 'source.md').read_text())
        self.assertIn('Fictional test author', (folder / 'source.md').read_text())
        self.assertEqual(m.validate(self.root), [])

    def test_fabricated_quote_is_rejected_before_review_is_saved(self):
        folder = m.ingest(self.root, self.source)
        with self.assertRaisesRegex(ValueError, 'Quotation not present'):
            m.review_source(self.root, self.source, self.review('This made up quotation never occurred in the source.'))
        self.assertFalse((folder / 'review.json').exists())
        self.assertEqual(m.catalog(self.root)['items'][0]['status'], 'captured')

    def test_review_revision_archives_prior_content(self):
        folder = m.ingest(self.root, self.source)
        m.review_source(self.root, self.source, self.review())
        prior = (folder / 'review.json').read_bytes()
        review = self.review(); review['summary'] = 'Revised interpretation of the same original evidence.'
        m.review_source(self.root, self.source, review)
        archive = folder / 'history' / (m.digest(prior) + '.json')
        self.assertEqual(archive.read_bytes(), prior)
        self.assertEqual(m.read(folder / 'review.json')['summary'], review['summary'])

    def test_tampering_with_original_is_detected(self):
        folder = m.ingest(self.root, self.source)
        raw = m.read(folder / 'raw.json'); raw['text'] += ' Changed.'
        m.save(folder / 'raw.json', raw)
        self.assertTrue(any('source text changed' in error for error in m.validate(self.root)))

    def test_invalid_identity_and_mismatched_canonical_url_are_rejected(self):
        for fields in [{'source_id': '../escape'}, {'url': 'https://www.youtube.com/watch?v=other'}, {'creator_slug': 'unregistered'}]:
            with self.assertRaises(ValueError):
                m.ingest(self.root, dict(self.source, **fields))
        self.assertFalse((self.root / 'updates/catalog.json').exists())

    def test_queue_does_not_downgrade_review_and_rebuild_has_source_link(self):
        folder = m.ingest(self.root, self.source)
        m.review_source(self.root, self.source, self.review())
        m.queue(self.root, self.source)
        m.rebuild(self.root)
        self.assertEqual(m.catalog(self.root)['items'][0]['status'], 'reviewed')
        self.assertIn('materials/test-person/youtube/new/source.md', (self.root / 'updates/index.md').read_text())
        self.assertEqual(m.validate(self.root), [])

    def test_caption_capture_preserves_native_segments_and_skips_duplicate_download(self):
        backend = self.root / 'sharran-knowledge-base/scripts/fetch_transcripts.py'
        backend.parent.mkdir(parents=True)
        backend.write_text("def ytdlp(video_id):\n    return [{'start': 0.0, 'text': 'This fixture has enough words to support a quoted insight.'}]\n")
        m.queue(self.root, self.source)
        folder = m.capture(self.root, 'test-person', 'new', 'auto')
        raw = m.read(folder / 'raw.json')
        self.assertEqual(raw['provider'], 'yt-dlp-captions')
        self.assertEqual(raw['text'], raw['native_segments'][0]['text'])
        self.assertEqual(raw['native_segments'][0]['start'], 0.0)
        backend.write_text("raise RuntimeError('No second download should occur')\n")
        self.assertEqual(m.capture(self.root, 'test-person', 'new', 'auto'), folder)
        self.assertEqual(m.validate(self.root), [])

    def test_blocked_caption_access_keeps_the_source_pending(self):
        backend = self.root / 'sharran-knowledge-base/scripts/fetch_transcripts.py'
        backend.parent.mkdir(parents=True)
        backend.write_text("def ytdlp(video_id):\n    raise RuntimeError('Access blocked')\n")
        m.queue(self.root, self.source)
        with patch.dict(m.os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'source remains pending'):
                m.capture(self.root, 'test-person', 'new', 'auto')
        self.assertEqual(m.catalog(self.root)['items'][0]['status'], 'discovered')
        self.assertFalse((m.folder_for(self.root, self.source) / 'raw.json').exists())


if __name__ == '__main__':
    unittest.main()
