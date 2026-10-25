"""Optional end-to-end check: pip install playwright; playwright install chromium.
Run from any directory: python scripts/test_studio_browser.py
Uses an isolated temporary database; never opens your normal workspace database.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def check():
    with tempfile.TemporaryDirectory(prefix="studio-browser-") as temporary:
        env = dict(os.environ, WORKSPACE_DB=str(Path(temporary) / "test.sqlite3"))
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.workspace:app", "--host", "127.0.0.1", "--port", "8090"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            with sync_playwright() as pw:
                options = {"headless": True}
                if os.environ.get("BROWSER_EXECUTABLE"):
                    options["executable_path"] = os.environ["BROWSER_EXECUTABLE"]
                browser = pw.chromium.launch(**options)
                page = browser.new_page(viewport={"width": 1440, "height": 1050})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                base = "http://127.0.0.1:8090"
                for attempt in range(50):
                    try:
                        response = page.request.get(base + "/api/runs", timeout=1000)
                        if response.ok:
                            break
                    except Exception:
                        pass
                    if server.poll() is not None:
                        raise RuntimeError("Test server could not start on port 8090.")
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Test server did not become ready.")

                def visit(route):
                    page.goto(base + route)
                    page.wait_for_selector("#page h1")
                    assert not page.locator(".startup-error").count(), route

                visit("/portfolio")
                modern = page.locator("body").get_attribute("data-product") == "ModernizeIQ"
                primary = "demo-v3-legacy" if modern else "demo-v3-incident"
                demo_count = 2 if modern else 3
                assert page.locator(".portfolio-table tbody tr").count() == demo_count
                routes = page.locator(".side-nav a").evaluate_all("(nodes)=>nodes.map(n=>n.getAttribute('href'))")
                for route in routes:
                    visit(route)
                    assert "undefined" not in page.locator("#page").inner_text(), route
                visit("/portfolio?run=" + primary)
                page.locator("#portfolio-search").fill("no-such-project")
                assert page.locator(".portfolio-table tbody tr").count() == 0
                page.locator("#portfolio-search").fill("")
                page.locator("[data-demo]").first.click()
                page.wait_for_url("**/portfolio?run=" + primary)
                page.wait_for_selector(".portfolio-table")

                visit("/findings?run=" + primary)
                page.locator("[data-finding]").first.click()
                page.wait_for_selector("#drawer[open]")
                assert "Supporting evidence" in page.locator("#drawer").inner_text()
                page.get_by_label("Close details").click()
                page.locator("#finding-search").fill("no-such-finding")
                assert page.locator("#finding-table tbody tr").count() == 0

                if modern:
                    visit("/assessment?run=" + primary)
                    page.locator("[data-category]").first.click()
                    page.wait_for_selector("#drawer[open]")
                    assert "undefined" not in page.locator("#drawer").inner_text()
                    assert page.locator(".check-row").count() > 0
                    page.get_by_label("Close details").click()
                    visit("/architecture?run=" + primary)
                    page.locator("[data-map=both]").click()
                    assert page.locator("#map-view .architecture-map").count() == 2
                    page.locator("[data-proposed=true]").first.click()
                    page.wait_for_selector("#drawer[open]")
                    page.get_by_label("Close details").click()
                    visit("/dependencies?run=" + primary)
                    assert page.locator("#dep-table tbody tr").count() > 0
                    page.locator("#dep-search").fill("no-such-package")
                    assert page.locator("#dep-table tbody tr").count() == 0
                    visit("/roadmap?run=" + primary)
                    assert page.locator(".roadmap-card").count() > 0
                else:
                    visit("/services?run=" + primary)
                    assert page.locator(".service-card").count() == 6
                    visit("/signals?run=" + primary)
                    page.locator("#signal-service").select_option("payment-service")
                    page.locator("#signal-metric").select_option("error_rate")
                    assert page.locator("#signal-table tbody tr").count() == 45

                visit("/review?run=" + primary)
                for decision in ["accepted", "investigate"]:
                    page.locator("#decision-form select").select_option(decision)
                    page.locator("#decision-form textarea").fill("Browser check: " + decision)
                    page.locator("#decision-form button[type=submit]").click()
                    page.wait_for_function(
                        "decision => document.querySelector('.review-list button .pill:last-child').textContent === decision",
                        arg=decision,
                    )
                visit("/audit?run=" + primary)
                assert "Browser check: investigate" in page.locator(".audit-list").inner_text()
                assert page.locator(".audit-list article").count() == 2

                visit("/compare?run=" + primary)
                page.wait_for_selector(".comparison-summary")
                before = page.locator("#before").input_value()
                page.locator("#after").select_option(before)
                page.locator("#compare-button").click()
                assert "Choose two different snapshots" in page.locator("#comparison").inner_text()

                visit("/reports?run=" + primary)
                with page.expect_popup() as popup_info:
                    page.get_by_text("Open report", exact=False).click()
                popup = popup_info.value
                popup.wait_for_load_state()
                assert "Browser check: investigate" in popup.locator("body").inner_text()
                popup.close()
                for suffix in ["export", "findings.csv"]:
                    response = page.request.get(base + "/api/runs/" + primary + "/" + suffix)
                    assert response.ok and len(response.body()) > 20

                sample = page.request.get(base + "/api/sample").body()
                visit("/import?run=" + primary)
                page.locator("input[type=file]").set_input_files(
                    {
                        "name": "browser-sample.zip" if modern else "browser-sample.csv",
                        "mimeType": "application/zip" if modern else "text/csv",
                        "buffer": sample,
                    }
                )
                page.locator("input[name=name]").fill("Browser imported project")
                page.locator("textarea[name=objective]").fill("Verify input-to-evidence workflow")
                if not modern:
                    page.locator("input[name=latency]").fill("2000")
                page.locator("#upload-form button[type=submit]").click()
                page.wait_for_url("**/assessment?run=*")
                page.wait_for_selector("#page h1")
                assert "Browser imported project" in page.locator("#page").inner_text()
                if not modern:
                    assert "No incident detected with these settings" in page.locator("#page").inner_text()
                assert len(page.request.get(base + "/api/runs").json()) == demo_count + 1

                page.set_viewport_size({"width": 390, "height": 844})
                for route in routes:
                    visit(route)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), (
                        "Mobile overflow: " + route
                    )
                assert not errors, errors
                print(
                    f"{'ModernizeIQ' if modern else 'OpsPilot'}: PASS — {len(routes)} pages, desktop/mobile, demo, filters, drawers, reviews, comparison, report and import."
                )
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    check()
