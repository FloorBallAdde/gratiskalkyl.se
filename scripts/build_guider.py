#!/usr/bin/env python3
"""Bygger guidesidan /artiklar/ (artiklar/index.html) i den nya designen.

Guiderna grupperas per ämne enligt GUIDES i build_amnen.py. Titel och beskrivning
hämtas från sökindexet (search-index.js), som i sin tur följer guidernas metabeskrivningar.

    python3 scripts/build_guider.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import build_amnen as A  # noqa: E402

ROOT = A.ROOT
PATH = "/artiklar/"


def main():
    idx = A.load_index()
    guides = {u: x for u, x in idx.items() if x.get("type") == "guide"}
    used = set()
    sections = []
    for name, sub, hub, _ in S.TOPICS:
        if not hub or hub not in A.GUIDES:
            continue
        urls = [u for u in A.GUIDES[hub] if u in guides and u not in used]
        used.update(urls)
        if not urls:
            continue
        slug = hub.strip("/")
        sections.append((name, hub, slug, urls))
    rest = [u for u in guides if u not in used]
    if rest:
        sections.append(("Övriga guider", None, "ovriga", rest))
    n = len(guides)

    jump = "".join(f'<a class="gk-chip" href="#{slug}">{S.e(name)}</a>' for name, _, slug, _ in sections)
    body_secs = []
    for name, hub, slug, urls in sections:
        cards = A.guidecards(idx, urls)
        more = f'<a href="{hub}" style="font-weight:700;font-size:15px">Allt om {S.e(name)} →</a>' if hub else ""
        body_secs.append(f"""<section class="gk-sec" id="{slug}" aria-labelledby="h-{slug}">
<div class="gk-sec-head"><div><h2 id="h-{slug}">{S.e(name)}</h2></div>{more}</div>
<div class="gk-guides">{cards}</div>
</section>""")

    title = f"Guider om privatekonomi 2026 – {n} guider | GratisKalkyl"
    desc = ("Gratis guider om privatekonomi 2026 – lön och skatt, deklaration, bolån, sparande, pension, "
            "föräldrapenning och elkostnad. Enkelt förklarat med officiella källor.")
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Guider om privatekonomi 2026",
         "url": S.SITE + PATH, "description": desc, "inLanguage": "sv"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guider", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "ItemList", "numberOfItems": n,
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": guides[u]["title"], "url": S.SITE + u}
                             for i, u in enumerate([u for _, _, _, us in sections for u in us])]},
    ]
    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs([("Hem", "/"), ("Guider", None)])}
<h1>Guider om privatekonomi</h1>
<p class="gk-lead">{n} guider som förklarar reglerna bakom kalkylatorerna – enkelt, på svenska och med officiella källor.</p>
<label class="gk-search" style="max-width:620px"><span class="gk-sr">Sök bland guiderna</span>{S.ICON_SEARCH}<input type="search" id="article-search" data-search-dropdown="auto" placeholder="Sök guide, t.ex. deklaration eller ISK" autocomplete="off" spellcheck="false"></label>
<div class="gk-chips">{jump}</div>
</div>
{''.join(body_secs)}
</main>
"""
    html_text = S.head(title, desc, PATH, og_title="Guider om privatekonomi 2026", jsonld=ld) + S.header() + body + S.footer()
    out = os.path.join(ROOT, "artiklar", "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, n, "guider i", len(sections), "ämnen")


if __name__ == "__main__":
    main()
