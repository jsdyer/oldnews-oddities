# Old News Oddities

A public browser tool for following curious reports in historical U.S. newspapers.
Real Library of Congress page scans, editable discovery topics, arbitrary live
full-text queries, random page discovery and a downloadable source trail.

<!-- coolcode:guide -->
Choose a topic or search your own phrase, then open the original page to check the OCR and surrounding columns. Topic matches are historical reports, not verified events; save useful pages and export their source links. If a live request fails, import an official Library JSON response with its exact search URL; clippings stay usable and imports are clearly dated as imports.
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
can be slow or blocked during heavy load. The Library explicitly warns that even
requests below its limit may receive HTTP 429 or HTML verification pages. Browser
cross-site access and network failures can also hide the underlying response;
“Failed to fetch” alone cannot distinguish them. A successful test in one browser
does not guarantee access from every visitor's browser. The app never retries
failures automatically and preserves previous results and clippings.

Live requests use the documented `at=results,pagination` projection to avoid
unneeded response fields. This reduces payload size; it does not remove upstream
access controls or guarantee a faster search.

### Recover a search using an official JSON file

1. Set your query, then expand **Import Library of Congress results**. Its JSON
   link follows the attempted query and page, including a failed next-page request.
2. Open **Open this search as Library JSON** in a normal tab. If JSON appears,
   save it as a `.json` file. If the provider returns verification or an error,
   an HTML save is not usable JSON; use the provider's own interface as permitted.
3. Click **Use the linked search URL**, or paste the exact source URL of an
   already-saved response. The URL is explicit so a file is not silently associated
   with whichever form happens to be open.
4. Choose the JSON file. The app validates the collection, query, dates, page,
   count, available pagination metadata and source links before replacing results.
   Existing clippings stay intact. Choose **Save this page** to retain and export
   imported pages just like live results.

File reads are local. Imported pages carry `mode: imported`, their exact
`sourceUrl`, `importedAt`, date range and page information in each clipping's
research context. The upstream retrieval time is unknown (`retrievedAt: null`),
not the import time. Imports do not automatically continue network pagination.

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

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

The separate schedule guard remains a mitigation, not a scheduling guarantee. The independent [CoolCode refresh watchdog](https://github.com/jsdyer/jsdyer.github.io/blob/main/services/refresh-watchdog/README.md) is maintained in GitHub and uses the generated workflow and freshness registry; do not maintain another target list here. Using it requires installation on a Linux server and GitHub credentials with access to this repository. A generated target does not prove that a private server has adopted it; verify the installed service's report. The guard does not collect data, create dummy commits or change source/check timestamps. Successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
