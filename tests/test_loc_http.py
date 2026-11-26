import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from loc_http import read_loc, NoRedirect, LOCRequestError
SECRET='test@example.invalid EXAMPLE_PRIVATE_HEADER_TOKEN'
URL='https://www.loc.gov/collections/chronicling-america/?fo=json'
class PrivateLOCTests(unittest.TestCase):
 def read(self,url=URL):return read_loc(url,timeout=12,limit=1000,default_agent='Public Collector/1.0')
 def test_private_value_is_sent_only_in_header(self):
  with patch.dict(os.environ,{'LOC_USER_AGENT':SECRET}),patch('loc_http._OPENER.open',return_value=io.BytesIO(b'{"results":[]}')) as opener:
   self.assertEqual(self.read(),b'{"results":[]}');req=opener.call_args.args[0];self.assertEqual(req.get_header('User-agent'),SECRET);self.assertNotIn(SECRET,req.full_url)
 def test_without_exemption_public_collector_still_works(self):
  with patch.dict(os.environ,{'LOC_USER_AGENT':''}),patch('loc_http._OPENER.open',return_value=io.BytesIO(b'{}')) as opener:
   self.read();self.assertEqual(opener.call_args.args[0].get_header('User-agent'),'Public Collector/1.0')
 def test_header_is_never_forwarded_to_other_hosts_or_redirects(self):
  for url in ['http://www.loc.gov/','https://www.loc.gov.evil.test/','https://tile.loc.gov/','https://user@loc.gov/','https://loc.gov:444/','https://example.invalid/']:
   with patch.dict(os.environ,{'LOC_USER_AGENT':SECRET}),patch('loc_http._OPENER.open') as opener:
    with self.assertRaises(LOCRequestError):self.read(url)
    opener.assert_not_called()
  for destination in ['https://www.loc.gov/other/','https://example.invalid/']:
   with self.assertRaises(LOCRequestError):NoRedirect().redirect_request(Request(URL),None,302,'Found',{},destination)
 def test_invalid_header_never_reaches_network_or_error_text(self):
  for value in [SECRET+'\nInjected: value','User-Agent: '+SECRET,'"'+SECRET+'"']:
   with patch.dict(os.environ,{'LOC_USER_AGENT':value}),patch('loc_http._OPENER.open') as opener:
    with self.assertRaises(LOCRequestError) as got:self.read()
    self.assertNotIn(SECRET,str(got.exception));opener.assert_not_called()
 def test_response_echo_and_error_details_do_not_escape(self):
  with patch.dict(os.environ,{'LOC_USER_AGENT':SECRET}):
   for raw in [json.dumps({'echo':SECRET}).encode(),json.dumps({'echo':SECRET.split()[-1]}).encode(),('\"'+''.join('\\u%04x'%ord(c) for c in SECRET.split()[-1])+'\"').encode()]:
    with patch('loc_http._OPENER.open',return_value=io.BytesIO(raw)):
     with self.assertRaises(LOCRequestError) as got:self.read()
     self.assertNotIn(SECRET.split()[-1],str(got.exception))
   for error in [HTTPError(URL,403,SECRET,{},None),URLError(SECRET)]:
    with patch('loc_http._OPENER.open',side_effect=error):
     with self.assertRaises(LOCRequestError) as got:self.read()
     self.assertNotIn(SECRET,str(got.exception));self.assertTrue(got.exception.__suppress_context__)
 def test_oversized_body_is_rejected(self):
  with patch.dict(os.environ,{'LOC_USER_AGENT':''}),patch('loc_http._OPENER.open',return_value=io.BytesIO(b'x'*1001)):
   with self.assertRaises(LOCRequestError):self.read()
