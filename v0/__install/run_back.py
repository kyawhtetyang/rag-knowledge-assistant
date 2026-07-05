# load/new_versions/run_back.py
import fnmatch
import os
import posixpath

# =========================
# CONFIGURATION
# =========================
# Options: "top", "down", "alphabet"
FOLDER_MODE = "top"  # change as needed

# 🔘 OUTPUT SWITCHES
INCLUDE_COMMAND_LINE = False   # True / False
INCLUDE_FILE_TREE   = True    # True / False
INCLUDE_BODY        = True    # True / False

# 🔘 VISIBILITY CONTROL
INCLUDE_INVISIBLE_FILES   = True    # include .env, .gitignore
INCLUDE_INVISIBLE_FOLDERS = False   # mostly skip hidden folders

# 🔘 BINARY PLACEHOLDER MODE
# True  = keep old behavior and write "[binary file skipped]" placeholder blocks
# False = skip binary/non-text files entirely from output
KEEP_BINARY_PLACEHOLDER = False

# 🔘 PATH EXCLUSIONS (project-root relative)
# Example:
#   "backend/data" -> keep "backend/data/" entry, exclude everything under it.
#   "frontend/dist/" -> keep "frontend/dist/" entry, exclude descendants.
#
# Notes:
#   - You can write folder exclusions as:
#       "backend_fastapi/data"
#       "backend_fastapi/data/"
#       "./backend_fastapi/data"
#       "/absolute/path/to/project/backend_fastapi/data"
#   - For folder-style inputs (without wildcards), descendants are excluded and
#     the folder itself remains as a placeholder entry for restore/refill.
EXCLUDED_PATH_PATTERNS = [
    "backend/data",
    "backend_fastapi/data",
    "data",
]

# =========================
# BLACKLIST (folders and files to skip)
# =========================
BLACKLIST_FOLDERS = {
    "__install",
    ".git",
    ".venv",
    ".idea",
    ".vscode",
    "__pycache__",
    ".next",
    "dist",
    "node_modules",
    "_backup",
    "build",
    "target",
    "release",
    ".release",
    "out",
}

BLACKLIST_FILES = {
    ".DS_Store",
    "package-lock.json",
}

# 🚫 BINARY FILE EXTENSIONS (DO NOT EXPORT)
BLACKLIST_EXTENSIONS = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".ico",
    ".icns",
    ".webp",
    ".heic",
    ".gif",
    ".bmp",
    ".tiff",
    ".avif",
    ".zip",
}

INVISIBLE_FILE_WHITELIST = {".env", ".gitignore"}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL_FOLDER = os.path.join(PROJECT_ROOT, "__install")
OUTPUT_FILE = os.path.join(INSTALL_FOLDER, "all_back.txt")

LANG_MAP = {
    ".py": "python",
    ".html": "html",
    ".js": "javascript",
    ".css": "css",
    ".txt": "text",
    ".md": "markdown",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".sh": "shell",
    ".bat": "bat",
    ".tsx": "tsx",
    ".ts": "ts",
    ".sql": "sql",
    "": "shell",
}

# =========================
# HELPERS
# =========================
def normalize_rel_path(path: str) -> str:
    value = (path or "").strip().replace("\\", "/")
    if not value:
        return ""

    if os.path.isabs(value):
        abs_root = os.path.realpath(PROJECT_ROOT)
        abs_path = os.path.realpath(value)
        try:
            if os.path.commonpath([abs_root, abs_path]) != abs_root:
                return ""
        except ValueError:
            return ""
        value = os.path.relpath(abs_path, abs_root).replace("\\", "/")

    while value.startswith("./"):
        value = value[2:]

    normalized = posixpath.normpath(value)
    if normalized in ("", ".", ".."):
        return ""
    if normalized.startswith("../"):
        return ""
    return normalized.strip("/")

def parse_exclusion_rule(raw_pattern: str):
    """
    Parse one configured exclusion into a runtime rule:
      - ("children_only", "folder/path")
      - ("full", "file/or/exact/path")
      - ("glob", "glob/pattern")
    """
    raw = (raw_pattern or "").strip().replace("\\", "/")
    if not raw:
        return None

    is_children_marker = False
    if raw.endswith("/*"):
        is_children_marker = True
        raw = raw[:-2]
    elif raw.endswith("/"):
        is_children_marker = True
        raw = raw[:-1]

    normalized = normalize_rel_path(raw)
    if not normalized:
        return None

    if is_children_marker:
        return ("children_only", normalized)

    # Plain folder paths should "just work" without requiring "/*".
    if not any(ch in normalized for ch in "*?["):
        candidate_abs = os.path.join(PROJECT_ROOT, normalized)
        if os.path.isfile(candidate_abs):
            return ("full", normalized)
        return ("children_only", normalized)

    return ("glob", normalized)

def get_path_exclusion_state(rel_path: str, is_dir: bool) -> str:
    """
    Returns:
      - "none": included
      - "children_only": include dir node, skip descendants
      - "full": skip path entirely
    """
    rel = normalize_rel_path(rel_path)
    for raw_pattern in EXCLUDED_PATH_PATTERNS:
        rule = parse_exclusion_rule(raw_pattern)
        if not rule:
            continue
        kind, value = rule

        if kind == "children_only":
            if is_dir and rel == value:
                return "children_only"
            if rel.startswith(value + "/"):
                return "full"
            continue

        if kind == "full" and rel == value:
            return "full"

        if kind == "glob" and fnmatch.fnmatch(rel, value):
            return "full"

    return "none"

def is_skipped_file(name: str) -> bool:
    # Explicit filename blacklist
    if name in BLACKLIST_FILES:
        return True

    # 🚫 Binary extension blacklist
    _, ext = os.path.splitext(name)
    if ext.lower() in BLACKLIST_EXTENSIONS:
        return True

    # Hidden files handling
    if name.startswith(".") and name not in INVISIBLE_FILE_WHITELIST:
        if not INCLUDE_INVISIBLE_FILES:
            return True

    return False

def detect_version():
    return os.path.basename(PROJECT_ROOT)

def get_language(filename):
    if filename == ".env":
        return "shell"
    if filename == ".gitignore":
        return "text"
    _, ext = os.path.splitext(filename)
    return LANG_MAP.get(ext.lower(), "shell")

def write_folder(folder, version, f_out):
    f_out.write(f"### {folder}\n")
    f_out.write("```python\n")
    f_out.write(f"# {version}/{folder}/\n")
    f_out.write("```\n\n")

def write_file(file_path, rel_path, version, level, f_out):
    filename = os.path.basename(file_path)
    if is_skipped_file(filename):
        return

    lang = get_language(filename)
    content_lines = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                content_lines.append(line.rstrip())
    except UnicodeDecodeError:
        if KEEP_BINARY_PLACEHOLDER:
            content_lines = ["[binary file skipped]"]
        else:
            # Text-only snapshot mode: skip non-text files completely.
            return

    f_out.write(f"{'#' * level} {filename}\n")
    f_out.write(f"```{lang}\n")
    f_out.write(f"# {version}/{rel_path}\n")
    for line in content_lines:
        f_out.write(line + "\n")
    f_out.write("```\n\n")

# =========================
# ENTRY SORTING
# =========================
def sort_entries(path):
    entries = []

    for e in os.listdir(path):
        full = os.path.join(path, e)
        rel_path = os.path.relpath(full, PROJECT_ROOT).replace("\\", "/")
        exclusion_state = get_path_exclusion_state(rel_path, os.path.isdir(full))

        # Skip blacklisted folders
        if os.path.isdir(full) and e in BLACKLIST_FOLDERS:
            continue

        # Skip path-pattern excluded folders/files
        if exclusion_state == "full":
            continue

        # Skip invisible folders if flag is False
        if os.path.isdir(full) and e.startswith(".") and not INCLUDE_INVISIBLE_FOLDERS:
            continue

        # Skip blacklisted or skipped files
        if not os.path.isdir(full) and is_skipped_file(e):
            continue

        entries.append(e)

    if FOLDER_MODE == "top":
        folders = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        files = [e for e in entries if not os.path.isdir(os.path.join(path, e))]
        return sorted(folders) + sorted(files)
    elif FOLDER_MODE == "down":
        folders = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        files = [e for e in entries if not os.path.isdir(os.path.join(path, e))]
        return sorted(files) + sorted(folders)
    else:
        return sorted(entries)

# =========================
# TRAVERSAL (BODY)
# =========================
def traverse(path, level, f_out, version):
    entries = sort_entries(path)
    for entry in entries:
        full = os.path.join(path, entry)
        rel_path = os.path.relpath(full, PROJECT_ROOT).replace("\\", "/")
        if os.path.isdir(full):
            write_folder(rel_path, version, f_out)
            # For pattern ".../*", keep folder header but skip descendants.
            if get_path_exclusion_state(rel_path, True) == "children_only":
                continue
            traverse(full, level + 1, f_out, version)
        else:
            write_file(full, rel_path, version, level, f_out)

# =========================
# FILE TREE
# =========================
def generate_file_tree(path, prefix=""):
    lines = []
    entries = sort_entries(path)
    for i, entry in enumerate(entries):
        full = os.path.join(path, entry)
        rel_path = os.path.relpath(full, PROJECT_ROOT).replace("\\", "/")
        connector = "└─ " if i == len(entries) - 1 else "├─ "
        if os.path.isdir(full):
            exclusion_state = get_path_exclusion_state(rel_path, True)
            if exclusion_state == "children_only":
                lines.append(f"{prefix}{connector}{rel_path}/* (excluded)")
                continue

            lines.append(f"{prefix}{connector}{entry}/")
            new_prefix = prefix + ("    " if i == len(entries) - 1 else "│   ")
            lines.extend(generate_file_tree(full, new_prefix))
        else:
            lines.append(f"{prefix}{connector}{entry}")
    return lines

# =========================
# TOP BLOCKS
# =========================
def write_command_line_block(f_out, version):
    f_out.write("### __install/map.txt\n")
    f_out.write("```python\n")
    f_out.write(f"# {version}/__install/map.txt\n")
    f_out.write("cd ~/Downloads/v1/__install/\n")
    f_out.write("conda activate fk\n")
    f_out.write("python run_back.py\n\n")
    f_out.write("cd ~/Downloads/v1/\n")
    f_out.write("conda activate fk\n")
    f_out.write("npm install\n")
    f_out.write("npx vite\n")
    f_out.write("npm run dev\n")
    f_out.write("```\n\n")

def write_file_tree_block(f_out, version):
    f_out.write("### __install/map.txt\n")
    f_out.write("```python\n")
    f_out.write(f"# {version}/__install/map.txt\n")
    f_out.write(f"{version}/\n")
    for line in generate_file_tree(PROJECT_ROOT):
        f_out.write(line + "\n")
    f_out.write("```\n\n")

# =========================
# MAIN
# =========================
def traverse_and_write():
    version = detect_version()
    os.makedirs(INSTALL_FOLDER, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        if INCLUDE_COMMAND_LINE:
            write_command_line_block(f_out, version)
        if INCLUDE_FILE_TREE:
            write_file_tree_block(f_out, version)
        if INCLUDE_BODY:
            traverse(PROJECT_ROOT, 3, f_out, version)

def main():
    traverse_and_write()
    print(f"Generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
