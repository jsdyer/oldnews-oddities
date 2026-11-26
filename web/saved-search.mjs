import {reviewedPages} from './verified-pages.mjs';

// Compare only published excerpts and metadata. A saved capture with the same
// phrase and operation also proves a hit when the OCR excerpt omits the phrase.
const words = value => String(value || '').normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
const clean = value => words(value).join(' ');

function includesSequence(sequence, query) {
  const first = query[0];
  return sequence.some((word,index) => word === first && query.every((q,i) => sequence[index + i] === q));
}
function matchesText(record, query, capture) {
  const terms = words(query.query);
  if (!terms.length) return !String(query.query || '').trim();
  const op = query.operation || 'AND';
  if (clean(capture.query.query) === terms.join(' ') && capture.query.operation === op) return true;
  const fields = [record.title, record.newspaper || record.paper, record.city, record.state, record.excerpt || record.ocrExcerpt].map(words);
  if (op === 'PHRASE') return fields.some(field => includesSequence(field, terms));
  if (op === 'OR') return terms.some(term => fields.some(field => field.includes(term)));
  if (op.startsWith('~')) {
    // Treat distance as intervening words. Never span different fields.
    const span = Number(op.slice(1)) + terms.length;
    const count = terms.reduce((map, term) => map.set(term, (map.get(term) || 0) + 1), new Map());
    return fields.some(field => field.some((word, i) => count.has(word) && [...count].every(([term, n]) =>
      field.slice(i, i + span).filter(w => w === term).length >= n)));
  }
  return terms.every(term => fields.some(field => field.includes(term)));
}
function fitsFilters(record, query) {
  if (query.start && (!record.date || record.date < query.start)) return false;
  if (query.end && (!record.date || record.date > query.end)) return false;
  const filterFields = {state:record.state,city:record.city,title:record.newspaper || record.paper,lccn:record.lccn};
  return Object.entries(filterFields).every(([key, value]) => !query[key] || clean(value) === clean(query[key]));
}

export function findSavedPages(captures, query) {
  const corpus = new Set(), matches = new Map();
  for (const capture of captures) {
    for (const record of capture.records || []) {
      let url;
      try {url = new URL(record.url);} catch {continue;}
      // Additional hosts are available only through our exact reviewed records.
      const trustedReview = capture === reviewedPages && reviewedPages.records.includes(record);
      if (url.protocol !== 'https:' || url.username || url.password) continue;
      if (!trustedReview && !['www.loc.gov','loc.gov'].includes(url.host)) continue;
      // The same newspaper page can carry a different OCR-highlight term.
      url.searchParams.delete('q');
      const id = url.href;
      corpus.add(id);
      if (!matches.has(id) && fitsFilters(record,query) && matchesText(record,query,capture)) {
        matches.set(id,{record,capturedAt:capture.capturedAt});
      }
    }
  }
  const entries = [...matches.values()];
  if (query.sort === 'date' || query.sort === 'date_desc') {
    const direction = query.sort === 'date' ? 1 : -1;
    entries.sort((a,b) => direction * String(a.record.date).localeCompare(String(b.record.date)));
  }
  return {examined:corpus.size,matches:entries};
}

export function showSavedSearch(container, captures, query, showEmpty = true) {
  const {examined, matches} = findSavedPages([...captures, reviewedPages], query);
  if (!matches.length && !showEmpty) { container.hidden = true; return; }
  const heading = document.createElement('h3');
  heading.textContent = 'Matches in saved newspaper pages';
  const description = document.createElement('p');
  description.textContent = `${matches.length} matches among ${examined} saved pages for ${query.query ? '“' + query.query + '”' : 'your filters'}. These saved matches come from retained search receipts and individually verified newspaper scans. The live archive has separate coverage.`;
  const list = document.createElement('ol');
  for (const {record, capturedAt} of matches) {
    const item = document.createElement('li'), link = document.createElement('a');
    link.textContent = record.title || 'Original newspaper page';
    link.href = record.url; link.target = '_blank'; link.rel = 'noopener';
    item.append(link,document.createTextNode(` · ${record.date || 'undated'} · saved ${String(capturedAt || '').slice(0,10) || 'date unknown'}`));
    if (record.sourceLabel) {
      const citation = document.createElement('p');
      citation.textContent = record.sourceLabel + ' · “' + record.excerpt + '”';
      item.append(citation);
    }
    list.append(item);
  }
  container.replaceChildren(heading, description, list);
  container.hidden = false;
}
