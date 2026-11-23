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
                page.get_by_text("Follow your own curiosity", exact=True).click()
                page.locator("#query").fill("mechanical man")
                page.locator("#searchSubmit").click()
                page.wait_for_function("document.getElementById('status').textContent.includes('Live search complete')")
                assert page.locator(".record").count() == 1
                assert "mechanical man" in page.locator("#shelfTitle").inner_text()
                # A failed custom search preserves the live page and existing clippings.
                page.locator(".save").first.click()
                page.wait_for_timeout(4100)
                page.unroute("https://www.loc.gov/collections/chronicling-america/**")
                page.route("https://www.loc.gov/collections/chronicling-america/**", lambda route: route.fulfill(status=200, content_type="text/html", body="<html>verification required</html>"))
                page.locator("#query").fill("Halifax")
                page.locator("#searchSubmit").click()
                page.wait_for_function("document.getElementById('status').textContent.includes('web page instead of JSON')")
                assert page.locator(".record").count() == 1
                assert "1 page" in page.locator("#clipCount").inner_text()
                assert "qs=Halifax" in page.locator("#providerJSON").get_attribute("href")
                assert page.locator("#importSource").input_value() == ""
                page.locator("#copySource").click()
                source_url = page.locator("#importSource").input_value()
                assert "qs=Halifax" in source_url
                imported = {"results": [{"page_id": "imported-halifax", "url": "https://www.loc.gov/resource/sn123/1900-01-01/ed-1/?sp=1", "date": "1900-01-01", "title": "Imported Halifax report"}], "pagination": {"of": 1, "current": 1, "perpage": 12}}
                import_path = Path(temporary) / "library-response.json"
                import_path.write_text(json.dumps(imported))
                page.locator("#importLibrary").set_input_files(str(import_path))
                page.wait_for_function("document.getElementById('status').textContent.includes('Imported 1 newspaper pages')")
                assert "Imported Halifax report" in page.locator(".record h3").inner_text()
                assert "original retrieval time is unknown" in page.locator("#topicDescription").inner_text()
                assert "1 page" in page.locator("#clipCount").inner_text()
                assert not page.locator("#more").is_visible()
                page.locator(".save").first.click()
                with page.expect_download() as downloaded:
                    page.locator("#exportJSON").click()
                exported = json.loads(Path(downloaded.value.path()).read_text())
                imported_context = next(r["researchContext"] for r in exported["records"] if r["id"] == "imported-halifax")
                assert imported_context["retrievedAt"] is None
                assert imported_context["importedAt"]
                assert imported_context["sourceUrl"] == source_url
                # Reject HTML/incorrect URLs without replacing imported results.
                page.locator("#importSource").fill("https://evil.test/results.json")
                page.locator("#importLibrary").set_input_files(str(import_path))
                page.wait_for_function("document.getElementById('status').textContent.includes('Could not import')")
                assert "Imported Halifax report" in page.locator(".record h3").inner_text()
                assert "2 pages" in page.locator("#clipCount").inner_text()
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
