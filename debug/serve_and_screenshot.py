#!/usr/bin/env python3
"""
Serve documentation over HTTP and take screenshots.
"""
import asyncio
import http.server
import socketserver
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from playwright.async_api import async_playwright


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that doesn't log every request."""

    def log_message(self, format, *args):
        pass


async def screenshot_served_docs():
    """Take screenshots of documentation served over HTTP."""

    # Setup HTTP server
    PORT = 8008
    build_dir = Path("docs/build")

    if not build_dir.exists():
        print(
            "❌ Build directory doesn't exist. Run: poetry run sphinx-build -b html docs/source docs/build"
        )
        return

    # Start HTTP server in background
    def start_server():
        import os

        os.chdir(build_dir)
        with socketserver.TCPServer(("", PORT), QuietHTTPHandler) as httpd:
            httpd.serve_forever()

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    print(f"🌐 Starting HTTP server on port {PORT}...")
    time.sleep(2)

    # Test server is running
    try:
        response = requests.get(f"http://localhost:{PORT}/", timeout=5)
        print(f"✅ Server running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return

    # Setup screenshots
    screenshots_dir = Path("debug/screenshots")
    screenshots_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = screenshots_dir / f"http_session_{timestamp}"
    session_dir.mkdir(exist_ok=True)

    base_url = f"http://localhost:{PORT}"

    urls_to_capture = [
        ("index", f"{base_url}/index.html"),
        ("autoapi_index", f"{base_url}/autoapi/index.html"),
        ("mcp_module", f"{base_url}/autoapi/mcp/index.html"),
        ("agents_submodule", f"{base_url}/autoapi/mcp/agents/index.html"),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Light mode context
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, color_scheme="light"
        )
        page = await context.new_page()

        print(f"📸 Taking HTTP-served screenshots: {timestamp}")

        for name, url in urls_to_capture:
            try:
                print(f"📸 Capturing: {name}")

                await page.goto(url, timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=5000)

                # Take screenshots
                full_path = session_dir / f"{name}_full.png"
                await page.screenshot(path=full_path, full_page=True, type="png")

                viewport_path = session_dir / f"{name}_viewport.png"
                await page.screenshot(path=viewport_path, full_page=False, type="png")

                print(f"✅ Saved: {name}")

                # Check for issues
                await check_http_issues(page, name, session_dir)

            except Exception as e:
                print(f"❌ Error capturing {name}: {e}")

        # Dark mode test
        await context.close()
        dark_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, color_scheme="dark"
        )
        dark_page = await dark_context.new_page()

        try:
            await dark_page.goto(f"{base_url}/index.html")
            await dark_page.wait_for_load_state("networkidle")

            dark_path = session_dir / "index_dark_mode.png"
            await dark_page.screenshot(path=dark_path, full_page=True)
            print(f"🌙 Dark mode captured")

        except Exception as e:
            print(f"❌ Dark mode error: {e}")

        await browser.close()

    # Create comparison summary
    create_comparison_summary(session_dir, timestamp)
    print(f"🎯 HTTP session complete! Check: {session_dir}")


async def check_http_issues(page, name, session_dir):
    """Check for issues with HTTP-served pages."""
    issues = []

    try:
        # Check if CSS loaded properly
        css_count = await page.evaluate(
            """
            () => document.styleSheets.length
        """
        )

        working_css = await page.evaluate(
            """
            () => {
                let working = 0;
                for (let sheet of document.styleSheets) {
                    try {
                        sheet.cssRules; // Will throw if failed to load
                        working++;
                    } catch (e) {
                        // CSS failed to load
                    }
                }
                return working;
            }
        """
        )

        if working_css < css_count / 2:
            issues.append(
                f"⚠️ CSS loading issues: {working_css}/{css_count} stylesheets working"
            )
        else:
            issues.append(
                f"✅ CSS loading good: {working_css}/{css_count} stylesheets working"
            )

        # Check navigation
        nav_found = await page.locator(".sidebar, .wy-nav-side, .bd-sidebar").count()
        if nav_found > 0:
            issues.append(f"✅ Navigation found: {nav_found} elements")
        else:
            issues.append("❌ No navigation found")

        # Check for proper theme
        furo_theme = await page.evaluate(
            """
            () => {
                const html = document.documentElement;
                return html.getAttribute('data-theme') || 'none';
            }
        """
        )

        issues.append(f"Theme: {furo_theme}")

        # Save issues
        issues_path = session_dir / f"{name}_issues.txt"
        issues_path.write_text("\n".join(issues))

        if any("❌" in issue for issue in issues):
            print(f"⚠️ Issues found for {name}")
        else:
            print(f"✅ {name} looks good")

    except Exception as e:
        print(f"❌ Error checking {name}: {e}")


def create_comparison_summary(session_dir, timestamp):
    """Create summary comparing HTTP vs file:// serving."""

    summary = f"""# HTTP-Served Documentation Screenshots

**Timestamp**: {timestamp}  
**Method**: HTTP server on localhost:8008
**Purpose**: Compare with file:// protocol issues

## Key Differences Expected:

1. **CSS Loading**: Should work properly over HTTP
2. **Navigation**: Furo sidebar should appear
3. **Theme**: Proper light/dark mode support
4. **No CORS issues**: All resources load correctly

## Files:

"""

    for file_path in sorted(session_dir.glob("*.png")):
        size_kb = file_path.stat().st_size // 1024
        summary += f"- `{file_path.name}` ({size_kb}KB)\n"

    summary += """

## Analysis Commands:

```bash
# Compare with file:// screenshots
ls -la debug/screenshots/session_*/

# View HTTP served results
xdg-open debug/screenshots/http_session_*/index_full.png

# Check issues
cat debug/screenshots/http_session_*/index_issues.txt
```
"""

    readme_path = session_dir / "README.md"
    readme_path.write_text(summary)


if __name__ == "__main__":
    asyncio.run(screenshot_served_docs())
