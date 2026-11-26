import test from 'node:test';
import assert from 'node:assert/strict';
import {findSavedPages} from '../web/saved-search.mjs';

const paper={url:'https://www.loc.gov/resource/paper/1915-02-03/ed-1/?sp=7&q=foo',title:'Newspaper page',date:'1915-02-03',state:'Maine',city:'Portland',newspaper:'Daily News',lccn:'sn12345678',excerpt:'Harbour officials met in Halifax after a lively debate.'};
const capture={capturedAt:'2026-10-01T00:00:00Z',query:{query:'wireless telegraph',operation:'PHRASE'},records:[paper]};
const testSearch=(query,operation='PHRASE',rest={})=>findSavedPages([capture],{query,operation,...rest}).matches;

test('local fallbacks honor exact terms, source-query evidence, dates and publication filters',()=>{
  assert.equal(testSearch('halifax').length,1);
  assert.equal(testSearch('lively debate').length,1);
  assert.equal(testSearch('wireless telegraph').length,1);
  assert.equal(testSearch('lively votes').length,0);
  assert.equal(testSearch('harbour halifax','AND').length,1);
  assert.equal(testSearch('boats halifax','OR').length,1);
  assert.equal(testSearch('harbour lively','~5').length,0);
  assert.equal(testSearch('halifax lively','~5').length,1);
  assert.equal(testSearch('newspaper officials','PHRASE').length,0);
  assert.equal(testSearch('halifax','PHRASE',{start:'1915-02-04'}).length,0);
  assert.equal(testSearch('','AND',{city:'Portland',lccn:'sn12345678'}).length,1);
  assert.equal(testSearch('','AND',{city:'Portland',title:'Other paper'}).length,0);
});

test('duplicate highlights do not inflate counts and an untrusted URL cannot become a search link',()=>{
  const second={...capture,records:[{...paper,url:paper.url.replace('q=foo','q=bar')},{...paper,url:'https://example.com/'}]};
  const found=findSavedPages([capture,second],{query:'Halifax',operation:'AND'});
  assert.equal(found.examined,1);
  assert.equal(found.matches.length,1);
  assert.equal(found.matches[0].capturedAt,capture.capturedAt);
});

import {reviewedPages} from '../web/verified-pages.mjs';
test('individual archival citations match the Halifax request without enabling arbitrary archive URLs',()=>{
 const req={query:'Halifax',operation:'PHRASE',start:'1800-01-01',end:'1930-12-31'};
 const {matches}=findSavedPages([reviewedPages],req);
 assert.equal(matches.length,4);
 assert.ok(matches.every(({record})=>/halifax/i.test(record.excerpt) && record.sourceLabel));
 assert.equal(findSavedPages([reviewedPages],{...req,end:'1917-12-06'}).matches.length,0);
 assert.equal(findSavedPages([reviewedPages],{...req,city:'Medford'}).matches.length,1);
 const imitation={...reviewedPages,records:[{...reviewedPages.records[0],url:'https://tile.loc.gov/some-other-path'}]};
 assert.equal(findSavedPages([imitation],req).matches.length,0);
});
