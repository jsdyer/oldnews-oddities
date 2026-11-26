#!/usr/bin/env python3
"""Retain a small real LoC page-search shelf; all topics are editable in config."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urlsplit
from loc_http import read_loc
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.loc.gov/collections/chronicling-america/'

def validate_config(c):
    if not isinstance(c, dict) or c.get('schemaVersion') != 1 or not isinstance(c.get('topics'), list) or not c['topics']:
        raise ValueError('config needs one or more topics')
    if not isinstance(c.get('pageSize'), int) or not 1 <= c['pageSize'] <= 80:
        raise ValueError('pageSize must be 1–80')
    if not isinstance(c.get('requestTimeoutSeconds'), int) or not 10 <= c['requestTimeoutSeconds'] <= 120:
        raise ValueError('request timeout must be 10–120 seconds')
    if not isinstance(c.get('minimumRequestIntervalSeconds'), (int,float)) or c['minimumRequestIntervalSeconds'] < 4:
        raise ValueError('leave at least four seconds between requests')
    ids=[]
    for t in c['topics']:
        if not all(isinstance(t.get(k), str) and t[k].strip() for k in ('id','label','query','description')):
            raise ValueError('topic needs id, label, query and description')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', t['id']) or t['id'] in ids:
            raise ValueError('topic IDs must be unique slugs')
        if t.get('operator') not in ('PHRASE','AND','OR') or not 1600 <= t.get('fromYear',0) <= t.get('toYear',0) <= 2100:
            raise ValueError('invalid operator or year range')
        ids.append(t['id'])
    return c

def source_url(topic, count):
    return BASE + '?' + urlencode({'fo':'json','c':count,'sp':1,'st':'gallery','dl':'page','searchType':'advanced','qs':topic['query'],'ops':topic['operator'],'start_date':f"{topic['fromYear']}-01-01",'end_date':f"{topic['toYear']}-12-31"})

def safe_url(v, images=False):
    if not isinstance(v,str): return None
    if v.startswith('http://www.loc.gov/'): v='https://'+v[7:]
    p=urlsplit(v)
    allowed=('www.loc.gov','loc.gov','tile.loc.gov') if images else ('www.loc.gov','loc.gov')
    return v if p.scheme=='https' and p.hostname in allowed and not p.username else None

def normalize(item):
    url=safe_url(item.get('url'))
    date=item.get('date','')
    if not url or '/resource/' not in url or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date): return None
    images=[safe_url(x,True) for x in item.get('image_url',[]) if '/image-services/' in x and '.jpg' in x]
    descriptions=item.get('description',[])
    return {'id':item.get('page_id') or url,'title':item.get('title','Untitled newspaper page'),'date':date,'url':url,'image':images[0] if images else None,'paper':next(iter(item.get('partof_title',[])),''),'city':next(iter(item.get('location_city',[])),''),'state':next(iter(item.get('location_state',[])),''),'language':item.get('language',[]),'ocrExcerpt':' '.join(descriptions)[:900],'lccn':next(iter(item.get('number_lccn',[])),''),'page':str(int(next(iter(item.get('number_page',['0'])),0))) or ''}

def normalize_response(data):
    if not isinstance(data,dict) or not isinstance(data.get('results'),list) or not isinstance(data.get('pagination'),dict): raise ValueError('Unexpected LoC response')
    records=[]; seen=set()
    for raw in data['results']:
        record=normalize(raw)
        if record and record['id'] not in seen: records.append(record);seen.add(record['id'])
    if data['results'] and not records: raise ValueError('Response contained no usable newspaper page records')
    total=data['pagination'].get('of',len(records))
    if not isinstance(total,int) or total<0: raise ValueError('Invalid total')
    return records,total

def collect(root=ROOT, if_changed=False):
    config_bytes=(root/'web/config.json').read_bytes()
    config=validate_config(json.loads(config_bytes)); digest=hashlib.sha256(config_bytes).hexdigest()
    dest=root/'web/data/shelf.json'
    if if_changed and dest.exists() and json.loads(dest.read_text()).get('configSha256')==digest:
        print('Configuration unchanged; retaining current shelf.');return
    captured=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    topics=[]
    for i,t in enumerate(config['topics']):
        if i: time.sleep(max(4,config.get('minimumRequestIntervalSeconds',4)))
        url=source_url(t,config['pageSize']); print('Collecting '+t['id'],flush=True)
        raw=read_loc(url,timeout=config['requestTimeoutSeconds'],limit=12_000_000,default_agent='CoolCode OldNewsOddities/1.0 (+https://coolcode.ca/oldnews-oddities/)')
        records,total=normalize_response(json.loads(raw))
        topics.append({'id':t['id'],'query':t['query'],'operator':t['operator'],'fromYear':t['fromYear'],'toYear':t['toYear'],'total':total,'records':records,'sourceUrl':url,'sourceSha256':hashlib.sha256(raw).hexdigest()})
        print(f'  {len(records)} pages; {total} search matches',flush=True)
    result={'schemaVersion':1,'capturedAt':captured,'configSha256':digest,'publisher':'Library of Congress / Chronicling America','topics':topics}
    dest.parent.mkdir(exist_ok=True)
    temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    print('Saved validated shelf.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--if-config-changed',action='store_true');args=parser.parse_args()
    collect(if_changed=args.if_config_changed)
