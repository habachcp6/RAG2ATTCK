"""Filesystem path safety validation for experiment execution."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class UnsafeOutputPathError(ValueError):
    """Raised when an untrusted output path violates safety invariants or cannot be inspected."""


def is_symlink_or_junction(target: Path | str) -> bool:
    """Detect whether a path is a symbolic link, directory junction, or reparse link.

    Covers POSIX symlinks as well as Windows symlinks, directory junctions,
    and all reparse point tags. Fails closed on any filesystem inspection error
    (such as PermissionError), only treating non-existent components (FileNotFoundError)
    as non-links.

    Raises:
        UnsafeOutputPathError: If inspecting the filesystem entry fails unexpectedly.
    """
    p = Path(target)
    try:
        lst = os.lstat(p)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise UnsafeOutputPathError(f"cannot safely inspect path component: {p}") from exc

    if stat.S_ISLNK(lst.st_mode):
        return True

    # Reject all Windows reparse tags (symlinks, junctions/mount-points, appexec links, etc.)
    tag = getattr(lst, "st_reparse_tag", 0)
    if tag != 0:
        return True

    reparse_attr = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    file_attrs = getattr(lst, "st_file_attributes", 0)
    if file_attrs & reparse_attr:
        return True

    try:
        if p.is_symlink() or os.path.islink(p):
            return True
        if hasattr(p, "is_junction") and p.is_junction():
            return True
        if hasattr(os.path, "isjunction") and os.path.isjunction(p):
            return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise UnsafeOutputPathError(f"cannot safely inspect path component: {p}") from exc

    return False


def validate_untrusted_output_path(path: Path | str) -> Path:
    """Validate and canonicalize an untrusted experiment output directory path.

    Defends against symlink, directory junction, and reparse-point path traversal
    defects by validating raw path components BEFORE resolution, followed by defensive
    post-resolution checks. Fails closed on any inspection error.

    Threat Model:
        The path validator protects against pre-existing symlinks, directory
        junctions, and reparse-point traversal in untrusted output path inputs.
        Assumption: Concurrent hostile filesystem mutation (TOCTOU race by another
        local process) is outside the single-tenant local execution threat model
        of the research runner.

    Validation rules:
    1. Reject symlink root on raw path before resolution.
    2. Reject existing symlink, junction, or reparse ancestor components of the absolute raw path.
    3. Reject existing symlink, junction, or reparse ancestor components of the raw path.
    4. Canonicalize/resolve only after pre-resolution checks succeed.
    5. Defensively verify resolved path and all resolved ancestor components are not symlinks.

    Args:
        path: Path or string representing the candidate output directory.

    Returns:
        Canonicalized safe resolved Path.

    Raises:
        ValueError / UnsafeOutputPathError: If the target path or any ancestor component
            is a symlink, junction, reparse point, or fails inspection.
    """
    if isinstance(path, str) and not path.strip():
        raise ValueError("output directory path must not be empty")

    raw_path = Path(path)

    # 1. Reject symlink root before resolution
    if is_symlink_or_junction(raw_path):
        raise ValueError("symlink output directory rejected")

    raw_abs = raw_path.absolute()
    if is_symlink_or_junction(raw_abs):
        raise ValueError("symlink output directory rejected")

    # 2. Reject existing symlink parent components in raw path ancestors
    for parent in reversed(raw_abs.parents):
        if is_symlink_or_junction(parent):
            raise ValueError("symlink output directory rejected")

    for parent in reversed(raw_path.parents):
        if is_symlink_or_junction(parent):
            raise ValueError("symlink output directory rejected")

    # 3. Canonicalize / resolve only after pre-resolution checks pass
    try:
        resolved = raw_path.resolve()
    except OSError as exc:
        raise UnsafeOutputPathError(f"cannot safely resolve path: {raw_path}") from exc

    # 4. Defensive post-resolution checks
    if is_symlink_or_junction(resolved):
        raise ValueError("symlink output directory rejected")

    for parent in reversed(resolved.parents):
        if is_symlink_or_junction(parent):
            raise ValueError("symlink output directory rejected")

    return resolved


__all__ = ["UnsafeOutputPathError", "is_symlink_or_junction", "validate_untrusted_output_path"]
