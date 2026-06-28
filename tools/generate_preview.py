#!/usr/bin/env python3
"""Generate a standalone HTML preview for a PennyPress course bundle."""

import sys
import json
import markdown
from pathlib import Path


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f0f0e8; color: #1a1a1a; height: 100vh; overflow: hidden; }
.layout { display: flex; height: 100vh; }

/* Sidebar */
.sidebar { width: 280px; min-width: 280px; background: #fff;
           border-right: 1px solid #e0e0d8; display: flex;
           flex-direction: column; overflow: hidden; }
.sidebar-header { padding: 20px 16px 12px; border-bottom: 1px solid #e0e0d8; }
.sidebar-label { font-size: 13px; font-weight: 700; color: #2d6a4f;
                 letter-spacing: 0.05em; margin-bottom: 8px; }
.course-title { font-size: 13px; font-weight: 600; color: #222;
                line-height: 1.4; margin-bottom: 4px; }
.card-count { font-size: 12px; color: #888; }
.toc-nav { flex: 1; overflow-y: auto; padding: 8px 0; }

/* TOC items */
.toc-item { padding: 8px 16px; font-size: 13px; cursor: pointer;
            line-height: 1.4; color: #333; transition: background 0.1s; }
.toc-item:hover { background: #f0faf5; }
.toc-item.active { background: #e8f5ee; color: #2d6a4f;
                   font-weight: 600; border-left: 3px solid #2d6a4f;
                   padding-left: 13px; }
.toc-chapter { font-weight: 700; color: #111; font-size: 13px;
               padding: 10px 16px 4px; cursor: default; }
.toc-chapter:hover { background: transparent; }
.toc-section { padding-left: 24px; }
.toc-section.active { padding-left: 21px; }
.toc-subsection { padding-left: 36px; }
.toc-subsection.active { padding-left: 33px; }
.toc-children { }

/* Main content */
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.cards-container { flex: 1; overflow-y: auto; padding: 32px 40px; }
.card-panel { max-width: 780px; margin: 0 auto; }
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px;
               padding-bottom: 16px; border-bottom: 2px solid #2d6a4f; }
.card-badge { background: #2d6a4f; color: #fff; font-size: 11px; font-weight: 700;
              padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.card-title { font-size: 18px; font-weight: 700; color: #111; line-height: 1.3; }

/* Card body markdown styles */
.card-body { background: #fff; border-radius: 8px; padding: 28px 32px;
             box-shadow: 0 1px 4px rgba(0,0,0,0.08); line-height: 1.8; }
.card-body h1 { font-size: 20px; font-weight: 700; margin: 0 0 16px;
                color: #1a1a1a; border-bottom: 1px solid #e8e8e0;
                padding-bottom: 8px; }
.card-body h2 { font-size: 17px; font-weight: 700; margin: 24px 0 10px;
                color: #2d2d2d; }
.card-body h3 { font-size: 15px; font-weight: 600; margin: 20px 0 8px;
                color: #333; }
.card-body p { margin-bottom: 14px; color: #333; }
.card-body ul, .card-body ol { margin: 0 0 14px 20px; }
.card-body li { margin-bottom: 6px; }
.card-body blockquote { border-left: 4px solid #52b788; padding: 10px 16px;
                         background: #f0faf5; margin: 16px 0; color: #1a5c3a;
                         border-radius: 0 4px 4px 0; }
.card-body img { max-width: 100%; height: auto; border-radius: 6px;
                 margin: 16px 0; display: block; }
.card-body code { background: #f4f4f0; padding: 2px 6px; border-radius: 3px;
                  font-size: 0.9em; font-family: 'Courier New', monospace; }
.card-body pre { background: #1e1e1e; color: #d4d4d4; padding: 16px;
                 border-radius: 6px; overflow-x: auto; margin: 16px 0; }
.card-body pre code { background: none; padding: 0; color: inherit; }
.card-body strong { font-weight: 700; color: #111; }
.card-body table { border-collapse: collapse; width: 100%; margin: 16px 0; }
.card-body th, .card-body td { border: 1px solid #ddd; padding: 8px 12px;
                                text-align: left; }
.card-body th { background: #f4f4f0; font-weight: 600; }

/* Navigation bar */
.nav-bar { display: flex; align-items: center; justify-content: space-between;
           padding: 12px 40px; background: #fff;
           border-top: 1px solid #e0e0d8; }
.nav-btn { background: #fff; border: 1px solid #ccc; color: #333;
           padding: 8px 20px; border-radius: 6px; cursor: pointer;
           font-size: 14px; transition: all 0.15s; }
.nav-btn:hover:not(:disabled) { border-color: #2d6a4f; color: #2d6a4f; }
.nav-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.nav-btn-next { background: #2d6a4f; color: #fff; border-color: #2d6a4f; }
.nav-btn-next:hover:not(:disabled) { background: #245a41; color: #fff; }
.nav-counter { font-size: 14px; color: #555; font-weight: 500; }
"""

JS = """
var current = 0;
var total = 0;

function init() {
  total = document.querySelectorAll('.card-panel').length;
  showCard(0);
}

function showCard(n) {
  if (n < 0 || n >= total) return;
  document.querySelectorAll('.card-panel').forEach(function(el, i) {
    el.style.display = i === n ? '' : 'none';
  });
  document.querySelectorAll('.toc-item[data-card-index]').forEach(function(el) {
    el.classList.toggle('active', parseInt(el.dataset.cardIndex) === n);
  });
  document.getElementById('counter').textContent = (n + 1) + ' / ' + total;
  document.getElementById('btn-prev').disabled = n === 0;
  document.getElementById('btn-next').disabled = n === total - 1;
  document.querySelector('.cards-container').scrollTop = 0;
  current = n;
}

function prevCard() { showCard(current - 1); }
function nextCard() { showCard(current + 1); }

document.addEventListener('DOMContentLoaded', init);
"""


def load_config(course_dir: Path) -> dict:
    with open(course_dir / "config.json", encoding="utf-8") as f:
        return json.load(f)


def convert_card(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # ../images/ → images/ (preview.html is one level above cards/)
    text = text.replace("../images/", "images/")
    md = markdown.Markdown(extensions=["extra", "nl2br"])
    return md.convert(text)


def find_leaf_title(toc: list, filename: str) -> str:
    for node in toc:
        if node.get("filename") == filename:
            return node.get("title", "")
        found = find_leaf_title(node.get("children", []), filename)
        if found:
            return found
    return filename


def render_toc_node(node: dict, card_index: dict) -> str:
    node_type = node.get("type", "section")
    title = node.get("title", "")
    filename = node.get("filename")
    children = node.get("children", [])

    if filename is not None:
        idx = card_index.get(filename, 0)
        css = f"toc-item toc-{node_type}"
        return (
            f'<div class="{css}" data-card-index="{idx}" '
            f'onclick="showCard({idx})">{title}</div>'
        )

    children_html = "".join(render_toc_node(c, card_index) for c in children)
    header_css = "toc-item toc-" + node_type
    if node_type == "chapter":
        header_css += " toc-chapter"
    return (
        f'<div class="toc-group">'
        f'<div class="{header_css}">{title}</div>'
        f'<div class="toc-children">{children_html}</div>'
        f'</div>'
    )


def build_html(config: dict, cards_html: list) -> str:
    title = config.get("title", "강좌 미리보기")
    toc = config.get("toc", [])
    card_filenames = config.get("cards", [])
    total = len(card_filenames)

    card_index = {fname: i for i, fname in enumerate(card_filenames)}
    toc_html = "".join(render_toc_node(node, card_index) for node in toc)

    panels = []
    for i, (fname, html) in enumerate(cards_html):
        card_title = find_leaf_title(toc, fname)
        display = "" if i == 0 else ' style="display:none"'
        panels.append(
            f'<div class="card-panel" data-card="{i}"{display}>'
            f'<div class="card-header">'
            f'<span class="card-badge">Card {i + 1}</span>'
            f'<h1 class="card-title">{card_title}</h1>'
            f"</div>"
            f'<div class="card-body">{html}</div>'
            f"</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Preview</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-label">강좌 목차</div>
      <div class="course-title">{title}</div>
      <div class="card-count">{total} 카드</div>
    </div>
    <nav class="toc-nav">{toc_html}</nav>
  </aside>
  <main class="main">
    <div class="cards-container">{"".join(panels)}</div>
    <div class="nav-bar">
      <button class="nav-btn" id="btn-prev" onclick="prevCard()">&#8249; 이전</button>
      <span class="nav-counter" id="counter">1 / {total}</span>
      <button class="nav-btn nav-btn-next" id="btn-next" onclick="nextCard()">다음 &#8250;</button>
    </div>
  </main>
</div>
<script>{JS}</script>
</body>
</html>"""


def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/generate_preview.py <course-name>")
        sys.exit(1)

    course_name = sys.argv[1]
    base = Path(__file__).parent.parent
    course_dir = base / "converted" / course_name

    if not course_dir.exists():
        print(f"Error: {course_dir} not found")
        sys.exit(1)

    config = load_config(course_dir)
    card_filenames = config.get("cards", [])

    cards_html = []
    for fname in card_filenames:
        html = convert_card(course_dir / "cards" / fname)
        cards_html.append((fname, html))

    out_html = build_html(config, cards_html)
    out = course_dir / "preview.html"
    out.write_text(out_html, encoding="utf-8")
    print(f"Preview generated: {out}")


if __name__ == "__main__":
    main()
