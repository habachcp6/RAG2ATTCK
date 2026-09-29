"""Filesystem path safety validation for experiment execution."""

from __future__ import annotations

import os
import stat
from pathlib import Path


def is_symlink_or_junction(target: Path | str) -> bool:
    """Detect whether a path is a symbolic link, directory junction, or reparse link.

    Covers POSIX symlinks as well as Windows symlinks, directory junctions,
    and mount-point reparse tags. Handles non-existent targets and permission
    errors safely without raising unhandled OS exceptions.
    """
    p = Path(target)
    try:
        if p.is_symlink() or os.path.islink(p):
            return True
    except (OSError, ValueError):
        pass

    try:
        if hasattr(p, "is_junction") and p.is_junction():
            return True
        if hasattr(os.path, "isjunction") and os.path.isjunction(p):
            return True
    except (OSError, ValueError):
        pass

    try:
        lst = os.lstat(p)
        if stat.S_ISLNK(lst.st_mode):
            return True
        tag = getattr(lst, "st_reparse_tag", 0)
        mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
        symlink_tag = getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C)
        if tag in (mount_point_tag, symlink_tag):
            return True
    except (OSError, ValueError):
        pass

    return False


def validate_untrusted_output_path(path: Path | str) -> Path:
    """Validate and canonicalize an untrusted experiment output directory path.

    Defends against symlink and directory junction path traversal defects
    by validating raw path components BEFORE resolution, followed by defensive
    post-resolution checks.

    Validation rules:
    1. Reject symlink root on raw path before resolution.
    2. Reject existing symlink or junction ancestor components of the absolute raw path.
    3. Reject existing symlink or junction ancestor components of the raw path.
    4. Canonicalize/resolve only after pre-resolution checks succeed.
    5. Defensively verify resolved path and all resolved ancestor components are not symlinks.

    Args:
        path: Path or string representing the candidate output directory.

    Returns:
        Canonicalized safe resolved Path.

    Raises:
        ValueError: If the target path or any ancestor component is a symlink or junction.
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
    resolved = raw_path.resolve()

    # 4. Defensive post-resolution checks
    if is_symlink_or_junction(resolved):
        raise ValueError("symlink output directory rejected")

    for parent in reversed(resolved.parents):
        if is_symlink_or_junction(parent):
            raise ValueError("symlink output directory rejected")

    return resolved


__all__ = ["is_symlink_or_junction", "validate_untrusted_output_path"]
