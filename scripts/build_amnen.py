#!/usr/bin/env python3
"""Bygger de sex ämnessidorna (/lon-och-jobb, /bil-och-energi …) och innehåller
gemensam data för startsidan: jämförelseverktyg, guider per ämne och beskrivningar.

    python3 scripts/build_amnen.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_index():
    with open(os.path.join(ROOT, "search-index.js"), encoding="utf-8") as f:
        s = f.read()
    items = json.loads(s[s.index("["):s.rindex("]") + 1])
    import html as _h
    return {x["url"]: {k: _h.unescape(v) if isinstance(v, str) else v for k, v in x.items()} for x in items}


# Jämförelseverktyg ("Vad borde det kosta?"). url=None betyder att det kommer snart.
COMPARE = {
    "/lon-och-jobb": [
        ("kr", "Vad borde jag tjäna?", "Din lön mot yrket i SCB:s statistik – och vad du ska begära", "/kalkylatorer/loneforhandling"),
        ("yrke", "Lön per yrke", "Median, spridning och lön per ålder för 105 yrken", "/kalkylatorer/yrkeslon/"),
    ],
    "/skatt-och-deklaration": [],
    "/boende-och-lan": [
        ("%", "Vilken bolåneränta borde jag ha?", "Din ränta mot bankernas snitträntor", None),
        ("hem", "Vad kostar det att bo här?", "Skatt och avgifter i din kommun", None),
        ("rot", "Vad kostar renoveringen?", "Badrum, tak och målning – med ROT", None),
    ],
    "/bil-och-energi": [
        ("el", "Vad borde elen kosta?", "Ditt elpris mot snittet för nya avtal i ditt elområde", "/kalkylatorer/elkostnadskalkylator"),
        ("bil", "Vad kostar bilen att leasa?", "Månadskostnad och vilka bilar som kostar lika mycket", None),
        ("bil", "Vad borde en begagnad bil kosta?", "Rimligt pris, vad du ska kontrollera och riskerna", None),
    ],
    "/sparande-och-pension": [
        ("%", "Vad kostar dina fonder?", "Avgifterna i kronor – och vad billigare fonder ger", None),
    ],
    "/familj-och-trygghet": [
        ("+", "Vad borde tandvården kosta?", "Priser och vad högkostnadsskyddet täcker", None),
    ],
}

GUIDES = {
    "/lon-och-jobb": ["/artiklar/rakna-ut-nettolon-2026", "/artiklar/vad-ar-semesterlon", "/artiklar/vad-ar-f-skatt"],
    "/skatt-och-deklaration": ["/artiklar/deklaration-2027", "/artiklar/skatteaterbaring-2027", "/artiklar/reseavdrag-2027",
                               "/artiklar/hur-far-man-tillbaka-skatten", "/artiklar/vad-ar-marginalskatt",
                               "/artiklar/vad-ar-kapitalvinstskatt", "/artiklar/vad-ar-moms-2026", "/artiklar/vad-ar-rot-rut-avdrag"],
    "/boende-och-lan": ["/artiklar/vad-ar-bolan", "/artiklar/hur-mycket-far-jag-lana-2026", "/artiklar/amorteringskrav-2026",
                        "/artiklar/vad-ar-effektiv-ranta", "/artiklar/skattefri-uthyrning-2026"],
    "/bil-och-energi": ["/artiklar/elkostnad-2026-sa-raknar-du", "/artiklar/privatleasing-eller-kopa-bil-2026", "/artiklar/reseavdrag-2027"],
    "/sparande-och-pension": ["/artiklar/vad-ar-ranta-pa-ranta", "/artiklar/manadssparande-rakna-ut", "/artiklar/vad-ar-isk",
                              "/artiklar/hur-beraknas-pension", "/artiklar/vad-ar-inflation", "/artiklar/csn-2026-belopp-och-regler"],
    "/familj-och-trygghet": ["/artiklar/rakna-ut-foraldrapenning-2026", "/artiklar/barnbidrag-2026", "/artiklar/rakna-ut-sjuklon-2026",
                             "/artiklar/a-kassa-2026-belopp-och-regler"],
}

INTRO = {
    "/lon-och-jobb": ("Lön & jobb – räkna på lön, semester och egen firma",
                      "Räkna ut nettolön, se vad du borde tjäna och vad du ska begära i lönesamtalet. Kalkylatorer för lön, semester, frilans och arbetsgivaravgift 2026.",
                      "Vad blir kvar efter skatt, vad tjänar andra i ditt yrke och vad ska du begära i lönesamtalet?"),
    "/skatt-och-deklaration": ("Skatt & deklaration – återbäring, avdrag och marginalskatt",
                               "Räkna ut skatteåterbäring, reseavdrag, marginalskatt, ROT och RUT. Kalkylatorer och guider inför deklarationen 2027.",
                               "Hur mycket får du tillbaka, vilka avdrag kan du göra och hur mycket skatt betalar du på nästa hundralapp?"),
    "/boende-och-lan": ("Boende & lån – bolån, amortering och budget",
                        "Räkna på bolån, amorteringskrav, lån och om det lönar sig att hyra eller köpa. Gratis kalkylatorer för boende 2026.",
                        "Vad kostar bolånet per månad, hur mycket måste du amortera och lönar det sig att köpa?"),
    "/bil-och-energi": ("Bil & energi – elkostnad, bil, leasing och solceller",
                        "Se vad elen borde kosta, räkna på bilkostnad, leasing, förmånsbil, drivmedel och solceller. Med officiella siffror, uppdaterat varje månad.",
                        "Allt om vad bilen och elen kostar dig – och om du kan betala mindre."),
    "/sparande-och-pension": ("Sparande & pension – ränta på ränta, pension och CSN",
                              "Räkna på sparande, ränta på ränta, pension, tjänstepension, löneväxling och CSN. Gratis kalkylatorer 2026.",
                              "Hur mycket växer sparandet, vad får du i pension och hur lång tid tar CSN-lånet?"),
    "/familj-och-trygghet": ("Familj & trygghet – föräldrapenning, sjukpenning och a-kassa",
                             "Räkna ut föräldrapenning, sjukpenning, karensavdrag, a-kassa, barnbidrag och underhållsstöd 2026.",
                             "Vad får du när du är föräldraledig, sjuk eller utan jobb – och vad får barnen?"),
}

MIN_PROMPT = {
    "/bil-och-energi": ("Spara din elkostnad i Min ekonomi",
                        "Då ser du direkt på startsidan om ditt elavtal fortfarande är rimligt. Sparas bara i din webbläsare.",
                        "/kalkylatorer/elkostnadskalkylator", "Räkna och spara"),
    "/lon-och-jobb": ("Spara din lön i Min ekonomi",
                      "Då ser du direkt på startsidan hur din lön står sig mot yrket. Sparas bara i din webbläsare.",
                      "/kalkylatorer/loneforhandling", "Räkna och spara"),
}


def tcard(mark, q, sub, url):
    body = (f'<div class="gk-mark">{S.e(mark)}</div><div class="body"><div class="top"><span class="q">{S.e(q)}</span>'
            f'<span class="gk-tag {"live" if url else "soon"}">{"Klar" if url else "Snart"}</span></div>'
            f'<span class="sub">{S.e(sub)}</span></div>')
    if url:
        return f'<a class="gk-tcard" href="{url}">{body}</a>'
    return f'<div class="gk-tcard soon" aria-label="{S.e(q)} – kommer snart">{body}</div>'


def calc_desc(idx, url):
    x = idx.get(url.rstrip("/")) or idx.get(url)
    return x["desc"] if x else ""


def calclist(idx, links):
    lis = []
    for t, u in links:
        d = calc_desc(idx, u)
        if "yrkeslon" in u:
            d = "Medianlön, lönespridning och lön per ålder enligt SCB"
        lis.append(f'<li><a href="{u}"><span><b>{S.e(t)}</b>{f"<small>{S.e(d)}</small>" if d else ""}</span>{S.ICON_CHEV}</a></li>')
    return '<ul class="gk-calclist">' + "".join(lis) + "</ul>"


def guidecards(idx, urls):
    out = []
    for u in urls:
        x = idx.get(u)
        if not x:
            continue
        out.append(f'<a class="gk-linkcard" href="{u}"><span>{S.e(x["title"])}<small>{S.e(x.get("desc", ""))}</small></span>{S.ICON_CHEV}</a>')
    return "".join(out)


def hub_page(topic, idx):
    name, sub, hub, links = topic
    title, desc, lead = INTRO[hub]
    comp = COMPARE[hub]
    guides = GUIDES[hub]
    live = [c for c in comp if c[3]]
    n_calc = len(links)
    jumps = []
    if comp:
        jumps.append(("#jamfor", "Jämför", f"{len(comp)} verktyg"))
    jumps.append(("#rakna", "Räkna", f"{n_calc} kalkylatorer"))
    jumps.append(("#lar-dig", "Lär dig", f"{len(guides)} guider"))
    jump_html = f'<nav class="gk-jump" style="--n:{len(jumps)}" aria-label="På sidan">' + "".join(
        f'<a href="{h}">{t}<small>{c}</small></a>' for h, t, c in jumps) + "</nav>"

    comp_html = ""
    if comp:
        comp_html = f"""<section class="gk-sec" id="jamfor" aria-labelledby="h-jamfor">
<div class="gk-sec-head"><div><span class="gk-kicker">Jämför</span><h2 id="h-jamfor">Betalar du rätt?</h2></div></div>
<p class="gk-hint">Räkna ut din kostnad, se om den är rimlig och vad alternativen kostar.{' Fler jämförelser är på väg.' if len(live) < len(comp) else ''}</p>
<div class="gk-guides">{''.join(tcard(*c) for c in comp)}</div>
</section>"""

    mp = MIN_PROMPT.get(hub)
    min_html = ""
    if mp:
        min_html = (f'<section class="gk-note-card" style="margin-top:28px"><strong>{S.e(mp[0])}</strong><span>{S.e(mp[1])}</span>'
                    f'<a class="gk-btn" style="align-self:flex-start" href="{mp[2]}">{S.e(mp[3])}</a></section>')

    others = "".join(
        f'<a class="gk-hubcard" href="{h}"><span class="t">{S.e(n)}{S.ICON_CHEV}</span><span class="x">{S.e(sb)}</span></a>'
        for n, sb, h, _ in S.TOPICS if h and h != hub)

    crumbs = [("Hem", "/"), (name, None)]
    ld = [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": S.SITE + hub, "description": desc, "inLanguage": "sv"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": S.SITE + hub}]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": f"Kalkylatorer – {name}", "numberOfItems": n_calc,
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t, "url": S.SITE + u} for i, (t, u) in enumerate(links)]},
    ]
    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<h1>{S.e(name)}</h1>
<p class="gk-lead">{S.e(lead)}</p>
{jump_html}
</div>
{comp_html}
<section class="gk-sec" id="rakna" aria-labelledby="h-rakna">
<div class="gk-sec-head"><div><span class="gk-kicker">Räkna</span><h2 id="h-rakna">Kalkylatorer</h2></div></div>
{calclist(idx, links)}
</section>
{min_html}
<section class="gk-sec" id="lar-dig" aria-labelledby="h-lar">
<div class="gk-sec-head"><div><span class="gk-kicker">Lär dig</span><h2 id="h-lar">Guider</h2></div></div>
<div class="gk-guides">{guidecards(idx, guides)}</div>
</section>
<section class="gk-sec" aria-labelledby="h-andra">
<div class="gk-sec-head"><div><h2 id="h-andra" style="font-size:22px">Andra ämnen</h2></div></div>
<div class="gk-guides">{others}</div>
</section>
</main>
"""
    return S.head(title + " | GratisKalkyl", desc, hub, og_title=title, jsonld=ld) + S.header() + body + S.footer()


def main():
    idx = load_index()
    for t in S.TOPICS:
        if not t[2]:
            continue
        html_text = hub_page(t, idx)
        out = os.path.join(ROOT, t[2].lstrip("/") + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html_text)
        missing = [u for u in GUIDES[t[2]] if u not in idx]
        print("Skrev", out, len(html_text), "tecken", ("SAKNAS: " + ", ".join(missing)) if missing else "")


if __name__ == "__main__":
    main()
