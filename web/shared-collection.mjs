import {safeUrl} from './model.mjs';
export const MANIFEST_URL='https://coolcode.ca/headlinevault/data/newspapers.json';
const CAPTURES_URL='https://coolcode.ca/headlinevault/data/captures.json';
export function sharedManifest(raw){
 if(raw?.schema!=='coolcode.newspaper-collection.v1'||raw.capturesUrl!==CAPTURES_URL||!Array.isArray(raw.papers)||raw.papers.length>10000)throw Error('The shared collection manifest is not supported.');
 return {source:String(raw.source||'Library of Congress'),geography:String(raw.geography||'Historical U.S. newspapers'),capturedAt:raw.capturedAt,papers:raw.papers,capturesUrl:CAPTURES_URL};
}
function validDate(s){return typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;}
export function sharedCaptures(payload){
 if(payload?.schemaVersion!==1||!payload.captures||typeof payload.captures!=='object'||Array.isArray(payload.captures))throw Error('The shared captures are not supported.');
 const captures=[];
 for(const [id,c]of Object.entries(payload.captures)){
  const q=c?.query,sourceUrl=safeUrl(c?.provenance?.url);
  if(c?.schemaVersion!==1||!Array.isArray(c.records)||c.records.length>5000||!q||typeof q.query!=='string'||!['PHRASE','AND','OR'].includes(q.operation)||!validDate(q.start)||!validDate(q.end)||q.start>q.end||!Number.isFinite(Date.parse(c.capturedAt))||!sourceUrl)throw Error('A shared capture has invalid dates or provenance.');
  const u=new URL(sourceUrl);if(u.pathname!=='/collections/chronicling-america/'||u.searchParams.get('qs')!==q.query||u.searchParams.get('ops')!==q.operation||u.searchParams.get('start_date')!==q.start||u.searchParams.get('end_date')!==q.end)throw Error('The shared capture does not match its original query URL.');
  if(!Number.isInteger(c.total)||c.total<0)throw Error('The shared result count is invalid.');
  const records=[],seen=new Set();
  for(const r of c.records){const url=safeUrl(r.url);if(!url||!new URL(url).pathname.startsWith('/resource/')||!validDate(r.date))throw Error('A shared newspaper page is invalid.');const key=String(r.id||url);if(seen.has(key))continue;seen.add(key);records.push({id:key,url,title:String(r.title||'Newspaper page'),date:r.date,image:safeUrl(r.image,true),paper:String(r.newspaper||''),city:String(r.city||''),state:String(r.state||''),language:typeof r.language==='string'?[r.language]:[],ocrExcerpt:String(r.excerpt||'').slice(0,2000),lccn:String(r.lccn||''),page:String(r.page||'')});}
  captures.push({id,query:q.query,operator:q.operation,fromYear:+q.start.slice(0,4),toYear:+q.end.slice(0,4),startDate:q.start,endDate:q.end,originalQuery:{...q},capturedAt:c.capturedAt,retrievedAt:c.capturedAt,sourceUrl,total:c.total,page:c.page||1,pageSize:c.pageSize||records.length,records,mode:'shared-headlinevault',sharedCollection:MANIFEST_URL});
 }
 if(!captures.length)throw Error('The shared collection contains no retained searches.');
 return captures;
}
export function headlineQueryLink(query){const u=new URL('https://coolcode.ca/headlinevault/');for(const k of ['query','operation','start','end','state','city','title','lccn','sort'])if(typeof query[k]==='string'&&query[k])u.searchParams.set(k,query[k]);u.hash='search';return u.href;}
export async function readSharedJSON(url){
 const response=await fetch(url,{credentials:'omit',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(20000)});
 if(!response.ok)throw Error('The shared newspaper collection could not be loaded.');
 const reader=response.body.getReader();let size=0;const chunks=[];while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>4000000){await reader.cancel();throw Error('The shared collection exceeds the supported size.');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
