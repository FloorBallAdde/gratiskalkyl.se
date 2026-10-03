#!/usr/bin/env python3
"""Bygger kalkylatorer/loneraknare.html (lön efter skatt) i den nya verktygsmallen.

Skatten räknas med scripts/skatt2026.py (Python) och assets/skatt2026.js (sidan) – identiska modeller
som ger samma skatteavdrag som Skatteverkets månadstabeller 32 och 33 för 2026 (kolumn 1 och 3).
Sidan visar SLUTLIG skatt för ett helt år delat med 12, med kommunens exakta skattesats.

Regler och belopp 2026 (Skatteverket, Belopp och procent 2026 och SKV 433 utgåva 36):
  - Grundavdrag 17 400–45 600 kr, förhöjt för den som fyllt 66 år vid årets ingång (född 1959 eller tidigare).
  - Statlig skatt 20 % på beskattningsbar inkomst över 643 000 kr – brytpunkt 660 400 kr (66+: 760 500 kr).
  - Jobbskatteavdrag, skattereduktion för förvärvsinkomst (0,75 %, högst 1 500 kr), allmän pensionsavgift 7 %
    (räknas av mot skatten), public service-avgift 1 % (högst 1 184 kr).
  - Begravningsavgift 0,292 % (Stockholm 0,07 %, Tranås 0,285 %).
  - Kommunalskatt per kommun: data/kommunalskatt-2026.json (SCB, rikssnitt 32,38 %).
  - Kyrkoavgift: riksgenomsnitt 1,05 % 2026 (Svenska kyrkan), kan ändras på sidan.

    python3 scripts/build_loneraknare.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import skatt2026 as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/loneraknare"
UPDATED = "1 oktober 2026"

# Konstanter – byts vid årsskiftet. Själva skattemodellen (PBB, jobbskatteavdrag osv.) ligger i skatt2026.py/.js.
K = {
    "SNITT_KS": 32.38,                 # genomsnittlig kommunalskatt 2026 (SCB)
    "BEGR": 0.292,                     # begravningsavgift 2026, procent
    "BEGR_SPEC": {"Stockholm": 0.07, "Tranås": 0.285},
    "KYRKA": 1.05,                     # riksgenomsnitt kyrkoavgift 2026 (Svenska kyrkan), procent
    "BRYT": 660400,                    # brytpunkt för statlig skatt, under 66 år (kr/år)
    "BRYT66": 760500,                  # brytpunkt, fyllt 66 år vid årets ingång
    "GA_MIN": 17400, "GA_MAX": 45600,  # grundavdrag under 66 år
    "MS_STEG": 1000,                   # marginalskatt räknas på nästa 1 000 kr/mån
    "MAX_LON": 1000000,                # övre gräns för sökningen netto -> brutto (kr/mån)
    "DEF_LON": 35000, "DEF_NETTO": 30000,
    "AR": 2026,
}
TABELL = [20000, 22000, 25000, 28000, 30000, 32000, 35000, 38000, 40000, 45000, 50000, 55000, 60000, 70000, 80000]

SRC = {
    "belopp": "https://www.skatteverket.se/privat/skatter/beloppochprocent/2026",
    "skv433": "https://skatteverket.se/download/18.1522bf3f19aea8075ba55c/1765284655603/teknisk-beskrivning-skv-433-2026-utgava-36.pdf",
    "tab32": "https://skatteverket.se/download/18.1522bf3f19aea8075ba61b/1765290451072/allmanna-tabeller-manad-tabell-32.pdf",
    "tab33": "https://www.skatteverket.se/download/18.1522bf3f19aea8075ba61c/1765290465443/allmanna-tabeller-manad-tabell-33.pdf",
    "scb": "https://www.scb.se/hitta-statistik/statistik-efter-amne/offentlig-ekonomi/finanser-for-den-kommunala-sektorn/kommunalskatterna/pong/statistiknyhet/kommunalskatterna-2026/",
    "kyrka": "https://www.svenskakyrkan.se/medlem/kyrkoavgiften",
    "kvarskatt": "https://www.skatteverket.se/kvarskatt",
}


def fmt(n, dec=0):
    s = f"{n:,.{dec}f}".replace(",", "\u00a0")
    return s.replace(".", ",") if dec else s


def kr(n):
    return fmt(int(n + 0.5) if n >= 0 else -int(-n + 0.5)) + "\u00a0kr"


def pct(x, dec=1):
    return fmt(x, dec)


def slug(namn):
    """Samma kommun-nycklar som den gamla sidan använde i delningslänkar (?k=...)."""
    if namn == "Håbo":
        return "haabo"
    s = namn.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o"), ("é", "e"), (" ", "-")):
        s = s.replace(a, b)
    return s


def begr(kommun):
    return K["BEGR_SPEC"].get(kommun, K["BEGR"])


# ---------------------------------------------------------------------------
# Python-referens – samma logik som sidans JS
# ---------------------------------------------------------------------------
def skatt(lon, ks=K["SNITT_KS"], bg=K["BEGR"], ky=0.0, aldre=False):
    return T.skatt_ar(lon * 12, kommunalskatt=ks, begravning=bg, kyrkoavgift=ky, fodd_fore_1960=aldre)


def berakna(lon, ks=K["SNITT_KS"], bg=K["BEGR"], ky=0.0, aldre=False):
    r = skatt(lon, ks, bg, ky, aldre)
    r2 = skatt(lon + K["MS_STEG"], ks, bg, ky, aldre)
    return {"r": r, "netto": r["netto"] / 12, "skatt": r["total"] / 12,
            "andel": r["total"] / (lon * 12) if lon > 0 else 0.0,
            "ms": (r2["total"] - r["total"]) / (K["MS_STEG"] * 12)}


def brutto_for_netto(mal, ks=K["SNITT_KS"], bg=K["BEGR"], ky=0.0, aldre=False):
    """Lägsta hela bruttolön (kr/mån) som ger minst `mal` kr netto per månad. Binärsökning."""
    lo, hi = 0, K["MAX_LON"]
    if skatt(hi, ks, bg, ky, aldre)["netto"] / 12 < mal:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if skatt(mid, ks, bg, ky, aldre)["netto"] / 12 >= mal:
            hi = mid
        else:
            lo = mid + 1
    return lo


def rnd(x):
    """Avrundning till hela kronor som Math.round i JS (för positiva tal)."""
    import math
    return int(math.floor(x + 0.5))


# ---------------------------------------------------------------------------
with open(os.path.join(ROOT, "data", "kommunalskatt-2026.json"), encoding="utf-8") as f:
    KOMMUNER = json.load(f)["kommuner"]
LAG = min(KOMMUNER, key=lambda x: x[1])
HOG = max(KOMMUNER, key=lambda x: x[1])

EX35 = berakna(35000)
EX30 = berakna(30000)
EX30_LAG = berakna(30000, LAG[1], begr(LAG[0]))
EX30_HOG = berakna(30000, HOG[1], begr(HOG[0]))
EX40 = berakna(40000)
EX35_66 = berakna(35000, aldre=True)
JSA_MAX = berakna(80000)["r"]["jobbskatteavdrag"] / 12
JSA_FRAN = 8.08 * T.PBB / 12          # jobbskatteavdraget är som störst från 8,08 prisbasbelopp (SKV 433)
B25 = brutto_for_netto(25000)
B30 = brutto_for_netto(30000)

FAQ = [
    ("Hur räknar man ut lön efter skatt?",
     "Ta årslönen och dra av grundavdraget. På resten räknas kommunalskatt och, över brytpunkten, statlig skatt. Sedan dras "
     "jobbskatteavdraget och skattereduktionen för förvärvsinkomst av, och public service-avgift och begravningsavgift läggs "
     "till. Dela med 12 så har du skatten per månad. Kalkylatorn ovan gör alla steg åt dig med 2026 års regler."),
    ("Hur mycket är 30 000 kr efter skatt?",
     f"Med genomsnittlig kommunalskatt ({pct(K['SNITT_KS'], 2)} %) blir 30 000 kr i månaden {kr(EX30['netto'])} efter skatt "
     f"2026, om du är under 66 år. I {LAG[0]}, som har lägst skatt ({pct(LAG[1], 2)} %), blir det {kr(EX30_LAG['netto'])} "
     f"och i {HOG[0]}, som har högst ({pct(HOG[1], 2)} %), {kr(EX30_HOG['netto'])}."),
    ("Vad blir min nettolön på 40 000 kr?",
     f"Ungefär {kr(EX40['netto'])} i månaden med genomsnittlig kommunalskatt 2026. Skatten är {kr(EX40['skatt'])}, eller "
     f"{pct(EX40['andel'] * 100)} % av lönen. Får du en löneökning går {pct(EX40['ms'] * 100)} % av den till skatt."),
    ("Hur räknar man ut bruttolön från nettolön?",
     "Det finns ingen enkel formel, eftersom avdragen ändras med inkomsten. Kalkylatorn provar sig i stället fram till den "
     f"bruttolön som ger din nettolön. För 25 000 kr netto i månaden behöver du ungefär {kr(B25)} i bruttolön med "
     "genomsnittlig kommunalskatt, om du är under 66 år."),
    ("När betalar man statlig skatt?",
     f"När lönen är över {kr(K['BRYT'])} om året, ungefär {fmt(round(K['BRYT'] / 12, -3))} kr i månaden. Det är brytpunkten "
     f"{K['AR']}. På den del som är över betalar du 20 % statlig skatt utöver kommunalskatten. Har du fyllt 66 år vid årets "
     f"början är brytpunkten {kr(K['BRYT66'])}."),
    ("Vad är jobbskatteavdraget?",
     "En skattereduktion för dig som har inkomst av arbete. Den räknas av automatiskt i skatten på lönen. Avdraget växer med "
     f"lönen och är som störst från ungefär {fmt(round(JSA_FRAN, -2))} kr i månaden – med genomsnittlig kommunalskatt "
     f"{kr(JSA_MAX)} i månaden {K['AR']}."),
    ("Betalar man mindre skatt efter 66 år?",
     f"Ja. Har du fyllt 66 år vid årets början – {K['AR']} gäller det dig som är född {K['AR'] - 67} eller tidigare – får du "
     f"ett högre grundavdrag. Med 35 000 kr i lön blir nettolönen {kr(EX35_66['netto'])} i stället för {kr(EX35['netto'])}, "
     "med genomsnittlig kommunalskatt."),
    ("Varför stämmer inte nettolönen med mitt lönebesked?",
     "Arbetsgivaren drar skatt enligt Skatteverkets skattetabell, som går i inkomststeg och räknar med hela procentsatser. "
     "Därför kan avdraget skilja sig något från den skatt vi räknar fram, och skillnaden jämnas ut i beslutet om slutlig skatt. "
     f"Är du med i Svenska kyrkan betalar du också kyrkoavgift, i snitt {pct(K['KYRKA'], 2)} % – välj det under Ålder och "
     "kyrkoavgift."),
]

CHEV = S.ICON_CHEV


def page():
    opts = (f'<option value="" data-ks="{K["SNITT_KS"]}" data-slug="">Rikssnitt – {pct(K["SNITT_KS"], 2)} %</option>'
            + "".join(f'<option value="{S.e(n)}" data-ks="{v}" data-slug="{slug(n)}">{S.e(n)} – {pct(v, 2)} %</option>'
                      for n, v in KOMMUNER))

    title = "Lön efter skatt 2026 – räkna ut din nettolön | GratisKalkyl"
    desc = (f"Räkna ut lön efter skatt 2026 i alla 290 kommuner. 35 000 kr i månaden blir {kr(EX35['netto'])} netto i "
            "rikssnitt. Se skatt, jobbskatteavdrag och bruttolön.").replace("\u00a0", " ")
    crumbs = [("Hem", "/"), ("Lön & jobb", "/lon-och-jobb"), ("Löneräknare", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Löneräknare 2026 – lön efter skatt",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Lön & jobb", "item": S.SITE + "/lon-och-jobb"},
            {"@type": "ListItem", "position": 3, "name": "Löneräknare", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    rows = []
    for lon in TABELL:
        b = berakna(lon)
        rows.append(f"<tr><td>{fmt(lon)}</td><td><strong>{fmt(rnd(b['netto']))}</strong></td>"
                    f"<td>{fmt(rnd(b['skatt']))}</td><td>{pct(b['andel'] * 100)}</td></tr>")
    tab_rows = "".join(rows)

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Löneräknare 2026</div>
<h1>Hur mycket får du ut efter skatt?</h1>
<p class="gk-lead">Skriv in din bruttolön och välj kommun så ser du direkt din nettolön, med samma regler som Skatteverkets skattetabeller 2026.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Alla 290 kommuner · Källa: <a href="{SRC['belopp']}" target="_blank" rel="noopener">Skatteverket</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="lonform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="lon">Bruttolön per månad</label>
<div class="gk-input"><input id="lon" inputmode="numeric" autocomplete="off" value="{fmt(K['DEF_LON'])}"><span class="unit">kr/mån</span></div>
<div class="gk-seg" style="--n:3" id="lonq" role="group" aria-label="Vanliga löner">
<button type="button" data-v="25000" aria-pressed="false">25 000</button>
<button type="button" data-v="35000" aria-pressed="true">35 000</button>
<button type="button" data-v="50000" aria-pressed="false">50 000</button>
</div>
<span class="gk-hint">Lönen före skatt, som det står i ditt anställningsavtal.</span>
</div>

<div class="gk-field">
<label for="kommun">Kommun du bor i</label>
<div class="gk-input"><select id="kommun">{opts}</select></div>
<span class="gk-hint">Kommunal- och regionskatt {K['AR']} enligt SCB.</span>
</div>

<details class="gk-more" id="more">
<summary>Ålder och kyrkoavgift</summary>
<div class="gk-stack" style="gap:14px">
<fieldset class="gk-fieldset">
<legend class="gk-legend">Ålder vid årets början</legend>
<div class="gk-seg" style="--n:2" id="alder" role="group" aria-label="Ålder">
<button type="button" data-v="0" aria-pressed="true">Under 66 år<small>född {K['AR'] - 66} eller senare</small></button>
<button type="button" data-v="1" aria-pressed="false">66 år eller äldre<small>född {K['AR'] - 67} eller tidigare</small></button>
</div>
</fieldset>
<fieldset class="gk-fieldset">
<legend class="gk-legend">Med i Svenska kyrkan?</legend>
<div class="gk-seg" style="--n:2" id="kyrka" role="group" aria-label="Kyrkoavgift">
<button type="button" data-v="0" aria-pressed="true">Nej</button>
<button type="button" data-v="1" aria-pressed="false">Ja<small>betalar kyrkoavgift</small></button>
</div>
</fieldset>
<div class="gk-field" id="kyrkaF" hidden>
<label for="kyrkaS">Kyrkoavgift i din församling</label>
<div class="gk-input"><input id="kyrkaS" inputmode="decimal" autocomplete="off" value="{pct(K['KYRKA'], 2)}"><span class="unit">%</span></div>
<span class="gk-hint">{pct(K['KYRKA'], 2)} % är riksgenomsnittet {K['AR']} enligt Svenska kyrkan. Din församlings sats står i beslutet om slutlig skatt.</span>
</div>
</div>
</details>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:14px" aria-labelledby="nbH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="nbH" style="font-size:22px">Från netto till brutto</h2>
<p class="gk-hint">Vilken bruttolön behöver du för att få ut ett visst belopp? Räknas med kommun och val ovan.</p>
</div>
<div class="gk-field">
<label for="netto">Nettolön du vill ha per månad</label>
<div class="gk-input"><input id="netto" inputmode="numeric" autocomplete="off" value="{fmt(K['DEF_NETTO'])}"><span class="unit">kr/mån</span></div>
</div>
<div id="nbRes" aria-live="polite"></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Din nettolön per månad</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån efter skatt</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<div class="gk-table-wrap" style="margin-top:14px"><table class="gk-table" id="split"></table></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="/kalkylatorer/loneforhandling"><span>Dags för lönesamtal?<small>Löneförhandling – se vad du ska begära i ditt yrke</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/yrkeslon/"><span>Vad tjänar andra?<small>Lön per yrke – medianlön för 105 yrken</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/arbetsgivaravgift-kalkylator"><span>Vad kostar lönen arbetsgivaren?<small>Arbetsgivaravgift och total lönekostnad</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Lön efter skatt för vanliga löner</h2>
<p>Så mycket blir kvar av lönen {K['AR']} med genomsnittlig kommunalskatt ({pct(K['SNITT_KS'], 2)} %), om du är under 66 år och inte betalar kyrkoavgift.</p>
<div class="gk-table-wrap"><table class="gk-table">
<thead><tr><th scope="col">Bruttolön</th><th scope="col">Nettolön</th><th scope="col">Skatt</th><th scope="col">Skatt %</th></tr></thead>
<tbody>{tab_rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor per månad, slutlig skatt {K['AR']} delad med 12. Välj din kommun i kalkylatorn för exakt belopp.</caption>
</table></div>

<h2>Så räknas skatten på lönen</h2>
<p>Kalkylatorn räknar ut din skatt för hela året och delar den med 12:</p>
<ol>
<li><strong>Grundavdraget</strong> dras från årslönen – {kr(K['GA_MIN'])} till {kr(K['GA_MAX'])} beroende på inkomst, mer om du har fyllt 66 år.</li>
<li>På resten betalar du <strong>kommunalskatt</strong>, {pct(LAG[1], 2)}–{pct(HOG[1], 2)} % beroende på kommun.</li>
<li>Är årslönen över {kr(K['BRYT'])} (ungefär {fmt(round(K['BRYT'] / 12, -3))} kr i månaden) tillkommer <strong>statlig skatt</strong>, 20 % på det som är över.</li>
<li><strong>Jobbskatteavdraget</strong> och skattereduktionen för förvärvsinkomst (högst 1 500 kr om året) sänker skatten.</li>
<li>Public service-avgift (1 %, högst 1 184 kr om året) och begravningsavgift ({pct(K['BEGR'], 3)} %) läggs till, och kyrkoavgift om du är med i Svenska kyrkan.</li>
</ol>
<p>Den allmänna pensionsavgiften på 7 % räknas av krona för krona mot skatten, så för de flesta påverkar den inte nettolönen.</p>

<h2>Räkna ut bruttolön från nettolön</h2>
<p>Vet du vad du vill ha ut i handen? Skriv beloppet i rutan <em>Från netto till brutto</em>, så räknar kalkylatorn baklänges med samma regler. För {kr(30000)} netto behöver du ungefär <strong>{kr(B30)}</strong> i bruttolön med genomsnittlig kommunalskatt.</p>

<h2>Därför skiljer sig lönebeskedet</h2>
<p>Arbetsgivaren drar preliminär skatt enligt Skatteverkets skattetabell. Den går i steg om 200 kr (100 kr upp till 20 000 kr) och räknar med hela procentsatser, så avdraget blir sällan exakt samma som skatten här. Skillnaden jämnas ut när du får beslut om slutlig skatt – som skatteåterbäring eller <a href="{SRC['kvarskatt']}" target="_blank" rel="noopener">kvarskatt</a>. Vi har stämt av modellen mot Skatteverkets tabeller 32 och 33 för {K['AR']}.</p>

<h2>Vanliga frågor om lön efter skatt</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['belopp']}" target="_blank" rel="noopener">Skatteverket – Belopp och procent, inkomstår 2026</a> – skiktgräns 643 000 kr, brytpunkt 660 400 kr (66+: 760 500 kr), grundavdrag 17 400–45 600 kr, public service-avgift högst 1 184 kr, allmän pensionsavgift 7 %, begravningsavgift 0,292 % (Stockholm 0,07 %, Tranås 0,285 %)</li>
<li><a href="{SRC['skv433']}" target="_blank" rel="noopener">Skatteverket – Teknisk beskrivning för skattetabeller 2026 (SKV 433)</a> – jobbskatteavdrag, skattereduktion för förvärvsinkomst (0,75 %, högst 1 500 kr), public service-avgift 1 %, pensionsavgiften räknas av mot skatten, inkomststeg i tabellerna</li>
<li>Skatteverket – månadstabell <a href="{SRC['tab32']}" target="_blank" rel="noopener">32</a> och <a href="{SRC['tab33']}" target="_blank" rel="noopener">33</a> för 2026 – kontroll av modellen</li>
<li><a href="{SRC['scb']}" target="_blank" rel="noopener">SCB – Kommunalskatterna 2026</a> – rikssnitt 32,38 %, lägst {LAG[0]} {pct(LAG[1], 2)} %, högst {HOG[0]} {pct(HOG[1], 2)} %</li>
<li><a href="{SRC['kyrka']}" target="_blank" rel="noopener">Svenska kyrkan – Kyrkoavgiften</a> – riksgenomsnitt {pct(K['KYRKA'], 2)} % {K['AR']}</li>
<li><a href="{SRC['kvarskatt']}" target="_blank" rel="noopener">Skatteverket – Kvarskatt</a> – slutlig skatt och skatteåterbäring</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/marginalskattekalkylator"><span>Marginalskatt<small>Hur mycket av en löneökning blir kvar?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/skatteaterbarings-kalkylator"><span>Skatteåterbäring<small>Får du tillbaka skatt eller blir det kvarskatt?</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-lon" type="application/json">{json.dumps(K, ensure_ascii=False)}</script>
<script defer src="/assets/skatt2026.js?v=20261001"></script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Hur mycket får du ut efter skatt? Löneräknare 2026", jsonld=ld)
            + S.header() + body + S.footer("Nettolönen är en uppskattning av slutlig skatt – skatteavdraget på lönebeskedet följer Skatteverkets skattetabell."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-lon').textContent);
  var T = window.GKSkatt2026;
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v), 0) + '\u00a0kr'; };
  var pc = function (x, d) { return GK.fmt(x, d === undefined ? 1 : d) + '\u00a0%'; };
  var st = { aldre: false, kyrka: false };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', String(x.getAttribute('data-v')) === String(v) ? 'true' : 'false'); }); }
  seg('lonq', function (v) { $('lon').value = GK.fmt(+v, 0); });
  seg('alder', function (v) { st.aldre = v === '1'; });
  seg('kyrka', function (v) { st.kyrka = v === '1'; $('kyrkaF').hidden = !st.kyrka; });
  $('lon').addEventListener('input', function () { press('lonq', GK.parse($('lon').value)); calc(); });
  $('kommun').addEventListener('change', calc);
  ['kyrkaS', 'netto'].forEach(function (id) { $(id).addEventListener('input', calc); });
  ['lon', 'netto'].forEach(function (id) { GK.groupInput($(id)); });

  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  /* Val i formuläret -> skatteparametrar */
  function opts() {
    var o = $('kommun').options[$('kommun').selectedIndex], namn = o.value;
    var ky = 0;
    if (st.kyrka) { ky = GK.parse($('kyrkaS').value); if (!isFinite(ky) || ky < 0 || ky > 5) ky = C.KYRKA; }
    return { namn: namn, ks: +o.getAttribute('data-ks'), bg: C.BEGR_SPEC[namn] !== undefined ? C.BEGR_SPEC[namn] : C.BEGR, ky: ky, aldre: st.aldre };
  }

  /* Modell – samma som scripts/build_loneraknare.py */
  function skatt(lon, o) { return T.skattAr(lon * 12, { kommunalskatt: o.ks, begravning: o.bg, kyrkoavgift: o.ky, aldre: o.aldre }); }
  function berakna(lon, o) {
    var r = skatt(lon, o), r2 = skatt(lon + C.MS_STEG, o);
    return { r: r, netto: r.netto / 12, skatt: r.total / 12, andel: lon > 0 ? r.total / (lon * 12) : 0, ms: (r2.total - r.total) / (C.MS_STEG * 12) };
  }
  function bruttoForNetto(mal, o) {
    var lo = 0, hi = C.MAX_LON;
    if (skatt(hi, o).netto / 12 < mal) return null;
    while (lo < hi) {
      var mid = Math.floor((lo + hi) / 2);
      if (skatt(mid, o).netto / 12 >= mal) hi = mid; else lo = mid + 1;
    }
    return lo;
  }

  function clear(msg) {
    $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'verdict', 'split', 'how'].forEach(function (id) { $(id).innerHTML = ''; });
  }

  function calc() {
    var lon = val('lon'), o = opts();
    nettoTillBrutto(o);
    if (!lon || lon < 100) return clear('Fyll i din lön före skatt.');
    var b = berakna(lon, o), r = b.r;
    var plats = o.namn ? o.namn : 'rikssnitt';
    $('resBig').textContent = GK.fmt(Math.round(b.netto), 0);
    $('resSub').textContent = 'av ' + kr(lon) + ' före skatt i ' + plats + '. Du betalar ' + kr(b.skatt) + ' i skatt, ' + pc(b.andel * 100) + ' av lönen.';
    $('tiles').innerHTML = tile('Skatt per månad', kr(b.skatt), pc(b.andel * 100) + ' av lönen') +
      tile('Marginalskatt', pc(b.ms * 100), 'Så mycket av en löneökning går till skatt') +
      tile('Nettolön per år', kr(r.netto), 'Bruttolön ' + kr(lon * 12)) +
      tile('Jobbskatteavdrag', kr(r.jobbskatteavdrag / 12) + '/mån', 'Ingår redan i skatten');

    var v = '';
    var bryt = o.aldre ? C.BRYT66 : C.BRYT;
    if (r.statligSkatt > 0) {
      v += verdict('warn', 'Du betalar statlig skatt', 'Lönen är över brytpunkten ' + kr(bryt) + ' om året (' + kr(bryt / 12) + ' i månaden). På det som är över betalar du 20 % extra – ' + kr(r.statligSkatt / 12) + ' i månaden.');
    }
    if (o.namn) {
      var s = berakna(lon, { ks: C.SNITT_KS, bg: C.BEGR, ky: o.ky, aldre: o.aldre }), d = Math.round(b.netto) - Math.round(s.netto);
      if (d > 0) v += verdict('good', kr(d) + ' mer i månaden än i snittet', 'Kommunalskatten i ' + o.namn + ' är ' + pc(o.ks, 2) + ' mot rikssnittet ' + pc(C.SNITT_KS, 2) + '. Med snittskatt hade du fått ' + kr(s.netto) + '.');
      else if (d < 0) v += verdict('info', kr(-d) + ' mindre i månaden än i snittet', 'Kommunalskatten i ' + o.namn + ' är ' + pc(o.ks, 2) + ' mot rikssnittet ' + pc(C.SNITT_KS, 2) + '. Med snittskatt hade du fått ' + kr(s.netto) + '.');
      else v += verdict('good', 'Samma som i snittet', 'Kommunalskatten i ' + o.namn + ' är ' + pc(o.ks, 2) + ', samma som rikssnittet.');
    } else {
      var lag = null, hog = null;
      Array.prototype.forEach.call($('kommun').options, function (x) {
        if (!x.value) return; var k = +x.getAttribute('data-ks');
        if (!lag || k < lag.k) lag = { n: x.value, k: k }; if (!hog || k > hog.k) hog = { n: x.value, k: k };
      });
      var nl = berakna(lon, { ks: lag.k, bg: C.BEGR_SPEC[lag.n] || C.BEGR, ky: o.ky, aldre: o.aldre }).netto;
      var nh = berakna(lon, { ks: hog.k, bg: C.BEGR_SPEC[hog.n] || C.BEGR, ky: o.ky, aldre: o.aldre }).netto;
      v += verdict('info', 'Välj din kommun för exakt belopp', 'Med din lön skiljer det ' + kr(Math.round(nl) - Math.round(nh)) + ' i månaden mellan ' + lag.n + ' (' + pc(lag.k, 2) + ') och ' + hog.n + ' (' + pc(hog.k, 2) + ').');
    }
    $('verdict').innerHTML = v;

    var rad = function (l, x, sign) { return '<tr><td>' + l + '</td><td>' + (sign || '') + GK.fmt(Math.round(x / 12), 0) + '</td></tr>'; };
    var apaNetto = r.pensionsavgift - Math.min(r.pensionsavgift, r.kommunalskatt + r.statligSkatt);
    $('split').innerHTML = '<thead><tr><th scope="col">Så fördelas skatten</th><th scope="col">kr/mån</th></tr></thead><tbody>' +
      rad('Kommunal- och regionskatt (' + pc(o.ks, 2) + ')', r.kommunalskatt, '') +
      (r.statligSkatt > 0 ? rad('Statlig skatt (20 %)', r.statligSkatt, '') : '') +
      (apaNetto > 0 ? rad('Allmän pensionsavgift (7 %)', apaNetto, '') : '') +
      rad('Jobbskatteavdrag', r.jobbskatteavdrag, '−') +
      (r.forvarvsreduktion > 0 ? rad('Skattereduktion förvärvsinkomst', r.forvarvsreduktion, '−') : '') +
      rad('Public service-avgift', r.publicService, '') +
      rad('Begravningsavgift (' + pc(o.bg, o.bg === 0.07 ? 2 : 3) + ')', r.begravning, '') +
      (r.kyrkoavgift > 0 ? rad('Kyrkoavgift (' + pc(o.ky, 2) + ')', r.kyrkoavgift, '') : '') +
      '<tr><td><strong>Skatt totalt</strong></td><td><strong>' + GK.fmt(Math.round(b.skatt), 0) + '</strong></td></tr></tbody>' +
      '<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Avrundat till hela kronor per månad.</caption>';

    $('how').innerHTML =
      '<p>Årslön: ' + kr(lon) + ' × 12 = ' + kr(lon * 12) + '. Grundavdrag ' + kr(r.grundavdrag) + (o.aldre ? ' (förhöjt för dig som fyllt 66 år)' : '') + ' ger en beskattningsbar inkomst på ' + kr(r.bfi) + '.</p>' +
      '<p>Kommunal- och regionskatt ' + pc(o.ks, 2) + ' = ' + kr(r.kommunalskatt) + ' om året' + (r.statligSkatt > 0 ? ', statlig skatt 20 % på ' + kr(r.bfi - T.SKIKT) + ' över skiktgränsen = ' + kr(r.statligSkatt) : '') + '. Allmän pensionsavgift 7 % (' + kr(r.pensionsavgift) + ') räknas av mot skatten. Jobbskatteavdrag ' + kr(r.jobbskatteavdrag) + (r.forvarvsreduktion > 0 ? ' och skattereduktion för förvärvsinkomst ' + kr(r.forvarvsreduktion) : '') + ' dras av.</p>' +
      '<p>Public service-avgift ' + kr(r.publicService) + ', begravningsavgift ' + kr(r.begravning) + (r.kyrkoavgift > 0 ? ' och kyrkoavgift ' + kr(r.kyrkoavgift) : '') + ' läggs till. Skatt för året: ' + kr(r.total) + ', det vill säga ' + kr(b.skatt) + ' i månaden.</p>' +
      '<p>Det är den slutliga skatten för ett år med samma lön varje månad. Skatteavdraget på lönebeskedet följer Skatteverkets skattetabell och kan skilja sig något.</p>';
  }

  var nbLast = null;
  function nettoTillBrutto(o) {
    var mal = val('netto');
    if (!mal || mal < 100) { $('nbRes').innerHTML = ''; nbLast = null; return; }
    var b = bruttoForNetto(mal, o);
    if (b === null) { $('nbRes').innerHTML = '<p class="gk-hint">Beloppet är för högt för kalkylatorn.</p>'; nbLast = null; return; }
    var x = berakna(b, o);
    nbLast = b;
    $('nbRes').innerHTML = '<div class="gk-tiles">' + tile('Bruttolön som behövs', kr(b) + '/mån', 'Ger ' + kr(x.netto) + ' efter skatt') +
      tile('Skatt', kr(x.skatt) + '/mån', pc(x.andel * 100) + ' av bruttolönen') + '</div>' +
      '<button type="button" class="gk-btn" id="nbUse" style="margin-top:12px">Räkna med ' + GK.fmt(b, 0) + ' kr i lön</button>';
  }
  $('nbRes').addEventListener('click', function (e) {
    if (!e.target.closest('#nbUse') || nbLast === null) return;
    $('lon').value = GK.fmt(nbLast, 0); press('lonq', nbLast); calc();
    var res = document.querySelector('.gk-result'); if (res && res.scrollIntoView) res.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  /* Delningslänkar från gamla sidan: ?lon=35000&k=huddinge&a=66 */
  try {
    var q = new URLSearchParams(location.search);
    var ql = parseInt(q.get('lon'), 10);
    if (ql > 0 && ql < 10000000) { $('lon').value = GK.fmt(ql, 0); press('lonq', ql); }
    var qk = q.get('k');
    if (qk) Array.prototype.forEach.call($('kommun').options, function (x, i) { if (x.getAttribute('data-slug') === qk) $('kommun').selectedIndex = i; });
    if (q.get('a') === '66') { st.aldre = true; press('alder', '1'); $('more').open = true; }
  } catch (e) {}

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "loneraknare.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    for lon, kommun, ky, aldre in CASES:
        ks = dict(KOMMUNER)[kommun] if kommun else K["SNITT_KS"]
        b = berakna(lon, ks, begr(kommun), ky, aldre)
        r = b["r"]
        print(f"{lon:>6} {kommun or 'rikssnitt':<10} kyrka {ky:<4} 66+ {aldre!s:<5} netto {rnd(b['netto'])} skatt {rnd(b['skatt'])} "
              f"({b['andel'] * 100:.1f} %) marg {b['ms'] * 100:.1f} % år {rnd(r['netto'])} jsa {rnd(r['jobbskatteavdrag'] / 12)} "
              f"statlig {rnd(r['statlig_skatt'] / 12)}")
    for mal, kommun in NB_CASES:
        ks = dict(KOMMUNER)[kommun] if kommun else K["SNITT_KS"]
        b = brutto_for_netto(mal, ks, begr(kommun))
        print(f"netto {mal} i {kommun or 'rikssnitt'} -> brutto {b} (ger {rnd(berakna(b, ks, begr(kommun))['netto'])})")


CASES = [(35000, "", 0.0, False), (25000, "Huddinge", 0.0, False), (70000, "Stockholm", 0.0, False),
         (45000, "Dorotea", 1.05, False), (35000, "", 0.0, True), (60000, "Tranås", 0.0, False)]
NB_CASES = [(30000, ""), (40000, "Stockholm"), (25000, "Göteborg")]

if __name__ == "__main__":
    main()
