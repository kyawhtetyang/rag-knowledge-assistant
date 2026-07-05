import os
import re
import shutil
import sys
from restore_config import is_valid_version, sanitize_version_path, should_skip_restore_path


SCRIPT_PATH = os.path.abspath(__file__)
INSTALL_FOLDER = os.path.dirname(SCRIPT_PATH)
PROJECT_ROOT = os.path.dirname(INSTALL_FOLDER)
PARENT_ROOT = os.path.dirname(PROJECT_ROOT)
CURRENT_VERSION = os.path.basename(PROJECT_ROOT)
ALL_TXT = os.path.join(INSTALL_FOLDER, "all.txt")


EXTRA_REFILL_SKIP_SUFFIXES = (".DS_Store",)


def should_skip(rel_path):
    return should_skip_restore_path(rel_path, extra_suffixes=EXTRA_REFILL_SKIP_SUFFIXES)

def sanitize_snapshot_path(path):
    return sanitize_version_path(path)

def parse_snapshot_paths():
    """
    Read current-version headers from all.txt and return paths such as:
    docs/ , docs/file.png , App.tsx
    """
    if not os.path.isfile(ALL_TXT):
        print(f"❌ Snapshot file not found: {ALL_TXT}")
        sys.exit(1)

    paths = []
    pattern = re.compile(rf"^(#|//)\s*{re.escape(CURRENT_VERSION)}/\s*(.+)$")
    with open(ALL_TXT, "r", encoding="utf-8") as f:
        for raw in f:
            stripped = raw.strip()
            match = pattern.match(stripped)
            if not match:
                continue
            rel = sanitize_snapshot_path(match.group(2))
            if rel:
                paths.append(rel.replace("\\", "/"))
    return paths

def find_folder_only_paths(snapshot_paths):
    """
    folder-only = has `name/` entry but no `name/<file-or-subfolder>` entries.
    """
    all_paths = set(snapshot_paths)
    folder_only = []
    for path in sorted(all_paths):
        if not path.endswith("/"):
            continue
        has_children = any(other != path and other.startswith(path) for other in all_paths)
        if not has_children:
            folder_only.append(path.rstrip("/"))
    return folder_only

def under_any_refill_root(rel_path, refill_roots):
    normalized = rel_path.replace("\\", "/").strip("/")
    for root in refill_roots:
        if normalized == root or normalized.startswith(root + "/"):
            return True
    return False


def validate_versions(source_version):
    if not is_valid_version(CURRENT_VERSION):
        print(f"❌ Current folder version is invalid: {CURRENT_VERSION}")
        sys.exit(1)
    if not is_valid_version(source_version):
        print(f"❌ Source version is invalid: {source_version}")
        print("   Example values: v0, v1, v2.1")
        sys.exit(1)
    if source_version == CURRENT_VERSION:
        print("❌ Source version cannot be same as current version.")
        sys.exit(1)


def refill_from(source_root, refill_roots):
    copied_files = []
    skipped_existing = []
    skipped_rules = []

    for root, dirs, files in os.walk(source_root):
        rel_dir = os.path.relpath(root, source_root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""

        # Prune skipped directories during traversal.
        pruned = []
        for d in dirs:
            rel_d = f"{rel_dir}/{d}".strip("/")
            if should_skip(rel_d + "/"):
                skipped_rules.append(rel_d + "/")
            else:
                pruned.append(d)
        dirs[:] = pruned

        for filename in files:
            rel_file = f"{rel_dir}/{filename}".strip("/")
            if not under_any_refill_root(rel_file, refill_roots):
                continue
            if should_skip(rel_file):
                skipped_rules.append(rel_file)
                continue

            src_file = os.path.join(source_root, rel_file)
            dst_file = os.path.join(PROJECT_ROOT, rel_file)

            if os.path.exists(dst_file):
                skipped_existing.append(rel_file)
                continue

            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied_files.append(rel_file)

    return copied_files, skipped_existing, sorted(set(skipped_rules))


def main():
    print(f"🔖 Current version: {CURRENT_VERSION}")
    source_version = input("version = ").strip()
    validate_versions(source_version)

    source_root = os.path.join(PARENT_ROOT, source_version)
    if not os.path.isdir(source_root):
        print(f"❌ Source folder not found: {source_root}")
        sys.exit(1)

    snapshot_paths = parse_snapshot_paths()
    refill_roots = find_folder_only_paths(snapshot_paths)
    if not refill_roots:
        print("ℹ️ No manual-copy folder gaps detected from all.txt.")
        print("   Nothing to refill.")
        return

    print(f"\n🔄 Refill source: {source_root}")
    print(f"🎯 Refill target: {PROJECT_ROOT}\n")
    print("📌 Refill scope (folder-only paths from all.txt):")
    for root in refill_roots:
        print(f"   - {root}/")
    print("")

    copied, existing, skipped = refill_from(source_root, refill_roots)

    for rel in copied:
        print(f"✅ Copied missing file: {os.path.join(PROJECT_ROOT, rel)}")

    print("\n📊 Refill summary")
    print(f"   Copied missing files: {len(copied)}")
    print(f"   Already existed (unchanged): {len(existing)}")
    print(f"   Skipped by rules: {len(skipped)}")

    if skipped:
        print("   Skipped paths:")
        for rel in skipped[:30]:
            print(f"   - {rel}")
        if len(skipped) > 30:
            print(f"   ... and {len(skipped) - 30} more")


if __name__ == "__main__":
    main()
