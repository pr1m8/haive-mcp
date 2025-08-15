#!/usr/bin/env python3
"""
Enhanced screenshot utility for AutoAPI documentation debugging.
Takes comprehensive screenshots with scrolling, multiple pages, and debug analysis.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


async def take_screenshot_with_scrolling(page, path: Path, name: str):
    """Take a full-page screenshot with progressive scrolling."""
    # Take initial viewport screenshot
    await page.screenshot(path=path / f"{name}_viewport.png")

    # Take full page screenshot
    await page.screenshot(path=path / f"{name}_fullpage.png", full_page=True)

    # Take scrolled screenshots to show different parts
    viewport_height = await page.evaluate("() => window.innerHeight")
    page_height = await page.evaluate("() => document.body.scrollHeight")

    if page_height > viewport_height:
        # Scroll to middle
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=path / f"{name}_middle.png")

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=path / f"{name}_bottom.png")

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)


async def analyze_page_features(page, url: str) -> dict:
    """Analyze page features to debug issues."""
    features = {
        "url": url,
        "title": await page.title(),
        "has_navigation": False,
        "has_breadcrumbs": False,
        "clickable_links_count": 0,
        "toc_entries": [],
        "view_source_links": 0,
        "css_files": [],
        "js_files": [],
        "errors": [],
    }

    try:
        # Check for navigation sidebar
        nav_elements = await page.query_selector_all(
            '[class*="sidebar"], [class*="navigation"], [class*="toctree"]'
        )
        features["has_navigation"] = len(nav_elements) > 0

        # Check for breadcrumbs
        breadcrumb_elements = await page.query_selector_all(
            '[class*="breadcrumb"], nav[aria-label*="breadcrumb"]'
        )
        features["has_breadcrumbs"] = len(breadcrumb_elements) > 0

        # Count clickable links in content
        content_links = await page.query_selector_all(
            'main a, .content a, [class*="autoapi"] a'
        )
        clickable_count = 0
        for link in content_links:
            href = await link.get_attribute("href")
            if href and not href.startswith("#"):
                clickable_count += 1
        features["clickable_links_count"] = clickable_count

        # Get TOC entries
        toc_elements = await page.query_selector_all(
            '.toctree-l1, .toctree-l2, [class*="toc"] li'
        )
        for toc in toc_elements[:10]:  # Limit to first 10
            text = await toc.text_content()
            if text and text.strip():
                features["toc_entries"].append(text.strip())

        # Count view source links
        view_source_links = await page.query_selector_all(
            'a[href*="source"], a[title*="source"], a[title*="View"]'
        )
        features["view_source_links"] = len(view_source_links)

        # Get loaded CSS and JS files
        css_links = await page.query_selector_all('link[rel="stylesheet"]')
        for css in css_links:
            href = await css.get_attribute("href")
            if href:
                features["css_files"].append(href)

        js_scripts = await page.query_selector_all("script[src]")
        for js in js_scripts:
            src = await js.get_attribute("src")
            if src:
                features["js_files"].append(src)

    except Exception as e:
        features["errors"].append(str(e))

    return features


async def capture_documentation_debug(port: int = 8003):
    """Capture comprehensive documentation screenshots with debug analysis."""

    # Create debug pictures directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = Path("debug") / "pictures" / f"autoapi_fix_{timestamp}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    # Base URL
    base_url = f"http://localhost:{port}"

    # Critical pages to test (based on the original issues)
    test_pages = [
        ("01_main_index", f"{base_url}/index.html"),
        ("02_autoapi_index", f"{base_url}/autoapi/index.html"),
        ("03_mcp_main", f"{base_url}/autoapi/mcp/index.html"),
        (
            "04_downloader_config_PROBLEMATIC",
            f"{base_url}/autoapi/mcp/downloader/config/index.html",
        ),
        ("05_agents_index", f"{base_url}/autoapi/mcp/agents/index.html"),
        ("06_mcp_agent", f"{base_url}/autoapi/mcp/agents/mcp_agent/index.html"),
        ("07_tools_index", f"{base_url}/autoapi/mcp/tools/index.html"),
        ("08_servers_index", f"{base_url}/autoapi/mcp/servers/index.html"),
        ("09_cli_manager", f"{base_url}/autoapi/mcp/cli/mcp_manager/index.html"),
        (
            "10_documentation_agent",
            f"{base_url}/autoapi/mcp/agents/documentation_agent/index.html",
        ),
    ]

    # Analysis results
    analysis_results = []

    async with async_playwright() as p:
        # Launch browser with debugging options
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--allow-running-insecure-content",
            ],
        )

        # Create context
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, color_scheme="light"
        )

        print(f"🔍 Starting AutoAPI documentation debug session: {timestamp}")
        print(f"📁 Debug pictures saved to: {debug_dir}")
        print(f"🌐 Testing server: {base_url}")
        print("-" * 80)

        for name, url in test_pages:
            page = await context.new_page()

            try:
                print(f"📸 Capturing and analyzing: {name}")
                print(f"   URL: {url}")

                # Navigate to page
                response = await page.goto(url, wait_until="networkidle")

                if response and response.status == 200:
                    # Wait for page to load completely
                    await page.wait_for_timeout(2000)

                    # Create subdirectory for this page
                    page_dir = debug_dir / name
                    page_dir.mkdir(exist_ok=True)

                    # Take comprehensive screenshots
                    await take_screenshot_with_scrolling(page, page_dir, name)

                    # Analyze page features
                    analysis = await analyze_page_features(page, url)
                    analysis_results.append(analysis)

                    # Save analysis to JSON
                    with open(page_dir / f"{name}_analysis.json", "w") as f:
                        json.dump(analysis, f, indent=2)

                    # Print quick status
                    nav_status = "✅" if analysis["has_navigation"] else "❌"
                    breadcrumb_status = "✅" if analysis["has_breadcrumbs"] else "❌"
                    links_status = (
                        "✅" if analysis["clickable_links_count"] > 0 else "❌"
                    )

                    print(
                        f"   Navigation: {nav_status} | Breadcrumbs: {breadcrumb_status} | Links: {links_status} ({analysis['clickable_links_count']})"
                    )

                else:
                    print(f"   ❌ HTTP {response.status if response else 'timeout'}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

            finally:
                await page.close()

        await browser.close()

    # Save comprehensive analysis
    with open(debug_dir / "comprehensive_analysis.json", "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "base_url": base_url,
                "pages_analyzed": len(analysis_results),
                "pages": analysis_results,
            },
            f,
            indent=2,
        )

    # Generate summary report
    summary_file = debug_dir / "SUMMARY_REPORT.md"
    with open(summary_file, "w") as f:
        f.write(f"# AutoAPI Documentation Debug Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Session**: {timestamp}\n")
        f.write(f"**Base URL**: {base_url}\n\n")

        f.write("## Page Analysis Summary\n\n")
        f.write("| Page | Navigation | Breadcrumbs | Links | View Source | Status |\n")
        f.write("|------|------------|-------------|-------|-------------|--------|\n")

        for analysis in analysis_results:
            name = (
                analysis["url"].split("/")[-2]
                if analysis["url"].endswith("/index.html")
                else "main"
            )
            nav = "✅" if analysis["has_navigation"] else "❌"
            breadcrumbs = "✅" if analysis["has_breadcrumbs"] else "❌"
            links = (
                f"✅ ({analysis['clickable_links_count']})"
                if analysis["clickable_links_count"] > 0
                else "❌"
            )
            view_src = (
                f"✅ ({analysis['view_source_links']})"
                if analysis["view_source_links"] > 0
                else "❌"
            )
            status = (
                "✅ OK"
                if analysis["has_navigation"] and analysis["clickable_links_count"] > 0
                else "❌ Issues"
            )

            f.write(
                f"| {name} | {nav} | {breadcrumbs} | {links} | {view_src} | {status} |\n"
            )

        f.write(f"\n## Issues Found\n\n")
        issues_found = False
        for analysis in analysis_results:
            if not analysis["has_navigation"] or analysis["clickable_links_count"] == 0:
                issues_found = True
                f.write(f"- **{analysis['title']}**: ")
                if not analysis["has_navigation"]:
                    f.write("Missing navigation sidebar. ")
                if analysis["clickable_links_count"] == 0:
                    f.write("No clickable links found. ")
                f.write(f"(URL: {analysis['url']})\n")

        if not issues_found:
            f.write(
                "🎉 No major issues found! All pages have navigation and clickable links.\n"
            )

        f.write(f"\n## File Structure\n\n")
        f.write("Screenshots are organized as follows:\n")
        f.write("- `[page_name]_viewport.png` - Initial viewport view\n")
        f.write("- `[page_name]_fullpage.png` - Full page screenshot\n")
        f.write("- `[page_name]_middle.png` - Middle section (if page is long)\n")
        f.write("- `[page_name]_bottom.png` - Bottom section (if page is long)\n")
        f.write("- `[page_name]_analysis.json` - Detailed analysis data\n")

    print("-" * 80)
    print(f"🎉 Debug session complete!")
    print(f"📁 All files saved to: {debug_dir}")
    print(f"📊 Summary report: {summary_file}")
    print(f"🔍 Analyzed {len(analysis_results)} pages")

    # Quick summary
    working_pages = sum(
        1
        for a in analysis_results
        if a["has_navigation"] and a["clickable_links_count"] > 0
    )
    print(f"✅ Working pages: {working_pages}/{len(analysis_results)}")

    return debug_dir


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8003

    # Check if server is running
    import urllib.request

    try:
        urllib.request.urlopen(f"http://localhost:{port}", timeout=5)
    except:
        print(f"❌ No server found on port {port}")
        print(
            f"   Start server: nohup python -m http.server {port} --directory docs/build > /tmp/http_server.log 2>&1 &"
        )
        exit(1)

    asyncio.run(capture_documentation_debug(port))
