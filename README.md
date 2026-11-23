# Old News Oddities

A public browser tool for following curious reports in historical U.S. newspapers.
Real Library of Congress page scans, editable discovery topics, arbitrary live
full-text queries, random page discovery and a downloadable source trail.

<!-- coolcode:guide -->
Choose a topic or search your own phrase, then open the original page to check the OCR and surrounding columns. Topic matches are historical reports, not verified events; save useful pages and export their source links.
<!-- /coolcode:guide -->

## Use it

The first shelf is a real retained LoC query for **mysterious airship**. Other
editable shelves explore perpetual motion, wireless telegraphy and sea serpents.
Choose **Follow your own curiosity**, enter any phrase and dates, then submit to
search the public collection. Search modes are exact phrase, all words and any
word. **Load the next page** continues that query; **Filter these pages** only
filters the pages already loaded. **Surprise me** randomly selects a loaded page,
not a random item from the entire collection. No registration or API key required.

Save any page to the tab's clippings list, even across searches. Export a JSON
research receipt or CSV source list. Nothing is automatically persisted across
browser sessions. Images and explicit searches contact the Library of Congress.
No query or saved page is sent to CoolCode; the shared aggregate counter records
the tool ID only.

## Expand or customize

**Edit `web/config.json`.** Topics, labels, descriptions, search phrases, match
operators, date ranges, result count and request timeout live here. There is no
fixed topic count. Add another object to `topics`, for example:

```json
{
  "id": "mechanical-people",
  "label": "Mechanical people",
  "query": "mechanical man",
  "operator": "PHRASE",
  "fromYear": 1850,
  "toYear": 1930,
  "description": "Automata, stage inventions and accounts of mechanical people."
}
```

Use a unique lowercase slug for `id`. `operator` accepts `PHRASE`, `AND` or `OR`.
`pageSize` accepts 1–80 and controls how many pages are fetched per topic/query,
not the number of topics or the archive's coverage. All counts derive from the
actual data. Dates must form a valid ordered range. The live form accepts custom
queries without changing any repository file.

**Publishing a configuration change:** save the config to `main`. The workflow
checks its hash and automatically refreshes the shelves when it differs from the
retained capture, then validates, tests, builds and publishes. Code-only pushes
reuse retained data. Manual **Run workflow → refresh_data** also refreshes; a
weekly Wednesday collection does the same. Failed API requests leave the last
successful deployed version intact. The job commits a successful shelf only
after its checks. GitHub may pause inactive public-repository schedules.

Local refresh/build:

```sh
python3 scripts/collect.py
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

The default build is offline. `scripts/collect.py --if-config-changed` avoids
requests when the configuration already matches the shelf. Keep request spacing
at least four seconds. Increasing collection size costs one sequential API
request per topic. The collector prepares the whole shelf before replacing it.

## Evidence and limits

- `web/data/shelf.json` records retrieval time, exact source queries, response
  SHA-256 digests, source-reported match counts and normalized page metadata.
- The retained shelf is the first result page per query, not a statistically
  representative sample or an exhaustive index. Search ranking and OCR can change.
- Dates describe newspaper publication. The query total is `pagination.of`
  (matching pages), not `pagination.total` (result pages).
- Images and source links point to the actual digitized newspaper page.
  Short OCR excerpts are displayed only when part of the query appears in the
  stored excerpt. An excerpt can still miss the relevant story or misread words.
- Never infer that a report is true because it appears in a newspaper. Satire,
  fiction, advertisements and contested claims share pages with ordinary news.
- Source records are U.S. newspapers, although their coverage can mention Canada.

## Source, access and rights

The [current Chronicling America API](https://www.loc.gov/apis/additional-apis/chronicling-america-api/)
is the loc.gov JSON API; the legacy API was retired in 2025.
[Current API limits](https://www.loc.gov/apis/json-and-yaml/working-within-limits/)
state 20 JSON requests per minute; the app submits only explicit searches with
at least four seconds between starts and no automatic retry storm. API requests
can be slow or blocked during heavy load. A failed live request preserves the
previous shelf and supplies the equivalent provider search link. The observed
API response supports cross-origin browser requests.

[Rights and access](https://www.loc.gov/collections/chronicling-america/about-this-collection/rights-and-access/):
the Library believes the collection is in the public domain or has no known
copyright restrictions. Later third-party material can have separate rights;
inspect the source record before reuse. Attribute Library of Congress /
Chronicling America and the original newspaper.

## Development and deployment

Source is in `web/`, collector/build scripts in `scripts/`, tests in `tests/`.
No production dependencies or secrets. Node and Python use their standard
libraries. CI adds test-only Playwright to check the app at a repository subpath.
Successful main builds publish GitHub Pages. Preserve relative paths and do not
add a CNAME. The CoolCode catalogue owns the shared domain and tool registration.
