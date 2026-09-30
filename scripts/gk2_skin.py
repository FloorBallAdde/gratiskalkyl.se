#!/usr/bin/env python3
"""Ger äldre sidor den nya designens skal: sidhuvud, meny, sidfot, typsnitt och färger.

Sidornas innehåll och räknelogik lämnas orörda. Mörkt läge stängs av på dessa sidor
(de visas alltid ljust) tills de byggts om helt i den nya mallen.

    python3 scripts/gk2_skin.py [mapp eller fil ...]   (standard: hela sajten)

Skriptet är idempotent: sidor som redan har skalet hoppas över.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "gk2-skin"

COLOR_MAP = {
    "#16a34a": "#0D6A45", "#15803d": "#0A5236", "#166534": "#0A5236", "#1a6b4a": "#0D6A45",
    "#0d4a30": "#0A5236", "#059669": "#0D6A45", "#10b981": "#1F8A5B", "#34d399": "#0D6A45",
    "#065f46": "#0A5236", "#064e3b": "#0A5236", "#22c55e": "#1F8A5B", "#6ee7b7": "#B9DCC8",
    "#e8f5ee": "#E4F1EA", "#dcfce7": "#E4F1EA", "#f0fdf4": "#E4F1EA", "#ecfdf5": "#E4F1EA", "#d1fae5": "#E4F1EA",
    "#bbf7d0": "#B9DCC8", "#a7f3d0": "#B9DCC8",
    "#1a1a2e": "#15201A", "#111827": "#15201A", "#1f2937": "#15201A", "#0f172a": "#15201A",
    "#6b7280": "#56625B", "#64748b": "#56625B", "#4b5563": "#56625B", "#555555": "#56625B", "#555": "#56625B",
    "#374151": "#3A4640",
    "#fafbfc": "#F6F5F1", "#f8fafc": "#F6F5F1", "#f9fafb": "#F6F5F1", "#f8f9fa": "#F6F5F1",
    "#e2e8f0": "#E2E0D8", "#e5e7eb": "#E2E0D8",
}
HEX_RE = re.compile(r"#[0-9a-fA-F]{6}(?![0-9a-fA-F])|#[0-9a-fA-F]{3}(?![0-9a-fA-F])")
DARK_SEL = re.compile(r"data-theme\s*=\s*[\"']?dark|\.dark-mode|html\.dark|body\.dark|:root\.dark", re.I)


def map_colors(text):
    return HEX_RE.sub(lambda m: COLOR_MAP.get(m.group(0).lower(), m.group(0)), text)


def _match_brace(css, i):
    """css[i] == '{' -> index efter matchande '}' (hoppar över kommentarer och strängar)."""
    depth, n = 0, len(css)
    while i < n:
        c = css[i]
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "\"'":
            j = i + 1
            while j < n and css[j] != c:
                j += 2 if css[j] == "\\" else 1
            i = j + 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def strip_dark(css):
    out, i, n = [], 0, len(css)
    while i < n:
        # kommentarer och blanktecken på toppnivå
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(css[i:j]); i = j; continue
        if css[i].isspace():
            out.append(css[i]); i += 1; continue
        b = css.find("{", i)
        sc = css.find(";", i)
        if b < 0:
            out.append(css[i:]); break
        if 0 <= sc < b:  # at-regel utan block, t.ex. @import
            stmt = css[i:sc + 1]
            if not (stmt.lstrip().startswith("@import") and "fonts.googleapis" in stmt):
                out.append(stmt)
            i = sc + 1; continue
        prelude = css[i:b]
        end = _match_brace(css, b)
        block = css[b:end]
        p = prelude.strip()
        if p.startswith("@media") and "prefers-color-scheme" in p and "dark" in p:
            pass  # hela blocket bort
        elif p.startswith("@media") or p.startswith("@supports"):
            inner = strip_dark(block[1:-1])
            if inner.strip():
                out.append(prelude + "{" + inner + "}")
        elif p.startswith("@"):
            out.append(prelude + block)
        else:
            sels = [x for x in prelude.split(",")]
            keep = [x for x in sels if not DARK_SEL.search(x)]
            if keep:
                out.append(",".join(keep) + block)
        i = end
    return "".join(out)


def element_end(s, start, tag):
    pat = re.compile(r"<(/?)%s\b[^>]*>" % tag, re.I)
    depth = 0
    for m in pat.finditer(s, start):
        if m.group(1) == "":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return m.end()
    return -1


def remove_site_header(body):
    m = re.search(r"<(header|nav)\b", body)
    if not m:
        return body, False
    end = element_end(body, m.start(), m.group(1))
    if end < 0:
        return body, False
    chunk = body[m.start():end]
    if re.search(r"logo|GratisKalkyl|nav-back|back-link|Alla kalkylatorer", chunk):
        # element i det gamla sidhuvudet som sidans skript fortfarande letar efter (t.ex. temaknapp)
        ids = [i for i in re.findall(r'id="([^"]+)"', chunk)
               if re.search(r"getElementById\(\s*['\"]%s['\"]|querySelector\(\s*['\"]#%s['\"]" % (re.escape(i), re.escape(i)), body)]
        keep = "".join(f'<span id="{i}"></span>' for i in ids)
        placeholder = f'<div hidden aria-hidden="true">{keep}</div>' if keep else ""
        return body[:m.start()] + placeholder + body[end:], True
    return body, False


def replace_footer(body, new_footer):
    starts = [m.start() for m in re.finditer(r"<footer\b", body)]
    if not starts:
        i = body.rfind("</body>")
        return body[:i] + new_footer + body[i:], "added"
    st = starts[-1]
    end = element_end(body, st, "footer")
    if end < 0:
        i = body.rfind("</body>")
        return body[:i] + new_footer + body[i:], "added"
    return body[:st] + new_footer + body[end:], "replaced"


HEAD_ADD = f"""<!-- {MARK} -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="/assets/gk.css?v=20261001">
<link rel="stylesheet" href="/assets/gk-skin.css?v=20261001">
"""


def skin(html):
    if MARK in html or "assets/gk.css" in html:
        return html, "skip"
    notes = []
    head_end = html.index("</head>")
    head, rest = html[:head_end], html[head_end:]

    # tema: alltid ljust på äldre sidor
    def drop_theme_script(m):
        block = m.group(0)
        if "gk-theme" in block and len(block) < 2500:
            return ""
        return block
    head = re.sub(r"<script\b[^>]*>.*?</script>", drop_theme_script, head, flags=re.S)
    rest = re.sub(r"<script\b[^>]*>.*?</script>", drop_theme_script, rest, flags=re.S)
    head = re.sub(r'\s*<script[^>]*src="/(theme|nav)\.js"[^>]*></script>', "", head)
    rest = re.sub(r'\s*<script[^>]*src="/(theme|nav)\.js"[^>]*></script>', "", rest)
    # gamla typsnitt
    head = re.sub(r'\s*<link[^>]+fonts\.(googleapis|gstatic)\.com[^>]*>', "", head)
    # stilar: ta bort mörkt läge, byt färger och typsnitt
    def fix_style(m):
        css = strip_dark(m.group(2))
        css = css.replace("'Inter',", "'Plus Jakarta Sans',").replace('"Inter",', '"Plus Jakarta Sans",')
        return m.group(1) + map_colors(css) + m.group(3)
    head = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", fix_style, head, flags=re.S)
    rest = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", fix_style, rest, flags=re.S)
    # färger i style-attribut och skript
    rest = re.sub(r'style="([^"]*)"', lambda m: 'style="' + map_colors(m.group(1)) + '"', rest)
    rest = re.sub(r"(<script\b(?![^>]*application/ld\+json)[^>]*>)(.*?)(</script>)",
                  lambda m: m.group(1) + map_colors(re.sub(
                      r"window\.matchMedia\(\s*['\"]\(prefers-color-scheme:\s*dark\)['\"]\s*\)\.matches", "false",
                      m.group(2))) + m.group(3), rest, flags=re.S)

    extra = HEAD_ADD
    if "search-dropdown.css" not in head:
        extra += '<link rel="stylesheet" href="/search-dropdown.css">\n'
    if "search-index.js" not in head:
        extra += '<script defer src="/search-index.js"></script>\n'
    if "search-dropdown.js" not in head:
        extra += '<script defer src="/search-dropdown.js"></script>\n'
    extra += '<script defer src="/assets/gk.js?v=20261001"></script>\n'
    head = re.sub(r"<head>", '<head>\n<script>document.documentElement.setAttribute("data-theme","light");</script>', head, count=1)
    head = head + extra

    # body
    bm = re.search(r"<body\b([^>]*)>", rest)
    battrs = bm.group(1)
    if 'class="' in battrs:
        battrs = battrs.replace('class="', 'class="gk-skin ', 1)
    else:
        battrs = battrs + ' class="gk-skin"'
    body = rest[bm.end():]
    body, removed = remove_site_header(body)
    notes.append("header-removed" if removed else "NO-HEADER-REMOVED")
    body, how = replace_footer(body, S.footer_html(skin=True))
    notes.append("footer-" + how)
    # huvudinnehållet får id för hoppa-länken
    if 'id="innehall"' not in body:
        mm = re.search(r"<main\b([^>]*)>", body)
        if mm and "id=" not in mm.group(1):
            body = body[:mm.start()] + "<main" + mm.group(1) + ' id="innehall">' + body[mm.end():]
        else:
            body = '<div id="innehall"></div>\n' + body
    new_rest = rest[:bm.start()] + "<body" + battrs + ">\n" + S.shell_top(skin=True) + body
    return head + new_rest, ",".join(notes)


def targets(args):
    paths = args or ["."]
    files = []
    for p in paths:
        p = os.path.join(ROOT, p) if not os.path.isabs(p) else p
        if os.path.isdir(p):
            files += glob.glob(os.path.join(p, "**", "*.html"), recursive=True)
        elif p.endswith(".html"):
            files.append(p)
    skipdirs = (os.sep + "scripts" + os.sep, os.sep + "node_modules" + os.sep)
    return sorted(f for f in set(files) if not any(d in f for d in skipdirs))


def main():
    res = {}
    for f in targets(sys.argv[1:]):
        with open(f, encoding="utf-8") as fh:
            html = fh.read()
        new, note = skin(html)
        if note != "skip":
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
        res[os.path.relpath(f, ROOT)] = note
    bad = {k: v for k, v in res.items() if "NO-" in v}
    print(f"{sum(1 for v in res.values() if v != 'skip')} sidor fick skalet, {sum(1 for v in res.values() if v == 'skip')} hoppades över")
    for k, v in bad.items():
        print("  KONTROLLERA:", k, v)


if __name__ == "__main__":
    main()
