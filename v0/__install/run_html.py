"""
Universal HTML Merger (v5-safe-universal)
-------------------------------------------
✅ Auto-inlines CSS, JS, and template content from base.html
✅ Handles Flask-style {{ url_for('static', filename='...') }}
✅ Safe fallback for any {{ url_*() }} function
✅ Strips {% extends ... %} automatically to avoid duplicate footers
✅ Works even if /static folder or files are missing
✅ Saves merged outputs to /__install/sample_html/
✅ Produces standalone HTML files (no dependencies)
"""

import os
import re
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # /v5/__install
ROOT_DIR = os.path.dirname(BASE_DIR)                           # /v5
TEMPLATE_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
OUTPUT_DIR = os.path.join(BASE_DIR, "sample_html")

os.makedirs(OUTPUT_DIR, exist_ok=True)

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def make_safe_url_func(name):
    def safe_func(*args, **kwargs):
        filename = kwargs.get("filename", "")
        return f"../{filename}" if filename else ""
    return safe_func

for name in ["url_for", "url_path", "url_image", "url_video", "url_css", "url_js"]:
    env.globals[name] = make_safe_url_func(name)

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

css_path = os.path.join(STATIC_DIR, "css", "style.css")
js_path = os.path.join(STATIC_DIR, "js", "script.js")

css_content = f"<style>\n{read_file(css_path)}\n</style>" if os.path.exists(css_path) else ""
js_content = f"<script>\n{read_file(js_path)}\n</script>" if os.path.exists(js_path) else ""

base_html_path = os.path.join(TEMPLATE_DIR, "base.html")
if not os.path.exists(base_html_path):
    raise FileNotFoundError(f"Missing required template: {base_html_path}")

base_html = read_file(base_html_path)

template_files = [
    f for f in os.listdir(TEMPLATE_DIR)
    if f.endswith(".html") and f != "base.html"
]

if not template_files:
    print("⚠️ No template files found to merge. Make sure you have .html templates in /templates/")
else:
    print(f"🔍 Found {len(template_files)} template(s): {', '.join(template_files)}")

def merge_with_base(html_body):
    merged = base_html

    if css_content:
        merged = re.sub(
            r'<link[^>]*(bootstrap|min\.css|style\.css)[^>]*>',
            css_content,
            merged,
            flags=re.IGNORECASE
        )

    if js_content:
        merged = re.sub(
            r'<script[^>]*(bootstrap|min\.js|script\.js)[^>]*></script>',
            js_content,
            merged,
            flags=re.IGNORECASE
        )

    if "{% block content %}{% endblock %}" in merged:
        merged = merged.replace("{% block content %}{% endblock %}", html_body)
    elif "{{ content }}" in merged:
        merged = merged.replace("{{ content }}", html_body)
    else:
        merged = re.sub(r"<body[^>]*>", r"\g<0>\n" + html_body, merged)

    return merged

for tpl_name in template_files:
    template_path = os.path.join(TEMPLATE_DIR, tpl_name)

    raw_content = read_file(template_path)
    raw_content = re.sub(r'{%\s*extends\s+["\'].*?["\']\s*%}', '', raw_content)

    template = env.from_string(raw_content)
    html_body = template.render(username="alice")

    merged_html = merge_with_base(html_body)

    output_file = os.path.join(OUTPUT_DIR, tpl_name.replace(".html", "_merged.html"))
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merged_html)

    print(f"✅ Generated: {output_file}")

print("\n✅ All templates successfully merged into /__install/sample_html/")


