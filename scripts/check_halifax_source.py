"""Check two encodings of one public query. Report only status and counts."""
import json
import os
import time
from urllib.parse import urlencode
from loc_http import read_loc, LOCRequestError


def check(label, params):
    url = 'https://www.loc.gov/collections/chronicling-america/?' + urlencode(params)
    try:
        blob = read_loc(url, timeout=85, limit=8_000_000, default_agent='CoolCode archive search')
        data = json.loads(blob)
        count = len(data['results'])
        total = data['pagination']['of']
        print(f'{label}: HTTP 200; {count} returned pages; {int(total)} matches', flush=True)
        return count > 0
    except LOCRequestError as error:
        print(f'{label}: {error}',flush=True)
        return False


if not os.environ.get('LOC_USER_AGENT'):
    raise SystemExit('The Actions secret is missing.')
values = dict(c='12', sp='1', st='gallery', dl='page', searchType='advanced', qs='halifax',
              ops='PHRASE', start_date='1800-01-01', end_date='1930-12-31', fo='json', at='results,pagination')
result = check('Original browser order', values)
time.sleep(5)
keys = ['dl', 'searchType', 'fo', 'at', 'qs', 'ops', 'c', 'sp', 'start_date', 'end_date', 'st']
gateway_result = check('Worker order', {key:values[key] for key in keys})
if not (result and gateway_result):
    raise SystemExit('One or more official source requests failed.')
