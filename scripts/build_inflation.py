#!/usr/bin/env python3
"""Bygger kalkylatorer/inflationskalkylator.html i den nya verktygsmallen.

Modell (samma i Python-referensen nedan och i sidans JS):
  Värde = belopp × KPI(till-år) / KPI(från-år). Fungerar åt båda hållen (till-år får vara tidigare).
  Prisökning = KPI(senare år) / KPI(tidigare år) − 1.
  Snittinflation per år = (KPI(senare) / KPI(tidigare)) ^ (1 / år) − 1, där år = skillnaden i år. Årsmedeltal
  motsvarar mitten av året; för 2026 används KPI för augusti, som ligger 1,5 månad senare – därför + 1,5/12 år.
  Köpkraften har minskat = 1 − KPI(tidigare) / KPI(senare).

KPI-serien (verifierad mot SCB 1 oktober 2026):
  - 1980–2024: SCB, "Konsumentprisindex (1980=100), fastställda tal", kolumnen Årsmedel.
  - 2025: årsmedel 417,98 = medel av SCB:s tolv månadstal 2025 (jan–aug från tabellen ovan, sep 418,26,
    okt 419,35, nov 417,83, dec 417,96 från SCB:s statistiknyheter).
  - 2026: inget årsmedel ännu. Senaste publicerade månad: augusti 2026 = 124,85 (2020=100), publicerad 14 sep 2026.
    SCB räknar om till 1980=100 genom att multiplicera med 3,3592 och avrunda till två decimaler → 419,40.
    Vid nästa KPI-publicering: byt SENAST (månad, kpi2020) och kör skriptet igen.

    python3 scripts/build_inflation.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/inflationskalkylator"
UPDATED = "1 oktober 2026"

# Senaste KPI-månaden (SCB, publicerad 14 sep 2026). Byt här när en ny månad publiceras.
SENAST = {"ar": 2026, "manad": "augusti", "kpi2020": 124.85, "faktor": 3.3592, "publicerad": "14 september 2026",
          "kpi_takt": 0.3, "kpif_takt": 0.7}

K = {
    # SCB, KPI fastställda årsmedeltal, 1980=100
    "KPI": {
        1980: 100.00, 1981: 112.10, 1982: 121.70, 1983: 132.60, 1984: 143.20,
        1985: 153.80, 1986: 160.30, 1987: 167.00, 1988: 176.70, 1989: 188.10,
        1990: 207.80, 1991: 227.20, 1992: 232.40, 1993: 243.20, 1994: 248.50,
        1995: 254.80, 1996: 256.00, 1997: 257.30, 1998: 257.00, 1999: 258.10,
        2000: 260.70, 2001: 267.10, 2002: 272.80, 2003: 278.10, 2004: 279.20,
        2005: 280.40, 2006: 284.22, 2007: 290.51, 2008: 300.61, 2009: 299.66,
        2010: 303.46, 2011: 311.43, 2012: 314.20, 2013: 314.06, 2014: 313.49,
        2015: 313.35, 2016: 316.43, 2017: 322.11, 2018: 328.40, 2019: 334.26,
        2020: 335.92, 2021: 343.19, 2022: 371.91, 2023: 403.70, 2024: 415.15,
        2025: 417.98,
    },
    "AR_MIN": 1980,
    "AR_MAX": SENAST["ar"],
    "MANAD": SENAST["manad"],
    "OFFSET": 1.5 / 12,   # augusti (mitten) ligger 1,5 månad efter årsmedlets mittpunkt
    "MAL": 2.0,           # Riksbankens inflationsmål, KPIF
    "MAL_AR": 1995,       # målet gäller formellt från 1995
    "KPI2020": SENAST["kpi2020"],
    "FAKTOR": SENAST["faktor"],
}
K["KPI"][SENAST["ar"]] = round(SENAST["kpi2020"] * SENAST["faktor"], 2)  # 419,40

# SCB:s månadstal 2025 (1980=100) – kontroll av årsmedel 2025
MAN_2025 = [416.57, 419.08, 416.20, 416.69, 416.95, 418.94, 419.75, 418.13, 418.26, 419.35, 417.83, 417.96]
assert round(sum(MAN_2025) / 12, 2) == K["KPI"][2025]

SRC = {
    "scb_fast": "https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/tabell-och-diagram/konsumentprisindex-kpi/kpi-faststallda-tal-1980100",
    "scb_sep25": "https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-september-2025/",
    "scb_okt25": "https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-oktober-2025/",
    "scb_nov25": "https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-november-2025/",
    "scb_dec25": "https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-december-2025/",
    "scb_senast": "https://www.scb.se/hitta-statistik/statistik-efter-amne/priser-och-ekonomiska-tendenser/priser/konsumentprisindex-kpi/pong/statistiknyhet/konsumentprisindex-kpi-augusti-2026/",
    "scb_basar": "https://www.scb.se/contentassets/a1e257bb3a574420b9d3f2ff59851c0a/2020-nytt-basar-for-konsumentprisindex.pdf",
    "scb_infl": "https://www.scb.se/hitta-statistik/sverige-i-siffror/samhallets-ekonomi/inflation/",
    "scb_prisomr": "https://www.scb.se/hitta-statistik/sverige-i-siffror/prisomraknaren/",
    "rb_kpif": "https://www.riksbank.se/globalassets/media/rapporter/ppr/fordjupningar/svenska/2017/kpif-malvariabel-for-penningpolitiken-fordjupning-i-penningpolitisk-rapport-september-2017",
    "rb_historik": "https://www.riksbank.se/sv/penningpolitik/inflationsmalet/historik-inflationsmalet/",
}

KPI = K["KPI"]
NU = K["AR_MAX"]
NU_LABEL = f"{K['MANAD']} {NU}"


def fmt(n, d=0):
    return f"{n:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(v, d=1):
    v = 0.0 if abs(v) < 0.5 * 10 ** -d else v
    return fmt(v, d)


def infl(belopp, fran, till):
    """Python-referens – samma som sidans JS."""
    v = belopp * KPI[till] / KPI[fran]
    e, l_ = min(fran, till), max(fran, till)
    f = KPI[l_] / KPI[e]
    ar = (l_ - e) + (K["OFFSET"] if l_ == NU else 0)
    snitt = (f ** (1 / ar) - 1) * 100 if ar > 0 else 0.0
    return {"varde": v, "prisokning": (f - 1) * 100, "snitt": snitt, "kopkraft": (1 - 1 / f) * 100, "ar": ar}


def ar_takt(y):
    return (KPI[y] / KPI[y - 1] - 1) * 100


EX = infl(100, 2000, NU)
EX1980 = infl(100, 1980, NU)
EX1990 = infl(100, 1990, NU)
EXB = infl(1000, NU, 2000)
S95 = infl(100, 1995, 2025)

FAQ = [
    ("Hur räknar man ut inflation mellan två år?",
     "Dela KPI för det senare året med KPI för det tidigare och multiplicera med beloppet. 100 kr år 2000 blir "
     f"100 × {fmt(KPI[NU], 2)} / {fmt(KPI[2000], 2)} = {fmt(EX['varde'])} kr i dagens penningvärde. Priserna har alltså stigit med "
     f"{pct(EX['prisokning'])} %, i snitt {pct(EX['snitt'])} % per år. KPI-talen kommer från SCB."),
    ("Vad är 100 kr från 1980 värt i dag?",
     f"Ungefär {fmt(EX1980['varde'])} kr. Priserna har mer än fyrdubblats sedan 1980: KPI har gått från 100 till "
     f"{fmt(KPI[NU], 2)} ({NU_LABEL}). 100 kr från 1990 motsvarar {fmt(EX1990['varde'])} kr i dag och 100 kr från 2000 "
     f"{fmt(EX['varde'])} kr."),
    ("Hur hög har inflationen varit per år i Sverige?",
     f"Mätt med KPI var inflationen {pct(ar_takt(2022))} % 2022, {pct(ar_takt(2023))} % 2023, {pct(ar_takt(2024))} % 2024 och "
     f"{pct(ar_takt(2025))} % 2025 (årsmedel mot årsmedel). I {NU_LABEL} var inflationstakten {pct(SENAST['kpi_takt'])} % enligt KPI "
     f"och {pct(SENAST['kpif_takt'])} % enligt KPIF. Från 1995 till 2025 steg KPI med i snitt {pct(S95['snitt'])} % per år. "
     "Alla år finns i tabellen i kalkylatorn."),
    ("Vad är skillnaden mellan KPI och KPIF?",
     "KPI mäter hur konsumentpriserna förändras, och där ingår hushållens räntekostnader för bolån. KPIF är KPI med fast ränta, "
     "alltså utan effekten av ändrade bolåneräntor. Sedan september 2017 är Riksbankens mål att KPIF ska öka med 2 % per år. "
     "För att räkna om gamla kronor till dagens penningvärde används KPI."),
    ("Finns det en inflationskalkylator från SCB?",
     "Ja, SCB har Prisomräknaren, som räknar om belopp med KPI månad för månad från 1920. Den här kalkylatorn använder SCB:s "
     "fastställda årsmedeltal för KPI från 1980, så svaren kan skilja något om du jämför enskilda månader."),
    ("Vad var 1 000 kr i dag värda förr?",
     f"Räkna bakåt genom att välja dagens år som från-år. 1 000 kr i dag motsvarar {fmt(EXB['varde'])} kr år 2000 – det var vad "
     "samma varor och tjänster kostade då. Med knappen Byt håll vänder du på beräkningen."),
    ("Varför räknar kalkylatorn 2026 med augusti?",
     f"SCB fastställer ett årsmedeltal först när året är slut. För 2026 använder vi därför KPI för {NU_LABEL}, den senaste "
     f"månaden SCB har publicerat ({SENAST['publicerad']}). Den är {fmt(SENAST['kpi2020'], 2)} med basår 2020 och "
     f"{fmt(KPI[NU], 2)} omräknad till basår 1980."),
]

CHEV = S.ICON_CHEV


def year_opts(sel):
    out = []
    for y in range(K["AR_MAX"], K["AR_MIN"] - 1, -1):
        lab = f"{y} ({K['MANAD'][:3]})" if y == NU else str(y)
        out.append(f'<option value="{y}"{" selected" if y == sel else ""}>{lab}</option>')
    return "".join(out)


def page():
    title = "Inflationskalkylator Sverige – KPI 1980–2026 | GratisKalkyl"
    desc = (f"100 kr år 2000 är värda {fmt(EX['varde'])} kr i dag. Räkna om belopp med SCB:s KPI 1980–2026: dagens "
            "penningvärde, total prisökning och inflation per år.")
    crumbs = [("Hem", "/"), ("Sparande & pension", "/sparande-och-pension"), ("Inflationskalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Inflationskalkylator – KPI 1980–2026",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Sparande & pension", "item": S.SITE + "/sparande-och-pension"},
            {"@type": "ListItem", "position": 3, "name": "Inflationskalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    # Tabell: 100 kr ett visst år i dagens penningvärde
    rows = []
    for y in (1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025):
        r = infl(100, y, NU)
        rows.append(f"<tr><td>{y}</td><td><strong>{fmt(r['varde'])} kr</strong></td><td>+{pct(r['prisokning'], 0)} %</td></tr>")
    ex_rows = "".join(rows)

    # Tabell: KPI och inflation per år, alla år (statisk – kan läsas av sökmotorer)
    krows = []
    for y in range(NU, K["AR_MIN"] - 1, -1):
        lab = f"{y} ({K['MANAD'][:3]})*" if y == NU else str(y)
        t = "–" if y == K["AR_MIN"] else pct(ar_takt(y)) + " %"
        krows.append(f"<tr><td>{lab}</td><td>{fmt(KPI[y], 2)}</td><td>{t}</td></tr>")
    kpi_rows = "".join(krows)

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Inflationskalkylator 2026</div>
<h1>Vad är pengarna värda i dag? – inflationskalkylator</h1>
<p class="gk-lead">Räkna om ett belopp mellan två år med SCB:s konsumentprisindex (KPI) – framåt till dagens penningvärde eller bakåt.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · KPI till och med {NU_LABEL} · Källa: <a href="{SRC['scb_fast']}" target="_blank" rel="noopener">SCB, KPI fastställda tal</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="inform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="belopp">Belopp</label>
<div class="gk-input"><input id="belopp" inputmode="decimal" autocomplete="off" value="100"><span class="unit">kr</span></div>
<div class="gk-seg" style="--n:3" id="beq" role="group" aria-label="Vanliga belopp">
<button type="button" data-v="100" aria-pressed="true">100 kr</button>
<button type="button" data-v="1000" aria-pressed="false">1 000 kr</button>
<button type="button" data-v="10000" aria-pressed="false">10 000 kr</button>
</div>
</div>
<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px">
<div class="gk-field">
<label for="fran">Från år</label>
<div class="gk-input"><select id="fran">{year_opts(2000)}</select></div>
</div>
<div class="gk-field">
<label for="till">Till år</label>
<div class="gk-input"><select id="till">{year_opts(NU)}</select></div>
</div>
</div>
<button type="button" class="gk-btn secondary" id="swap" style="align-self:flex-start">⇄ Byt håll</button>
<span class="gk-hint">Välj ett senare år i ”Från” för att räkna bakåt: vad dagens pengar motsvarade förr. {NU} räknas med KPI för {K['MANAD']}, den senaste månaden från SCB.</span>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:12px" aria-labelledby="perH">
<h2 id="perH" style="font-size:22px">Inflation per år</h2>
<figure style="margin:0">
<figcaption class="gk-hint" style="margin-bottom:8px" id="chartCap"></figcaption>
<div id="chart"></div>
</figure>
<details class="gk-more">
<summary>KPI och inflation för alla år 1980–{NU}</summary>
<div>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight">
<thead><tr><th scope="col">År</th><th scope="col">KPI (1980=100)</th><th scope="col">Inflation</th></tr></thead>
<tbody>{kpi_rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Årsmedeltal från SCB. Inflation = förändring mot året före. * {NU}: KPI för {NU_LABEL} jämfört med årsmedel {NU - 1}. Inflationstakten i {NU_LABEL} (jämfört med samma månad året före) var {pct(SENAST['kpi_takt'])} % enligt SCB.</caption>
</table></div>
</div>
</details>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">I dagens penningvärde</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="/kalkylatorer/sparkalkylator"><span>Räkna på ditt sparande<small>Sparkalkylator – månadssparande och mål</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/vad-ar-inflation"><span>Guide: Vad är inflation?<small>Hur den mäts och vad den betyder för dig</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Vad är 100 kr värt i dag?</h2>
<p>Så mycket behöver du i dag ({NU_LABEL}) för att köpa lika mycket som 100 kr räckte till förr, enligt SCB:s KPI:</p>
<div class="gk-table-wrap"><table class="gk-table">
<thead><tr><th scope="col">100 kr år</th><th scope="col">Är i dag</th><th scope="col">Prisökning</th></tr></thead>
<tbody>{ex_rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Årsmedel för KPI (1980=100) jämfört med KPI för {NU_LABEL} ({fmt(KPI[NU], 2)}). Källa: SCB.</caption>
</table></div>

<h2>Så räknar du om med KPI</h2>
<p>Konsumentprisindex (KPI) från SCB visar hur priserna på det hushållen köper har förändrats. Året 1980 är satt till 100. För att räkna om ett belopp tar du <strong>belopp × KPI för året du räknar till / KPI för året du räknar från</strong>. Är KPI dubbelt så högt har priserna fördubblats, och du behöver dubbelt så många kronor för att köpa samma saker – köpkraften har halverats.</p>

<h2>Inflation per år i Sverige</h2>
<p>Inflationen var {pct(ar_takt(2022))} % 2022 och {pct(ar_takt(2023))} % 2023, den högsta inflationen sedan 1991. Därefter sjönk den till {pct(ar_takt(2024))} % 2024 och {pct(ar_takt(2025))} % 2025. I {NU_LABEL} var inflationstakten {pct(SENAST['kpi_takt'])} % enligt KPI. Alla år från 1980 finns i tabellen ovan.</p>

<h2>KPI eller KPIF?</h2>
<p>KPIF är KPI med fast ränta – samma priser men utan effekten av att bolåneräntorna ändras. Riksbankens mål är att KPIF ska öka med <strong>2 % per år</strong>. Målet bestämdes 1993 och gäller sedan 1995; fram till september 2017 mättes det med KPI. Vill du veta vad pengar är värda i dag är det KPI som gäller, och det är KPI som både den här kalkylatorn och SCB:s egen <a href="{SRC['scb_prisomr']}" target="_blank" rel="noopener">Prisomräknaren</a> använder.</p>

<h2>Vanliga frågor om inflation</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['scb_fast']}" target="_blank" rel="noopener">SCB – Konsumentprisindex (1980=100), fastställda tal</a> – årsmedel 1980–2024 och månadstal januari–augusti 2025 (hämtat 1 oktober 2026)</li>
<li>SCB – KPI för <a href="{SRC['scb_sep25']}" target="_blank" rel="noopener">september</a>, <a href="{SRC['scb_okt25']}" target="_blank" rel="noopener">oktober</a>, <a href="{SRC['scb_nov25']}" target="_blank" rel="noopener">november</a> och <a href="{SRC['scb_dec25']}" target="_blank" rel="noopener">december 2025</a> – årsmedel 2025 = medel av årets tolv månader = {fmt(KPI[2025], 2)}</li>
<li><a href="{SRC['scb_senast']}" target="_blank" rel="noopener">SCB – Konsumentprisindex (KPI), {NU_LABEL}</a> – KPI {fmt(SENAST['kpi2020'], 2)} (2020=100), inflationstakt {pct(SENAST['kpi_takt'])} % (KPI) och {pct(SENAST['kpif_takt'])} % (KPIF), publicerad {SENAST['publicerad']}</li>
<li><a href="{SRC['scb_basar']}" target="_blank" rel="noopener">SCB – 2020 nytt basår för konsumentprisindex</a> (13 februari 2026) – KPI med basår 1980 = KPI med basår 2020 × 3,3592, avrundat till två decimaler</li>
<li><a href="{SRC['scb_infl']}" target="_blank" rel="noopener">SCB – Inflationen i Sverige</a> – KPIF utan effekten av ändrade bolåneräntor, mått för inflationsmålet sedan september 2017</li>
<li><a href="{SRC['rb_kpif']}" target="_blank" rel="noopener">Riksbanken – KPIF målvariabel för penningpolitiken</a> (september 2017) – målet 2 % för KPIF, tidigare definierat med KPI</li>
<li><a href="{SRC['rb_historik']}" target="_blank" rel="noopener">Riksbanken – Historik inflationsmålet</a> – fastställt 1993, gäller från 1995</li>
<li><a href="{SRC['scb_prisomr']}" target="_blank" rel="noopener">SCB – Prisomräknaren</a> – KPI månad för månad från 1920</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/sparkalkylator"><span>Sparkalkylator<small>Hur mycket behöver du spara varje månad?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/loneraknare"><span>Löneräknare<small>Har lönen hängt med? Se vad du får efter skatt</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-in" type="application/json">{json.dumps(K)}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Vad är pengarna värda i dag? Inflationskalkylator med SCB:s KPI", jsonld=ld)
            + S.header() + body
            + S.footer(f"KPI-talen kommer från SCB. För {NU} används KPI för {NU_LABEL} eftersom årsmedel saknas."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-in').textContent);
  var KPI = C.KPI, NU = C.AR_MAX;
  var $ = function (id) { return document.getElementById(id); };
  function lab(y) { return y === NU ? C.MANAD + ' ' + y : String(y); }
  function pct(v, d) { d = d == null ? 1 : d; if (Math.abs(v) < 0.5 * Math.pow(10, -d)) v = 0; return GK.fmt(v, d); }
  function krs(v) { return GK.fmt(v, v < 100 ? 2 : 0) + ' kr'; }

  /* Modell – samma som scripts/build_inflation.py */
  function infl(belopp, fran, till) {
    var v = belopp * KPI[till] / KPI[fran];
    var e = Math.min(fran, till), l = Math.max(fran, till);
    var f = KPI[l] / KPI[e];
    var ar = (l - e) + (l === NU ? C.OFFSET : 0);
    var snitt = ar > 0 ? (Math.pow(f, 1 / ar) - 1) * 100 : 0;
    return { varde: v, prisokning: (f - 1) * 100, snitt: snitt, kopkraft: (1 - 1 / f) * 100, ar: ar, e: e, l: l };
  }
  window.GKInfl = infl;

  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  $('beq').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    $('belopp').value = GK.fmt(+b.getAttribute('data-v'), 0); press(); calc();
  });
  function press() {
    var v = GK.parse($('belopp').value);
    $('beq').querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', +x.getAttribute('data-v') === v ? 'true' : 'false'); });
  }
  $('belopp').addEventListener('input', function () { press(); calc(); });
  GK.groupInput($('belopp'));
  ['fran', 'till'].forEach(function (id) { $(id).addEventListener('change', calc); });
  $('swap').addEventListener('click', function () { var a = $('fran').value; $('fran').value = $('till').value; $('till').value = a; calc(); });

  function calc() {
    var b = GK.parse($('belopp').value), fr = +$('fran').value, ti = +$('till').value;
    if (!isFinite(b) || b <= 0) {
      $('resBig').textContent = '–'; $('resSub').textContent = 'Fyll i ett belopp.';
      ['tiles', 'verdict', 'how'].forEach(function (id) { $(id).innerHTML = ''; });
      chart(Math.min(fr, ti), Math.max(fr, ti)); return;
    }
    if (fr === ti) {
      $('resLabel').textContent = 'Samma år';
      $('resBig').textContent = GK.fmt(b, b < 100 ? 2 : 0); $('resSub').textContent = 'Välj två olika år för att se hur priserna har ändrats.';
      ['tiles', 'verdict', 'how'].forEach(function (id) { $(id).innerHTML = ''; });
      chart(fr, fr); return;
    }
    var r = infl(b, fr, ti), fram = ti > fr, upp = r.prisokning >= 0;
    $('resLabel').textContent = ti === NU ? 'I dagens penningvärde (' + lab(NU) + ')' : 'I ' + ti + ' års penningvärde';
    $('resBig').textContent = GK.fmt(r.varde, r.varde < 100 ? 2 : 0);
    $('resSub').textContent = fram
      ? krs(b) + ' år ' + fr + ' motsvarar ' + krs(r.varde) + (ti === NU ? ' i dag.' : ' år ' + ti + '.') + ' Så mycket behövs för att köpa samma saker.'
      : krs(b) + (fr === NU ? ' i dag' : ' år ' + fr) + ' motsvarar ' + krs(r.varde) + ' år ' + ti + ' – det var vad samma saker kostade då.';
    var arTxt = GK.fmt(r.ar, r.ar % 1 ? 1 : 0) + ' år';
    $('tiles').innerHTML =
      tile(upp ? 'Priserna har stigit' : 'Priserna har sjunkit', (upp ? '+' : '') + pct(Math.abs(r.prisokning)) + ' %', r.e + '–' + (r.l === NU ? lab(NU) : r.l)) +
      tile('Inflation per år i snitt', pct(r.snitt, 2) + ' %', 'Under ' + arTxt) +
      tile('Köpkraften', (upp ? '−' : '+') + pct(Math.abs(r.kopkraft)) + ' %', '1 kr ' + (r.l === NU ? 'i dag' : 'år ' + r.l) + ' köper som ' + GK.fmt(KPI[r.e] / KPI[r.l], 2) + ' kr år ' + r.e) +
      tile('KPI (1980=100)', GK.fmt(KPI[r.e], 2) + ' → ' + GK.fmt(KPI[r.l], 2), r.e + ' → ' + lab(r.l));

    var mal = 'Riksbankens mål är att priserna, mätt med KPIF, ska öka med 2 % per år' + (r.e < C.MAL_AR ? ' – målet gäller sedan 1995.' : '.');
    var v;
    if (r.snitt > C.MAL + 0.5) v = verdict('warn', 'Högre än Riksbankens mål: ' + pct(r.snitt) + ' % mot 2 %', 'Mellan ' + r.e + ' och ' + lab(r.l) + ' steg KPI med i snitt ' + pct(r.snitt, 2) + ' % per år. ' + mal);
    else if (r.snitt < C.MAL - 0.5) v = verdict('info', 'Lägre än Riksbankens mål: ' + pct(r.snitt) + ' % mot 2 %', 'Mellan ' + r.e + ' och ' + lab(r.l) + ' steg KPI med i snitt ' + pct(r.snitt, 2) + ' % per år. ' + mal);
    else v = verdict('good', 'Nära Riksbankens mål: ' + pct(r.snitt) + ' % mot 2 %', 'Mellan ' + r.e + ' och ' + lab(r.l) + ' steg KPI med i snitt ' + pct(r.snitt, 2) + ' % per år. ' + mal);
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p>' + GK.fmt(b, b % 1 ? 2 : 0) + ' kr × KPI ' + lab(ti) + ' (' + GK.fmt(KPI[ti], 2) + ') / KPI ' + lab(fr) + ' (' + GK.fmt(KPI[fr], 2) + ') = ' + krs(r.varde) + '.</p>' +
      '<p>KPI-talen är SCB:s fastställda årsmedeltal med 1980 = 100. För ' + NU + ' finns inget årsmedel ännu, så vi använder KPI för ' + lab(NU) + ': ' + GK.fmt(C.KPI2020, 2) + ' med basår 2020, omräknat med SCB:s faktor ' + GK.fmt(C.FAKTOR, 4) + ' till ' + GK.fmt(KPI[NU], 2) + '.</p>' +
      '<p>Snittinflationen är den årliga ökning som ger samma totala prisökning: (' + GK.fmt(KPI[r.l], 2) + ' / ' + GK.fmt(KPI[r.e], 2) + ')^(1/' + GK.fmt(r.ar, r.ar % 1 ? 3 : 0) + ') − 1 = ' + pct(r.snitt, 2) + ' %.' + (r.l === NU ? ' Ett årsmedel motsvarar mitten av året och ' + lab(NU) + ' ligger 1,5 månad senare, därför ' + GK.fmt(r.ar, 3) + ' år.' : '') + '</p>';
    chart(r.e, r.l);
  }

  function chart(e, l) {
    var ys = [];
    for (var y = Math.max(e + 1, C.AR_MIN + 1); y <= l; y++) ys.push({ y: y, t: (KPI[y] / KPI[y - 1] - 1) * 100 });
    if (!ys.length) { $('chart').innerHTML = ''; $('chartCap').textContent = 'Välj två olika år för att se inflationen år för år.'; return; }
    var W = Math.max(300, Math.min(760, $('chart').clientWidth || 600)), H = W < 500 ? 190 : 210, L = 34, R = 16, Tp = 18, B = 26;
    var mx = Math.max.apply(null, ys.map(function (d) { return d.t; }).concat([2.5])), mn = Math.min.apply(null, ys.map(function (d) { return d.t; }).concat([0]));
    var hi = Math.ceil(mx / 2) * 2, lo = mn < 0 ? -Math.ceil(-mn) : 0;
    var step = hi - lo > 8 ? 4 : 2;
    var y = function (v) { return Tp + (hi - v) / (hi - lo) * (H - Tp - B); };
    var bw = (W - L - R) / ys.length;
    var g = '';
    for (var t = (lo <= -step ? lo : 0); t <= hi + 1e-9; t += (t < 0 ? -t : step)) g += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(t) + '" y2="' + y(t) + '" stroke="var(--gk-border)"/><text x="' + (L - 5) + '" y="' + (y(t) + 4) + '" text-anchor="end" font-size="11" fill="var(--gk-muted)">' + GK.fmt(t, 0) + ' %</text>';
    var bars = '';
    ys.forEach(function (d, i) {
      var x = L + i * bw, h = Math.abs(y(d.t) - y(0)), top = d.t >= 0 ? y(d.t) : y(0);
      bars += '<rect x="' + (x + Math.min(2, bw * 0.15)) + '" y="' + top + '" width="' + Math.max(1, bw - 2 * Math.min(2, bw * 0.15)) + '" height="' + Math.max(0.5, h) + '" rx="' + (bw > 10 ? 2 : 0) + '" fill="' + (d.t >= 0 ? 'var(--gk-accent)' : 'var(--gk-ink-2)') + '"><title>' + (d.y === NU ? lab(NU) : d.y) + ': ' + pct(d.t) + ' %</title></rect>';
    });
    var every = ys.length <= 8 ? 1 : ys.length <= 16 ? 2 : ys.length <= 30 ? 5 : 10;
    ys.forEach(function (d, i) {
      if (i % every && i !== ys.length - 1) return;
      if (i !== ys.length - 1 && ys.length - 1 - i < every / 2 && every > 1) return;
      g += '<text x="' + (L + (i + 0.5) * bw) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="var(--gk-muted)">' + (d.y === NU ? d.y + '*' : d.y) + '</text>';
    });
    var goal = '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(C.MAL) + '" y2="' + y(C.MAL) + '" stroke="var(--gk-ink)" stroke-width="1.5" stroke-dasharray="5 4"/>';
    $('chartCap').textContent = 'KPI-förändring mot året före, ' + (ys[0].y) + '–' + (l === NU ? lab(NU) : l) + '. Streckad linje: Riksbankens mål, 2 %.' + (l === NU ? ' * ' + lab(NU) + ' mot årsmedel ' + (NU - 1) + '.' : '');
    $('chart').innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Inflation per år ' + ys[0].y + '–' + l + ': ' + ys.map(function (d) { return d.y + ' ' + pct(d.t) + ' %'; }).join(', ') + '" style="display:block;font-family:inherit">' + g + bars + goal + '</svg>';
  }

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "inflationskalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    print(f"KPI {NU} ({K['MANAD']}) = {KPI[NU]}  | årsmedel 2025 kontroll = {sum(MAN_2025) / 12:.4f}")
    for b, fr, ti in [(100, 2000, NU), (100, 1980, NU), (1000, NU, 2000), (5000, 1990, 2010), (250, 2013, 2015), (100, 2025, NU)]:
        r = infl(b, fr, ti)
        print(f"{b} kr {fr}->{ti}: värde {r['varde']:.4f}  prisökning {r['prisokning']:.4f} %  snitt {r['snitt']:.4f} %/år  "
              f"köpkraft {r['kopkraft']:.4f} %  år {r['ar']:.4f}")


if __name__ == "__main__":
    main()
