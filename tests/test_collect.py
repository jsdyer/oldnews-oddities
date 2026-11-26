import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect import ROOT, validate_config, normalize_response, source_url, safe_url

class CollectorTests(unittest.TestCase):
    def setUp(self): self.config=json.loads((ROOT/'web/config.json').read_text())
    def test_adding_a_topic_requires_no_application_change(self):
        topic=copy.deepcopy(self.config['topics'][0]);topic.update(id='another-topic',query='mechanical man')
        self.config['topics'].append(topic)
        self.assertEqual(len(validate_config(self.config)['topics']),len(json.loads((ROOT/'web/config.json').read_text())['topics'])+1)
        self.assertIn('mechanical+man',source_url(topic,12))
    def test_duplicate_topic_rejected(self):
        self.config['topics'].append(self.config['topics'][0])
        with self.assertRaises(ValueError): validate_config(self.config)
    def test_rate_limit_and_invalid_dates_rejected(self):
        self.config['minimumRequestIntervalSeconds']=0
        with self.assertRaises(ValueError): validate_config(self.config)
        self.config['minimumRequestIntervalSeconds']=4
        self.config['topics'][0]['fromYear']=2050
        with self.assertRaises(ValueError): validate_config(self.config)
    def test_provider_empty_and_malformed_are_distinct(self):
        self.assertEqual(normalize_response({'results':[],'pagination':{'of':0}}),([],0))
        with self.assertRaises(ValueError): normalize_response({'error':'temporarily unavailable'})
    def test_unsafe_sources_excluded(self):
        self.assertIsNone(safe_url('https://www.loc.gov.evil.test/resource/a'))
        self.assertIsNone(safe_url('javascript:alert(1)'))
    def test_capture_covers_current_config(self):
        shelf=json.loads((ROOT/'web/data/shelf.json').read_text())
        configured=[t['id'] for t in self.config['topics']]
        watchlist=[t['id'] for t in json.loads((ROOT/'scripts/retained-watchlist.json').read_text())]
        retained=[t['id'] for t in shelf['topics']]
        self.assertEqual(retained[:len(configured)],configured)
        self.assertTrue(all(t in watchlist for t in retained[len(configured):]))
        for t in shelf['topics']:
            self.assertEqual(len(t['sourceSha256']),64)
            self.assertTrue(t['records'])

    def test_failed_refresh_retains_previous_shelf(self):
        import tempfile
        from unittest.mock import patch
        from collect import collect
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'web/data').mkdir(parents=True);(root/'web/config.json').write_text(json.dumps(self.config));out=root/'web/data/shelf.json';out.write_text('{"old":"capture"}');before=out.read_bytes()
            with patch('collect.read_loc',side_effect=RuntimeError('LOC request failed')):
                with self.assertRaises(RuntimeError):collect(root)
            self.assertEqual(out.read_bytes(),before)
