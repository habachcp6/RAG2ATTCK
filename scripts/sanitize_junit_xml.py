"""Inspect and sanitize JUnit XML files for public release."""

from __future__ import annotations

import re
from pathlib import Path


def sanitize_junit_xml(input_path: Path, output_path: Path) -> dict[str, any]:
    content = input_path.read_text(encoding="utf-8")

    # 1. Replace hostname
    content, host_sub_count = re.subn(r'hostname="[^"]+"', 'hostname="runner-workstation"', content)

    # 2. Replace absolute paths:
    # Generic replacement patterns:
    patterns = [
        (
            r"[Dd]:[\\/]RAG2ATTCK-worktrees[\\/]finalization-20261003[\\/]?",
            "/workspaces/RAG2ATTCK/",
        ),
        (r"[Dd]:[\\/]RAG2ATT&CK[\\/]?", "/workspaces/RAG2ATTCK/"),
        (r"[Cc]:[\\/]Users[\\/][^\\/\"\'<>\s]+[\\/]\.codex[\\/]?", "/workspaces/RAG2ATTCK/.codex/"),
        (
            r"[Cc]:[\\/]Users[\\/][^\\/\"\'<>\s]+[\\/]AppData[\\/]Local[\\/]Programs[\\/]Python[\\/][^\\/\"\'<>\s]+[\\/]?",
            "/opt/python/",
        ),
        (r"[Cc]:[\\/]Users[\\/][^\\/\"\'<>\s]+[\\/]\.local[\\/]bin[\\/]?", "/usr/local/bin/"),
        (r"[Cc]:[\\/]Users[\\/][^\\/\"\'<>\s]+[\\/]?", "/home/runner/"),
    ]

    total_path_subs = 0
    for pat, repl in patterns:
        content, c = re.subn(pat, repl, content)
        total_path_subs += c

    # Normalize backslashes inside sanitized paths if needed
    content = re.sub(
        r'/workspaces/RAG2ATTCK/([^\s"\'<>]+)',
        lambda m: "/workspaces/RAG2ATTCK/" + m.group(1).replace("\\", "/"),
        content,
    )

    # Check for remaining drive letters
    remaining_drives = re.findall(r'[A-Za-z]:\\[^"\'<>\s]+', content)

    output_path.write_text(content, encoding="utf-8")

    return {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "host_replacements": host_sub_count,
        "path_replacements": total_path_subs,
        "remaining_windows_paths_count": len(remaining_drives),
        "remaining_samples": remaining_drives[:3],
    }


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    pkg_xml = repo_root / "reports/evidence/r7_package_tests.xml"
    full_xml = repo_root / "reports/evidence/r7_full_tests.xml"

    pkg_sanitized = repo_root / "reports/evidence/r8_package_tests_public.xml"
    full_sanitized = repo_root / "reports/evidence/r8_full_tests_public.xml"

    res1 = sanitize_junit_xml(pkg_xml, pkg_sanitized)
    res2 = sanitize_junit_xml(full_xml, full_sanitized)

    print("Sanitization Result for Package Tests:")
    print(res1)
    print("\nSanitization Result for Full Tests:")
    print(res2)
