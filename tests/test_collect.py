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
        self.assertEqual([t['id'] for t in shelf['topics']],[t['id'] for t in self.config['topics']])
        for t in shelf['topics']:
            self.assertEqual(len(t['sourceSha256']),64)
            self.assertTrue(t['records'])
