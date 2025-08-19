#!/usr/bin/env python3
"""Screenshot specific problematic page."""

import os

from playwright.sync_api import sync_playwright


def screenshot_specific_page():
    url = "file:///home/will/Projects/haive/backend/haive/packages/haive-mcp/docs/build/autoapi/mcp/comprehensive_mcp_web/index.html"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            page.goto(url)
            page.wait_for_load_state("networkidle")

            # Take full page screenshot
            page.screenshot(
                path="debug/comprehensive_mcp_web_issue.png", full_page=True
            )
            print(f"✅ Screenshot saved: debug/comprehensive_mcp_web_issue.png")

            # Check for white on white text issues
            # Look for elements with poor contrast
            issues = page.evaluate(
                """
                () => {
                    const issues = [];
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgColor = style.backgroundColor;
                        const textColor = style.color;
                        
                        // Check for white/light backgrounds with white/light text
                        if ((bgColor.includes('255, 255, 255') || bgColor === 'white') && 
                            (textColor.includes('255, 255, 255') || textColor === 'white' || textColor.includes('240, 240, 240'))) {
                            issues.push({
                                tag: el.tagName,
                                class: el.className,
                                text: el.textContent.substring(0, 50),
                                bgColor: bgColor,
                                textColor: textColor
                            });
                        }
                    });
                    
                    return issues;
                }
            """
            )

            print(f"⚠️  Found {len(issues)} potential contrast issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"   {issue['tag']}.{issue['class']}: '{issue['text'][:30]}...'")
                print(f"      bg: {issue['bgColor']}, text: {issue['textColor']}")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            browser.close()


if __name__ == "__main__":
    screenshot_specific_page()
