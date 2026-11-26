const gateway = 'https://coolcode-visitor-api.jeffdyer.workers.dev/api/newspapers/search';

// Keep the official source URL in citations and exports. Only the interactive
// JSON request goes through the CoolCode newspaper endpoint.
export async function searchNewspapers(sourceUrl, signal) {
  const target = new URL(gateway);
  target.search = new URL(sourceUrl).search;
  const response = await fetch(target, {
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    signal,
    headers: {Accept: 'application/json'}
  });
  const isJSON = (response.headers.get('content-type') || '').includes('application/json');
  if (!response.ok) {
    const message = isJSON ? (await response.json().catch(() => null))?.error?.message : null;
    throw new Error(typeof message === 'string' ? message : `Newspaper search returned HTTP ${response.status}. Try again later.`);
  }
  if (!isJSON) throw new Error('Newspaper search returned a web page instead of JSON.');
  const result = await response.json();
  if (!Array.isArray(result?.data?.results) || !result?.data?.pagination || !Number.isFinite(Date.parse(result.fetched_at))) {
    throw new Error('Newspaper search returned an incomplete archive response.');
  }
  return result;
}
