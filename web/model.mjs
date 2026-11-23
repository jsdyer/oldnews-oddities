export const API = 'https://www.loc.gov/collections/chronicling-america/';
export function searchSpec(query, operator, fromYear, toYear) {
  query=String(query||'').trim(); fromYear=Number(fromYear);toYear=Number(toYear);
  if (!query || query.length>200) throw new Error('Enter a search between 1 and 200 characters.');
  if (!['PHRASE','AND','OR'].includes(operator)) throw new Error('Choose a valid search mode.');
  if (!Number.isInteger(fromYear)||!Number.isInteger(toYear)||fromYear<1600||toYear>2100||fromYear>toYear) throw new Error('Enter a valid year range from 1600 to 2100.');
  return {query,operator,fromYear,toYear};
}
export function searchUrl(spec,count=12,page=1,json=true) {
  const url=new URL(API);
  const params={c:String(count),sp:String(page),st:'gallery',dl:'page',searchType:'advanced',qs:spec.query,ops:spec.operator,start_date:`${spec.fromYear}-01-01`,end_date:`${spec.toYear}-12-31`};
  if(json)params.fo='json';for(const [k,v] of Object.entries(params))url.searchParams.set(k,v);return url.href;
}
export function safeUrl(value,image=false) {
  if(typeof value!=='string')return null;
  if(value.startsWith('http://www.loc.gov/'))value='https://'+value.slice(7);
  try {const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&(image?['loc.gov','www.loc.gov','tile.loc.gov']:['loc.gov','www.loc.gov']).includes(u.hostname)?u.href:null;}catch{return null;}
}
const first = x => Array.isArray(x) ? String(x[0]??'') : '';
export function normalizeResponse(data) {
  if(!data||!Array.isArray(data.results)||!data.pagination)throw new Error('The library returned an unexpected response. Your previous shelf is still available.');
  const records=[],seen=new Set();
  for(const x of data.results){
    const url=safeUrl(x.url),date=String(x.date||'');if(!url||!url.includes('/resource/')||!/^\d{4}-\d{2}-\d{2}$/.test(date))continue;
    const id=String(x.page_id||url);if(seen.has(id))continue;seen.add(id);
    records.push({id,title:String(x.title||'Untitled newspaper page'),date,url,image:(x.image_url||[]).filter(v=>typeof v==='string'&&v.includes('/image-services/')&&v.includes('.jpg')).map(v=>safeUrl(v,true)).find(Boolean)||null,paper:first(x.partof_title),city:first(x.location_city),state:first(x.location_state),language:Array.isArray(x.language)?x.language:[],ocrExcerpt:(x.description||[]).join(' ').slice(0,900),lccn:first(x.number_lccn),page:String(Number(first(x.number_page))) });
  }
  if(data.results.length&&!records.length)throw new Error('No usable newspaper pages were returned. Your previous shelf is still available.');
  const total=data.pagination.of;if(!Number.isInteger(total)||total<0)throw new Error('The library returned an invalid result count.');
  return {records,total};
}
export function textUrl(url){const u=new URL(url);u.searchParams.set('st','text');return u.href;}
export function matchedExcerpt(record,query,max=200){
  const text=record.ocrExcerpt||'',terms=query.toLowerCase().split(/\s+/).filter(x=>x.length>3);const index=terms.map(t=>text.toLowerCase().indexOf(t)).filter(x=>x>=0).sort((a,b)=>a-b)[0];
  if(index===undefined)return '';const start=Math.max(0,index-45);return (start?'…':'')+text.slice(start,start+max)+(start+max<text.length?'…':'');
}
export function filterRecords(records,query){query=query.trim().toLowerCase();return records.filter(r=>!query||[r.title,r.city,r.state,r.date,r.ocrExcerpt].join(' ').toLowerCase().includes(query));}
export function csv(records){const cell=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replaceAll('"','""')+'"';return [['Date','Newspaper page','Place','Source URL'],...records.map(r=>[r.date,r.title,[r.city,r.state].filter(Boolean).join(', '),r.url])].map(r=>r.map(cell).join(',')).join('\r\n');}
export function receipt(records,context,now=new Date().toISOString()){return {schemaVersion:1,tool:'oldnews-oddities',exportedAt:now,context,interpretation:'Historical newspaper search matches, not verified events. OCR can be wrong. Read the source page.',records};}
