#!/usr/bin/env python3
"""Fix bad file names in the data directory by removing spaces and special characters."""

import os
import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by replacing problematic characters."""
    # Extract base name and extension
    base, ext = os.path.splitext(filename)

    # Replace problematic characters
    # Spaces → underscores
    base = base.replace(" ", "_")

    # Remove or replace other problematic characters
    base = base.replace("(", "")
    base = base.replace(")", "")
    base = base.replace("[", "")
    base = base.replace("]", "")
    base = base.replace("'", "")
    base = base.replace('"', "")
    base = base.replace("/", "_")
    base = base.replace("\\", "_")
    base = base.replace("<", "")
    base = base.replace(">", "")
    base = base.replace(":", "_")
    base = base.replace("|", "_")
    base = base.replace("?", "")
    base = base.replace("*", "")

    # Remove any double underscores
    base = re.sub(r"_+", "_", base)

    # Remove leading/trailing underscores
    base = base.strip("_")

    # If the filename becomes empty, use a default
    if not base:
        base = "unnamed"

    return base + ext


def fix_bad_filenames(directory: str):
    """Fix all bad filenames in the given directory."""
    data_dir = Path(directory)

    if not data_dir.exists():
        print(f"Directory {directory} does not exist!")
        return

    renamed_count = 0
    error_count = 0

    # Find all files with problematic names
    for root, _, files in os.walk(data_dir):
        root_path = Path(root)

        for filename in files:
            # Check if filename needs fixing
            if any(
                char in filename
                for char in [
                    " ",
                    "(",
                    ")",
                    "[",
                    "]",
                    "'",
                    '"',
                    "<",
                    ">",
                    ":",
                    "|",
                    "?",
                    "*",
                ]
            ):
                old_path = root_path / filename
                new_filename = sanitize_filename(filename)
                new_path = root_path / new_filename

                # Handle conflicts by adding a number
                if new_path.exists() and new_path != old_path:
                    base, ext = os.path.splitext(new_filename)
                    counter = 1
                    while new_path.exists():
                        new_filename = f"{base}_{counter}{ext}"
                        new_path = root_path / new_filename
                        counter += 1

                try:
                    print(f"Renaming: {old_path.name} → {new_filename}")
                    old_path.rename(new_path)
                    renamed_count += 1
                except Exception as e:
                    print(f"  ERROR: Failed to rename {old_path}: {e}")
                    error_count += 1

    print(f"\n✅ Renamed {renamed_count} files")
    if error_count > 0:
        print(f"❌ Failed to rename {error_count} files")


if __name__ == "__main__":
    # Fix bad filenames in the data directory
    print("Fixing bad filenames in data directory...")
    fix_bad_filenames("data")

    print("\nDone!")
