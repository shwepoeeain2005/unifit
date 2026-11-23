"""Restore university pages destroyed by case-only renames on Windows."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT / "universities"
TARGET_RE = re.compile(
    r'url=(?P<target>[^">\s]+)|location\.replace\([\'"](?P<js>[^\'"]+)[\'"]\)',
    re.I,
)


def main() -> None:
    damaged = []
    for path in sorted(UNI.glob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "this page moved" not in text.lower():
            continue
        match = TARGET_RE.search(text)
        if not match:
            continue
        target = match.group("target") or match.group("js")
        if path.name.casefold() == Path(target).name.casefold():
            damaged.append((path.name, Path(target).name))

    print("damaged case-only pages", len(damaged))
    for old_name, new_name in damaged:
        # Prefer restoring original casing from git, then rewrite to lowercase content file.
        candidates = [old_name]
        # Also try common original casings from git ls-files
        restored = False
        for candidate in candidates:
            rel = f"universities/{candidate}"
            result = subprocess.run(
                ["git", "show", f"HEAD:{rel}"],
                cwd=ROOT,
                capture_output=True,
            )
            if result.returncode != 0:
                # try listing matching file from git
                listed = subprocess.run(
                    ["git", "ls-files", "universities"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                match = next(
                    (
                        line.strip()
                        for line in listed.stdout.splitlines()
                        if line.strip().casefold() == rel.casefold()
                    ),
                    None,
                )
                if not match:
                    print("NO GIT SOURCE", old_name)
                    continue
                result = subprocess.run(
                    ["git", "show", f"HEAD:{match}"],
                    cwd=ROOT,
                    capture_output=True,
                )
                if result.returncode != 0:
                    print("FAILED", old_name)
                    continue
            content = result.stdout
            # Write restored bytes to the current path (Windows keeps one casing)
            (UNI / old_name).write_bytes(content)
            print("restored", old_name, "bytes", len(content))
            restored = True
            break
        if not restored:
            print("UNRECOVERED", old_name)


if __name__ == "__main__":
    main()
