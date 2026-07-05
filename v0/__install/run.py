# -----------------------
# STEP 0: CONFIG / CONSTANTS 
# -----------------------
import os
import shutil
import hashlib
import re
import sys
from restore_config import is_valid_version, sanitize_version_path, should_skip_restore_path
from restore_config import normalize_snapshot_rel_path, safe_join_project_root

# -----------------------
# STEP 0a: Detect VERSION dynamically
# -----------------------
SCRIPT_PATH = os.path.abspath(__file__)
INSTALL_FOLDER = os.path.dirname(SCRIPT_PATH)          # __install/
PROJECT_ROOT = os.path.dirname(INSTALL_FOLDER)        # v* folder
VERSION = os.path.basename(PROJECT_ROOT)              # 'v0', 'v1', etc.

if not is_valid_version(VERSION):
    print(f"❌ ERROR: Version folder '{VERSION}' is invalid.")
    print("✔ Allowed versions:")
    print("   - Major only: v0 to v99")
    print("   - Minor: v0.1 to v99.99 (no .0, max 2 digits)")
    print("   Examples: v0, v1, v1.1, v3.9, v4.11")
    sys.exit(1)

INPUT_FILE = os.path.join(INSTALL_FOLDER, "all.txt")
HASH_FILE = os.path.join(INSTALL_FOLDER, ".build_hash")

# -----------------------
# TXT Separators (multiple supported)
# -----------------------
TXT_SEPARATORS = {
    "# ==========================================================",
    "// =========================================================="
}
DELETE_SEPARATOR = True   # True = remove separators, False = keep
DELETE_COMMENTS = False
DELETE_TITLES = True

TO_DELETE_LINES = {
                   "```py", "```python",
                   "```html", "```html",
                   "```js", "```javascript",
                   "```css", "```css",
                   "```txt", "```text",
                   "```md", "```markdown",
                   "```json", "```json",
                   "```yml", "```yaml",
                   "```yaml", "```yaml",
                   "```sh", "```shell",
                   "```bat", "```bat",
                   "```bash", "```bash",
                   "```tsx", "```ts",
                   "```ts", "```ts",
                   "```sql", "```sql",
                   "```copy code", "```"
                   }

# -----------------------
# STEP 1: UTILITY FUNCTIONS
# -----------------------
def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def safe_remove(path):
    if os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)

def has_existing_project(path):
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            if name != "__install" and not name.startswith('.'):
                return True
    return False

def read_input_file():
    with open(INPUT_FILE, "r") as f:
        return f.readlines()

def detect_versions_in_input(lines):
    versions = set()
    pattern = re.compile(r"^(#|//)\s*(v\d+(?:\.\d+)?)/")
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            versions.add(match.group(2))
    return sorted(versions)

def report_restore_gaps(file_blocks, skipped_paths, source_version_hint=None):
    """
    Show a warning when snapshot content is not fully reconstructable.
    """
    folder_only_paths = []
    all_paths = set(file_blocks.keys())
    for path in all_paths:
        if not path.endswith("/"):
            continue
        has_children = any(other != path and other.startswith(path) for other in all_paths)
        if not has_children:
            folder_only_paths.append(path)

    if not skipped_paths and not folder_only_paths:
        return

    print("\n⚠️ Restore incomplete: some paths were not reconstructed automatically.")

    if skipped_paths:
        print("   Skipped by safety rules:")
        for path in skipped_paths:
            print(f"   - {path}")

    if folder_only_paths:
        print("   Folders created as empty (no file entries in all.txt):")
        for path in folder_only_paths:
            print(f"   - {path}*  (copy/create files manually)")
            if source_version_hint and source_version_hint != VERSION:
                source_guess = os.path.join(os.path.dirname(PROJECT_ROOT), source_version_hint, path.rstrip("/"))
                print(f"     suggested source: {source_guess}")

# -----------------------
# STEP 2: PROMPT LAYERS
# -----------------------
def prompt_layers():
    overwrite = False
    all_txt_changed = False

    project_exists = has_existing_project(PROJECT_ROOT)
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()
        current_hash = file_hash(INPUT_FILE)
        all_txt_changed = current_hash != last_hash
    else:
        all_txt_changed = True

    if project_exists:
        reset_mode = input("🧹 Reset existing project before rebuild? (y/n): ").lower().strip() == "y"
        if reset_mode:
            print(f"\n🧨 Resetting project folder: {PROJECT_ROOT}")
            for item in os.listdir(PROJECT_ROOT):
                if item == "__install" or item.startswith('.'):
                    continue
                safe_remove(os.path.join(PROJECT_ROOT, item))
            print("✅ Old project files removed except __install\n")
            overwrite = True
            return overwrite, all_txt_changed

    if project_exists and not overwrite:
        confirm_overwrite = input("⚠️ Overwrite existing files if found? (y/n): ").lower().strip() == "y"
        if confirm_overwrite:
            overwrite = True

    if all_txt_changed and not overwrite:
        update_mode = input("🆕 all.txt has changed — update project? (y/n): ").lower().strip() == "y"
        if update_mode:
            overwrite = True

    return overwrite, all_txt_changed

# -----------------------
# STEP 3: PROCESS / CLEAN DATA
# -----------------------
def clean_lines(lines, prefix=VERSION + "/"):
    cleaned_lines = []
    current_file = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in TO_DELETE_LINES:
            continue

        if DELETE_SEPARATOR and stripped in TXT_SEPARATORS:
            if not (current_file and current_file.endswith(".txt")):
                continue

        match = re.match(r"^(#|//)\s*" + re.escape(prefix) + r"\s*(.+)$", stripped)
        if match:
            current_file = sanitize_version_path(match.group(2))
            cleaned_lines.append(line.rstrip())
            continue

        if current_file and current_file.endswith(".txt") and stripped in TXT_SEPARATORS:
            cleaned_lines.append(line.rstrip())
            continue

        if stripped.startswith("#") and not re.match(r"^(#|//)\s*" + re.escape(prefix), stripped):
            if DELETE_COMMENTS:
                continue
        if DELETE_TITLES and re.match(r"^#{3,}\s", stripped):
            continue

        cleaned_lines.append(line.rstrip())
    return cleaned_lines

# -----------------------
# STEP 4: ORGANIZE / STRUCTURE FILE BLOCKS
# -----------------------
def build_file_blocks(cleaned_lines, prefix=VERSION + "/"):
    file_blocks = {}
    block_lines = []
    block_number = None
    current_file = None
    number_pattern = re.compile(r"#\s+(\d+)[/\s]")

    for i, line_strip in enumerate(cleaned_lines):
        match = re.match(r"^(#|//)\s*" + re.escape(prefix) + r"\s*(.+)$", line_strip)
        if match:
            if current_file and block_lines:
                file_blocks.setdefault(current_file, []).append((block_number, block_lines))
            raw_path = sanitize_version_path(match.group(2))
            try:
                current_file = normalize_snapshot_rel_path(raw_path)
            except ValueError as exc:
                print(f"⏭️ Skipped unsafe snapshot header: {raw_path} ({exc})")
                current_file = None
            block_lines = []
            block_number = None
            if i + 1 < len(cleaned_lines):
                next_line = cleaned_lines[i + 1].strip()
                match_num = number_pattern.match(next_line)
                if match_num:
                    block_number = int(match_num.group(1))
            continue
        if current_file:
            block_lines.append(line_strip)

    if current_file and block_lines:
        file_blocks.setdefault(current_file, []).append((block_number, block_lines))
    return file_blocks

# -----------------------
# STEP 5: SAVE FILES
# -----------------------
def save_blocks(file_blocks, overwrite=True):
    skipped_paths = []
    for current_file, blocks in file_blocks.items():
        try:
            safe_rel_path, abs_path = safe_join_project_root(PROJECT_ROOT, current_file)
        except ValueError as exc:
            print(f"⏭️ Skipped unsafe restore path: {current_file} ({exc})")
            skipped_paths.append(current_file)
            continue

        current_file = safe_rel_path
        if should_skip_restore_path(current_file):
            print(f"⏭️ Skipped binary/sensitive path: {current_file}")
            skipped_paths.append(current_file)
            continue

        blocks_sorted = sorted(blocks, key=lambda x: (x[0] is None, x[0] if x[0] is not None else 0))
        combined_lines = []
        for idx, (_, lines_block) in enumerate(blocks_sorted):
            if idx > 0 and current_file.endswith("__install/map.txt"):
                combined_lines.append(next(iter(TXT_SEPARATORS)))  # insert one separator
            combined_lines.extend(lines_block)

        if current_file.endswith("/"):
            os.makedirs(abs_path, exist_ok=True)
            print(f"📁 Created folder: {abs_path}")
            continue
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if not overwrite and os.path.exists(abs_path):
            print(f"⏭️ Exists, overwrite disabled: {abs_path}")
            continue

        with open(abs_path, "w") as f_out:
            for line in combined_lines:
                f_out.write(line + "\n")
        print(f"✅ Created/Updated: {abs_path}")
    return skipped_paths

# -----------------------
# MAIN FUNCTION
# -----------------------
def main():
    print(f"🔖 Detected version folder: {VERSION}")

    overwrite, all_txt_changed = prompt_layers()
    lines = read_input_file()
    versions_in_input = detect_versions_in_input(lines)
    source_version_hint = next((v for v in versions_in_input if v != VERSION), None)
    cleaned_lines = clean_lines(lines)
    file_blocks = build_file_blocks(cleaned_lines)
    skipped_paths = save_blocks(file_blocks, overwrite=overwrite)
    report_restore_gaps(file_blocks, skipped_paths, source_version_hint=source_version_hint)

    current_hash = file_hash(INPUT_FILE)
    with open(HASH_FILE, "w") as f:
        f.write(current_hash)

    print(f"\n🎯 All files safely created inside: {PROJECT_ROOT}")
    print("💾 Hash saved for next comparison.")

# -----------------------
# SCRIPT ENTRY POINT
# -----------------------
if __name__ == "__main__":
    main()
