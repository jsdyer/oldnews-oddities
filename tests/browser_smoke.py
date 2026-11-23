"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import json
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator(".record").first.wait_for()
                assert page.locator("#topics button").count() > 0
                page.locator(".save").first.click()
                assert "1 page" in page.locator("#clipCount").inner_text()
                page.locator("#shuffle").click()
                assert page.locator("#spotlight").is_visible()
                page.locator("#filter").fill("nothing-matches-this-unique-text")
                assert page.locator(".record").count() == 0
                page.locator("#filter").fill("")
                assert page.locator(".record").count() > 0
                with page.expect_download() as download:
                    page.locator("#exportJSON").click()
                assert download.value.suggested_filename.endswith(".json")
                page.locator("#clearClips").click()
                assert page.locator("#exportJSON").is_disabled()
                captured = json.loads((ROOT / "web/data/shelf.json").read_text())["topics"][0]["records"][0]
                mock = {"results": [{"page_id": captured["id"], "url": captured["url"], "date": captured["date"], "title": captured["title"], "image_url": [], "description": [], "location_city": [captured["city"]], "location_state": [captured["state"]]}], "pagination": {"of": 1, "total": 1}}
                page.route("https://www.loc.gov/collections/chronicling-america/**", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(mock)))
                page.locator("summary").click()
                page.locator("#query").fill("mechanical man")
                page.locator("#searchSubmit").click()
                page.wait_for_function("document.getElementById('status').textContent.includes('Live search complete')")
                assert page.locator(".record").count() == 1
                assert "mechanical man" in page.locator("#shelfTitle").inner_text()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: real shelf, topic cards, clippings export, filters, shuffle and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
