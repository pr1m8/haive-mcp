#!/usr/bin/env python3
"""
Screenshot documentation for debugging visual issues.
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


async def screenshot_docs():
    """Take comprehensive screenshots of the documentation."""

    # Setup paths
    screenshots_dir = Path("debug/screenshots")
    screenshots_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = screenshots_dir / f"session_{timestamp}"
    session_dir.mkdir(exist_ok=True)

    # Documentation URLs to capture
    base_url = "file://" + str(Path.cwd().absolute() / "docs" / "build")

    urls_to_capture = [
        ("index", f"{base_url}/index.html"),
        ("autoapi_index", f"{base_url}/autoapi/index.html"),
        ("mcp_module", f"{base_url}/autoapi/mcp/index.html"),
        ("agents_submodule", f"{base_url}/autoapi/mcp/agents/index.html"),
        ("specific_agent", f"{base_url}/autoapi/mcp/agents/mcp_agent/index.html"),
    ]

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)  # headless for WSL
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            color_scheme="light",  # Test light mode first
        )

        page = await context.new_page()

        print(f"📸 Starting screenshot session: {timestamp}")
        print(f"📁 Screenshots will be saved to: {session_dir}")

        for name, url in urls_to_capture:
            try:
                print(f"📸 Capturing: {name}")
                print(f"🔗 URL: {url}")

                # Navigate to page
                await page.goto(url, timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=5000)

                # Take full page screenshot
                screenshot_path = session_dir / f"{name}_full.png"
                await page.screenshot(path=screenshot_path, full_page=True, type="png")
                print(f"✅ Saved: {screenshot_path}")

                # Take viewport screenshot (above the fold)
                viewport_path = session_dir / f"{name}_viewport.png"
                await page.screenshot(path=viewport_path, full_page=False, type="png")
                print(f"✅ Saved: {viewport_path}")

                # Check for specific issues
                await check_page_issues(page, name, session_dir)

            except Exception as e:
                print(f"❌ Error capturing {name}: {e}")
                error_path = session_dir / f"{name}_error.txt"
                error_path.write_text(f"Error: {e}\nURL: {url}\n")

        # Test dark mode
        print(f"🌙 Testing dark mode...")
        await context.close()

        # Create dark mode context
        dark_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, color_scheme="dark"
        )
        dark_page = await dark_context.new_page()

        # Test main page in dark mode
        try:
            await dark_page.goto(f"{base_url}/index.html")
            await dark_page.wait_for_load_state("networkidle", timeout=5000)

            dark_path = session_dir / "index_dark_mode.png"
            await dark_page.screenshot(path=dark_path, full_page=True, type="png")
            print(f"🌙 Dark mode saved: {dark_path}")

        except Exception as e:
            print(f"❌ Dark mode error: {e}")

        await browser.close()

    # Create summary
    create_summary(session_dir, timestamp)
    print(f"🎯 Session complete! Check: {session_dir}")


async def check_page_issues(page, name, session_dir):
    """Check for specific visual issues on the page."""
    issues = []

    try:
        # Check for white-on-white text issues
        elements_with_white_text = await page.evaluate(
            """
            () => {
                const elements = Array.from(document.querySelectorAll('*'));
                return elements.filter(el => {
                    const style = window.getComputedStyle(el);
                    const color = style.color;
                    const bgColor = style.backgroundColor;
                    return color.includes('rgb(255, 255, 255)') || color.includes('#fff') || color.includes('#ffffff');
                }).length;
            }
        """
        )

        if elements_with_white_text > 10:
            issues.append(
                f"⚠️ Potential white text issues: {elements_with_white_text} elements"
            )

        # Check for missing navigation
        nav_elements = await page.locator(".sidebar, .navigation, .toctree").count()
        if nav_elements == 0:
            issues.append("❌ No navigation elements found")

        # Check for broken CSS
        css_errors = await page.evaluate(
            """
            () => {
                const errors = [];
                const stylesheets = Array.from(document.styleSheets);
                for (let sheet of stylesheets) {
                    try {
                        sheet.cssRules; // This will throw if CSS failed to load
                    } catch (e) {
                        errors.push(sheet.href || 'inline');
                    }
                }
                return errors;
            }
        """
        )

        if css_errors:
            issues.append(f"❌ CSS loading errors: {css_errors}")

        # Save issues report
        if issues:
            issues_path = session_dir / f"{name}_issues.txt"
            issues_path.write_text("\n".join(issues))
            print(f"⚠️ Issues found for {name}: {len(issues)}")

    except Exception as e:
        print(f"❌ Error checking issues for {name}: {e}")


def create_summary(session_dir, timestamp):
    """Create a summary of the screenshot session."""

    summary = f"""# Documentation Screenshot Session
    
**Timestamp**: {timestamp}
**Directory**: {session_dir}

## Files Captured:

"""

    # List all files
    for file_path in sorted(session_dir.glob("*")):
        if file_path.is_file():
            size_kb = file_path.stat().st_size // 1024
            summary += f"- `{file_path.name}` ({size_kb}KB)\n"

    summary += f"""

## Analysis Commands:

```bash
# View screenshots
cd {session_dir}
ls -la *.png

# Check for issues
cat *_issues.txt

# Open in browser
xdg-open index_full.png
```

## Key Areas to Check:

1. **White-on-white text**: Look at navigation and content areas
2. **Missing sidebar**: Check left navigation panel
3. **Broken layout**: Look for overlapping or misaligned elements
4. **CSS loading**: Check if styles are applied correctly
"""

    summary_path = session_dir / "README.md"
    summary_path.write_text(summary)


if __name__ == "__main__":
    asyncio.run(screenshot_docs())
