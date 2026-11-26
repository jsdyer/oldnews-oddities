"""One read of the deployed public route, then page 2 after a successful page 1."""
import json
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

class Manual(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None
opener = build_opener(Manual())
def get_page(page):
    params = dict(c='12',sp=str(page),st='gallery',dl='page',searchType='advanced',qs='halifax',ops='PHRASE',start_date='1800-01-01',end_date='1930-12-31',fo='json',at='results,pagination')
    url = 'https://coolcode-visitor-api.jeffdyer.workers.dev/api/newspapers/search?'+urlencode(params)
    try:
        reply = opener.open(Request(url,headers={'Origin':'https://coolcode.ca','Accept':'application/json'}),timeout=90)
    except HTTPError as err:
        reply = err
    with reply:
        cors=reply.headers.get('access-control-allow-origin')
        raw=reply.read(2500000)
        try:
            body=json.loads(raw)
        except ValueError:
            body={}
        err=body.get('error',{})
        code=err.get('code') if isinstance(err,dict) else None
        if not code: code=body.get('error_code')
        print('page',page,'HTTP',reply.status,'CORS',cors,'public error code',code,'retry',reply.headers.get('Retry-After'),flush=True)
        if reply.status!=200 or cors!='https://coolcode.ca':
            return None,False
    data=body['data']; pagination=data['pagination']
    rows=data['results']
    assert pagination['current']==page and pagination['perpage']==12 and rows
    links=[]
    for row in rows:
        href=row.get('url') or row.get('id') or ''
        parsed=urlsplit(href)
        assert parsed.scheme in {'http','https'} and parsed.hostname in {'loc.gov','www.loc.gov'} and parsed.path.startswith(('/resource/','/item/'))
        assert row['date'] and row['title']
        links.append(href)
    print('returned',len(rows),'available',pagination['of'],'next',bool(pagination['next']),'captured',body['fetched_at'],'example',rows[0]['date'],rows[0]['title'][:125],links[0],flush=True)
    return links,pagination['next']
if __name__=='__main__':
    first,more=get_page(1)
    if not first:
        raise SystemExit('The public Worker did not serve the first page. No further request was made.')
    if more:
        time.sleep(6)
        second,_=get_page(2)
        if not second:
            raise SystemExit('Page two did not return source-linked records.')
        print('distinct new records on page 2',len(set(second)-set(first)))
        assert set(second)-set(first)
