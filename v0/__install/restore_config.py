import os
import posixpath
import re


VERSION_PATTERN = r"^v([0-9]|[1-9][0-9])(\.([1-9]|[1-9][0-9]))?$"

# Paths that must never be reconstructed/refilled from snapshots.
SKIP_RESTORE_PREFIXES = (
    ".git/",
    "__install/",
    "node_modules/",
    "dist/",
    "build/",
    "target/",
    "release/",
    "out/",
    ".venv/",
    "__pycache__/",
    "frontend/src-tauri/binaries/",
    "frontend/src-tauri/target/",
    "frontend/node_modules/",
    "frontend/dist/",
    "landing/node_modules/",
    "landing/dist/",
    "backend/.venv/",
    "backend/__pycache__/",
    "backend/dist/",
    "backend/build/",
    "electron/dist/",
    "electron/out/",
    "electron/release/",
    "android/",
    "ios/",
)

SKIP_RESTORE_CONTAINS = (
    ".app/Contents/MacOS/",
    ".app/Contents/Frameworks/",
)

SKIP_RESTORE_SUFFIXES = (
    ".pyc",
    ".dmg",
    ".apk",
    ".aab",
    ".ipa",
    ".exe",
)


def is_valid_version(version):
    return bool(re.match(VERSION_PATTERN, version))


def sanitize_version_path(path):
    return re.split(r"\s|->", path.strip())[0]


def normalize_snapshot_rel_path(path):
    """
    Normalize a snapshot path and ensure it remains a relative project path.
    Keeps trailing slash for folder entries.
    """
    candidate = sanitize_version_path(path)
    if not candidate or "\x00" in candidate:
        raise ValueError("empty or invalid path")

    had_trailing_slash = candidate.endswith("/")
    normalized = posixpath.normpath(candidate.replace("\\", "/"))

    if normalized in ("", ".", ".."):
        raise ValueError("invalid relative path")
    if normalized.startswith("../") or normalized.startswith("/"):
        raise ValueError("path escapes project root")
    if "/../" in f"/{normalized}/":
        raise ValueError("path escapes project root")

    if had_trailing_slash:
        normalized += "/"
    return normalized


def safe_join_project_root(project_root, rel_path):
    """
    Join project_root + rel_path and ensure the resolved path is inside project_root.
    Returns normalized relative path and absolute resolved path.
    """
    normalized_rel = normalize_snapshot_rel_path(rel_path)
    rel_for_fs = normalized_rel.rstrip("/")

    abs_root = os.path.realpath(project_root)
    abs_target = os.path.realpath(os.path.join(abs_root, rel_for_fs))

    if os.path.commonpath([abs_root, abs_target]) != abs_root:
        raise ValueError("resolved path is outside project root")

    return normalized_rel, abs_target


def should_skip_restore_path(rel_path, extra_suffixes=()):
    normalized = rel_path.strip().replace("\\", "/")
    if any(normalized.startswith(prefix) for prefix in SKIP_RESTORE_PREFIXES):
        return True
    if any(token in normalized for token in SKIP_RESTORE_CONTAINS):
        return True
    if any(normalized.endswith(suffix) for suffix in SKIP_RESTORE_SUFFIXES):
        return True
    if any(normalized.endswith(suffix) for suffix in extra_suffixes):
        return True
    return False
