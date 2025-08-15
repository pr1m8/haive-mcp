#!/usr/bin/env python3
"""Debug AutoAPI template issues."""

import os
import sys
from pathlib import Path


def check_template_files():
    """Check if template files are being used."""
    template_dir = Path("docs/source/_autoapi_templates")

    print("=== Template Directory Check ===")
    if template_dir.exists():
        print(f"✅ Template directory exists: {template_dir}")

        # List all template files
        for root, dirs, files in os.walk(template_dir):
            level = root.replace(str(template_dir), "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print(f"❌ Template directory missing: {template_dir}")


def check_conf_py():
    """Check if conf.py has correct settings."""
    conf_file = Path("docs/source/conf.py")

    print("\n=== Conf.py Settings Check ===")
    if conf_file.exists():
        content = conf_file.read_text()

        # Check for critical settings
        settings = {
            "autoapi_template_dir": "autoapi_template_dir",
            "autoapi_own_page_level": "autoapi_own_page_level",
            "autoapi_dirs": "autoapi_dirs",
            "autoapi_type": "autoapi_type",
        }

        for name, pattern in settings.items():
            if pattern in content:
                # Find the line
                for line in content.split("\n"):
                    if pattern in line and not line.strip().startswith("#"):
                        print(f"✅ {name}: {line.strip()}")
                        break
            else:
                print(f"❌ {name}: NOT FOUND")
    else:
        print(f"❌ Conf.py not found: {conf_file}")


def check_generated_files():
    """Check what files AutoAPI generated."""
    autoapi_dir = Path("docs/source/autoapi")

    print("\n=== Generated Files Check ===")
    if autoapi_dir.exists():
        # Count RST files
        rst_files = list(autoapi_dir.rglob("*.rst"))
        print(f"Total RST files generated: {len(rst_files)}")

        # Show structure
        print("\nGenerated structure:")
        for f in sorted(rst_files)[:20]:  # Show first 20
            rel_path = f.relative_to(autoapi_dir)
            print(f"  {rel_path}")

        if len(rst_files) > 20:
            print(f"  ... and {len(rst_files) - 20} more files")
    else:
        print(f"❌ AutoAPI directory not found: {autoapi_dir}")


def check_build_output():
    """Check HTML output structure."""
    html_dir = Path("docs/build/html/autoapi")

    print("\n=== HTML Output Check ===")
    if html_dir.exists():
        # Count HTML files
        html_files = list(html_dir.rglob("*.html"))
        print(f"Total HTML files generated: {len(html_files)}")

        # Check for module-level pages
        module_dirs = [d for d in html_dir.iterdir() if d.is_dir()]
        print(f"Module directories: {len(module_dirs)}")

        if module_dirs:
            print("\nModule structure:")
            for d in sorted(module_dirs)[:10]:
                subfiles = list(d.rglob("*.html"))
                print(f"  {d.name}/ ({len(subfiles)} files)")
    else:
        print(f"❌ HTML directory not found: {html_dir}")


def check_template_errors():
    """Look for template errors in build output."""
    print("\n=== Template Error Check ===")
    print(
        "Run: poetry run sphinx-build -b html docs/source docs/build 2>&1 | grep -E 'ERROR|WARNING.*\.rst' | head -20"
    )
    print("\nCommon issues:")
    print("- 'Unexpected indentation' - Check Jinja2 template spacing")
    print("- 'Unknown target' - Missing references or macros")
    print("- 'Error parsing' - RST syntax errors in templates")


if __name__ == "__main__":
    check_template_files()
    check_conf_py()
    check_generated_files()
    check_build_output()
    check_template_errors()

    print("\n=== Quick Debug Commands ===")
    print("1. Test with default templates:")
    print("   mv docs/source/_autoapi_templates docs/source/_autoapi_templates.bak")
    print("   poetry run sphinx-build -b html docs/source docs/build --fresh-env")
    print("\n2. Test specific template:")
    print(
        "   poetry run python -m jinja2 docs/source/_autoapi_templates/python/module.rst"
    )
    print("\n3. Enable AutoAPI debug:")
    print("   Add to conf.py: autoapi_keep_files = True")
    print("\n4. Clean and rebuild:")
    print("   rm -rf docs/build docs/source/autoapi")
    print("   poetry run sphinx-build -b html docs/source docs/build -v")
