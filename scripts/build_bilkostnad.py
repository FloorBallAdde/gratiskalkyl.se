#!/usr/bin/env python3
"""Bygger kalkylatorer/bilkostnadsraknare.html i den nya verktygsmallen.

Modell (samma i Python-referensen nedan och i sidans JS):
  Värdeminskning: bilen tappar samma procent p av sitt värde varje år (användarens antagande).
    Värde efter k år = pris × (1 − p/100)^k. Tappat = pris − värde efter n år (n = år du behåller bilen).
    Värdeminskning per år i kalkylen = tappat / n.
  Drivmedel per år = mil per år × förbrukning (l/mil eller kWh/mil) × pris (kr/l eller kr/kWh).
  Årskostnad = värdeminskning + drivmedel + försäkring × 12 + fordonsskatt + service och däck
               + (parkering + ränta på billån + övrigt) × 12.
  Per månad = årskostnad / 12. Per mil = årskostnad / mil per år.
  Procentsats från annonspriser = 1 − (äldre bils pris / yngre bils pris)^(1 / åldersskillnad).

Siffror med källa (verifierade 1 oktober 2026):
  - Snittkörsträcka: Trafikanalys, Körsträckor 2025 (publicerad 17 april 2026).
  - Bensin- och dieselpris: Preems listpriser (företagskort, inkl. moms): bensin 95 från 2 oktober, diesel från 1 oktober 2026 (kontrollerat 3 oktober 2026).
  - Skattefri bilersättning egen bil 25 kr/mil: Skatteverket, Belopp och procent 2026.
  - Fordonsskatt: grundbelopp 360 kr, koldioxidbelopp 22 kr/g över 111 g/km, förhöjt belopp (malus)
    107 kr/g över 75 g och 132 kr/g över 125 g de tre första åren för bilar skattepliktiga från 1 juni
    2022: Vägtrafikskattelag (2006:227) 2 kap. 8, 9 och 9 a §§ samt Transportstyrelsen.
Ingen källa för "typisk" värdeminskning hittades – procentsatsen är ett tydligt märkt exempel.
Försäkring, service/däck och fordonsskatt för bensinbil är exempel som användaren byter ut.

    python3 scripts/build_bilkostnad.py
"""
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/bilkostnadsraknare"
UPDATED = "3 oktober 2026"

# Konstanter med källa – byt här vid prisuppdatering eller årsskifte
K = {
    "PRIS": {"bensin": 18.89, "diesel": 23.14},  # Preem listpris företagskort, kr/l inkl. moms (bensin från 2 okt, diesel från 1 okt 2026)
    "PRIS_DATUM": "3 oktober 2026",
    "KOR_PRIVAT": 1155,        # Trafikanalys, Körsträckor 2025: privatägda personbilar, mil/år
    "KOR_ALLA": 1243,          # alla personbilar
    "KOR_LADDBAR": 1700,       # elbilar och laddhybrider, ungefär
    "MILERS": 25,              # Skatteverket: skattefri bilersättning egen bil 2026, kr/mil
    "GRUND": 360,              # VSL 2 kap. 8 §: grundbelopp, kr/år
    "CO2_KR": 22,              # VSL 2 kap. 9 §: kr per gram över CO2_GRANS
    "CO2_GRANS": 111,          # g/km
    "MALUS_KR1": 107,          # VSL 2 kap. 9 a §: kr/g över 75 g upp till 125 g, tre första åren
    "MALUS_KR2": 132,          # kr/g över 125 g
    "MALUS_G1": 75,
    "MALUS_G2": 125,
}
# Exempelvärden i formuläret (märkta som exempel på sidan – inga påståenden om vad som är typiskt)
D = {
    "PRIS": 300000, "PROC": 15, "AR": 5, "ALDER": 0,
    "FORBR": {"bensin": 0.7, "diesel": 0.7, "el": 2.0},
    "FORS": 500,     # kr/mån
    "SERV": 6000,    # kr/år
    "CO2_EX": 120,   # g/km – exempel för fordonsskatten
}

SRC = {
    "trafa": "https://www.trafa.se/globalassets/statistik/vagtrafik/korstrackor/2025/korstrackor-2025---2026-04-17.pdf",
    "preem": "https://www.preem.se/foretag/kund-hos-preem/listpriser/",
    "skv": "https://www.skatteverket.se/privat/skatter/beloppochprocent/2026.4.1522bf3f19aea8075ba21.html",
    "ts_storlek": "https://www.transportstyrelsen.se/sv/vagtrafik/fordon/skatter-och-avgifter/fordonsskatt/skattens-storlek/",
    "ts_skatt": "https://www.transportstyrelsen.se/sv/vagtrafik/fordon/skatter-och-avgifter/fordonsskatt/",
    "ts_skulder": "https://www.transportstyrelsen.se/sv/vagtrafik/e-tjanster-och-blanketter/e-tjanster-inom-vagtrafik/fordon/fordonets-skulder/",
    "vsl": "https://www.riksdagen.se/sv/dokument-lagar/dokument/svensk-forfattningssamling/_sfs-2006-227/",
}


def r(x, d=0):
    """Avrundning som i webbläsaren (halvt uppåt) – för att jämföra med JS."""
    q = Decimal(1).scaleb(-d)
    return float(Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP))


def fmt(n, d=0):
    s = f"{r(n, d):,.{d}f}"
    return s.replace(",", " ").replace(".", ",")


def kr10(v):
    return fmt(r(v / 10) * 10)


# ── Python-referens – samma logik som sidans JS ──────────────────────────
def varde(pris, proc, ar):
    vals = [pris * (1 - proc / 100) ** k for k in range(ar + 1)]
    tapp = pris - vals[-1]
    return {"vals": vals, "slut": vals[-1], "tapp": tapp, "per_ar": tapp / ar, "per_man": tapp / ar / 12,
            "forsta": pris * proc / 100, "andel": tapp / pris * 100}


def kostnad(pris, proc, ar, mil, forbr, bpris, fors, skatt, serv, park=0, ranta=0, ovr=0):
    """fors, park, ranta, ovr i kr/mån – skatt och serv i kr/år – mil per år."""
    v = varde(pris, proc, ar)
    poster = {
        "varde": v["per_ar"],
        "drivmedel": mil * forbr * bpris,
        "forsakring": fors * 12,
        "skatt": skatt,
        "service": serv,
        "parkering": park * 12,
        "ranta": ranta * 12,
        "ovrigt": ovr * 12,
    }
    tot = sum(poster.values())
    return {"poster": poster, "ar": tot, "man": tot / 12, "permil": tot / mil if mil > 0 else None, "v": v}


def procent_fran_priser(yngre, aldre, ar):
    return (1 - (aldre / yngre) ** (1 / ar)) * 100


def fordonsskatt(co2, malus=False):
    """Bensinbil (och elbil med co2 = 0) – för räkneexemplen i texten."""
    if malus:
        return K["GRUND"] + K["MALUS_KR1"] * max(0, min(co2, K["MALUS_G2"]) - K["MALUS_G1"]) + \
            K["MALUS_KR2"] * max(0, co2 - K["MALUS_G2"])
    return K["GRUND"] + K["CO2_KR"] * max(0, co2 - K["CO2_GRANS"])


PB, PD = K["PRIS"]["bensin"], K["PRIS"]["diesel"]
SKATT_EX = fordonsskatt(D["CO2_EX"])            # 558 kr
SKATT_MALUS = fordonsskatt(D["CO2_EX"], True)   # 5 175 kr
EX = kostnad(D["PRIS"], D["PROC"], D["AR"], K["KOR_PRIVAT"], D["FORBR"]["bensin"], PB, D["FORS"], SKATT_EX, D["SERV"])
V3 = varde(D["PRIS"], D["PROC"], 3)
p2 = lambda v: fmt(v, 2)  # noqa: E731

FAQ = [
    ("Hur mycket kostar en bil i månaden?",
     "Lägg ihop allt bilen kostar under ett år – värdeminskning, drivmedel, försäkring, fordonsskatt, service och däck, "
     "parkering och ränta på billån – och dela med 12. Ett exempel: en bil för 300 000 kr som tappar 15 % i värde per år och "
     f"behålls i 5 år, körs {fmt(K['KOR_PRIVAT'])} mil om året och drar 0,7 liter bensin per mil à {p2(PB)} kr, med 500 kr i månaden "
     f"i försäkring, {fmt(SKATT_EX)} kr i skatt och 6 000 kr om året för service och däck, kostar ungefär {kr10(EX['man'])} kr i månaden. "
     "Fyll i dina egna belopp i kalkylatorn."),
    ("Hur mycket tappar en ny bil i värde per år?",
     "Det finns ingen officiell siffra – det beror på modell, körsträcka, skick och efterfrågan. Ta reda på det för din modell genom "
     "att jämföra annonspriser för samma modell i olika åldrar, och räkna om skillnaden till procent per år i kalkylatorn. "
     "Tappar bilen 15 % per år är den värd 85 % av priset efter ett år och 44 % efter fem år."),
    ("Hur räknar man ut värdeminskning på en bil?",
     "Värdet efter ett antal år är inköpspriset × (1 − procentsatsen) upphöjt till antalet år. Värdeminskningen är inköpspriset "
     "minus det värdet. En bil för 300 000 kr som tappar 15 % per år är värd 300 000 × 0,85⁵ = "
     f"{kr10(varde(300000, 15, 5)['slut'])} kr efter fem år. Den har då tappat {kr10(varde(300000, 15, 5)['tapp'])} kr, "
     f"eller {kr10(varde(300000, 15, 5)['per_ar'])} kr per år i snitt."),
    ("Hur mycket är en ny bil värd efter 3 år?",
     "Det beror på hur snabbt just den modellen tappar i värde. Räknar du med 15 % per år är bilen värd 0,85³ = "
     f"{fmt(0.85 ** 3 * 100)} % av nypriset efter tre år – en bil för 300 000 kr är då värd ungefär {kr10(V3['slut'])} kr. "
     f"Med 10 % per år blir det {fmt(0.9 ** 3 * 100)} % och med 20 % per år {fmt(0.8 ** 3 * 100)} %."),
    ("Hur räknar man på en ny bil?",
     "Gör en bilkalkyl (personbilskalkyl) för hela tiden du tänker ha bilen: vad den kostar, vad den kan säljas för när du "
     "byter och alla kostnader under tiden. Skillnaden mellan köp- och säljpris delad med antalet år är värdeminskningen per år. "
     "Lägg till drivmedel, försäkring, skatt, service, däck och parkering, och ränta om du lånar. Amorteringen på lånet är ingen "
     "extra kostnad – den betalar av bilen, och det är redan räknat i värdeminskningen."),
    ("Vad kostar det att köra bil per mil?",
     "Dela bilens årskostnad med antalet mil du kör. Bara bränslet kostar förbrukningen gånger literpriset: 0,7 liter per mil "
     f"med bensin för {p2(PB)} kr/l blir {p2(0.7 * PB)} kr per mil. Med alla kostnader blir det mer. Som jämförelse är den "
     f"skattefria milersättningen för egen bil {K['MILERS']} kr per mil 2026."),
    ("Hur mycket är fordonsskatten för en elbil?",
     f"{fmt(K['GRUND'])} kr per år. Fordonsskatten är ett grundbelopp på {K['GRUND']} kr plus ett koldioxidbelopp, och en elbil "
     "släpper inte ut någon koldioxid. Därför betalar den bara grundbeloppet."),
    ("Hur många mil kör en vanlig bil per år?",
     f"Enligt Trafikanalys körde privatägda personbilar i snitt {fmt(K['KOR_PRIVAT'])} mil under 2025 och alla personbilar "
     f"{fmt(K['KOR_ALLA'])} mil. Elbilar och laddhybrider körde längre, ungefär {fmt(K['KOR_LADDBAR'])} mil."),
]

CHEV = S.ICON_CHEV


def seg(vals, pressed, small=None):
    out = []
    for v, lab in vals:
        sm = f"<small>{small[v]}</small>" if small and v in small else ""
        out.append(f'<button type="button" data-v="{v}" aria-pressed="{"true" if v == pressed else "false"}">{lab}{sm}</button>')
    return "".join(out)


def page():
    title = "Värdeminskning bil & bilkostnad per månad | GratisKalkyl"
    desc = ("Vad kostar bilen per månad och per mil? Räkna ut värdeminskningen per år, drivmedel, försäkring, "
            "skatt och service. Elbilar betalar 360 kr i fordonsskatt.")
    crumbs = [("Hem", "/"), ("Bil & energi", "/bil-och-energi"), ("Bilkostnadsräknare", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Bilkostnadsräknare 2026 – bilkostnad per månad och värdeminskning",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-03"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Bil & energi", "item": S.SITE + "/bil-och-energi"},
            {"@type": "ListItem", "position": 3, "name": "Bilkostnadsräknare", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    rows = "".join(
        f"<tr><td>{p} %</td>" + "".join(f"<td>{fmt((1 - p / 100) ** n * 100)} %</td>" for n in (1, 3, 5)) + "</tr>"
        for p in (10, 15, 20, 25))
    k0 = lambda v: fmt(v)  # noqa: E731

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Bilkostnadsräknare 2026</div>
<h1>Vad kostar bilen per månad?</h1>
<p class="gk-lead">Räkna ut vad bilen kostar per månad och per mil – och hur mycket den tappar i värde varje år.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Bensinpris {K['PRIS_DATUM']} · Källa: <a href="{SRC['trafa']}" target="_blank" rel="noopener">Trafikanalys</a>, <a href="{SRC['ts_storlek']}" target="_blank" rel="noopener">Transportstyrelsen</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="bkform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="pris">Bilens pris</label>
<div class="gk-input"><input id="pris" inputmode="numeric" autocomplete="off" value="{k0(D['PRIS'])}"><span class="unit">kr</span></div>
<span class="gk-hint">Vad du betalar för bilen. Förifyllt exempel.</span>
</div>

<div class="gk-field">
<label for="proc">Värdeminskning per år</label>
<div class="gk-input"><input id="proc" inputmode="decimal" autocomplete="off" value="{D['PROC']}"><span class="unit">% per år</span></div>
<span class="gk-hint">Exempel – ditt antagande. Räkna ut en procentsats för din modell från annonspriser i kortet <a href="#vH">Värdeminskning</a>.</span>
</div>

<div class="gk-field">
<label for="ar">Hur länge behåller du bilen?</label>
<div class="gk-input"><input id="ar" inputmode="numeric" autocomplete="off" value="{D['AR']}"><span class="unit">år</span></div>
<div class="gk-seg" style="--n:3" id="arq" role="group" aria-label="Antal år">
{seg([(3, "3 år"), (5, "5 år"), (8, "8 år")], D['AR'])}
</div>
</div>

<div class="gk-field">
<label for="mil">Så långt kör du per år</label>
<div class="gk-input"><input id="mil" inputmode="numeric" autocomplete="off" value="{k0(K['KOR_PRIVAT'])}"><span class="unit">mil/år</span></div>
<div class="gk-seg" style="--n:3" id="milq" role="group" aria-label="Körsträcka">
{seg([(K['KOR_PRIVAT'], k0(K['KOR_PRIVAT'])), (1500, k0(1500)), (2000, k0(2000))], K['KOR_PRIVAT'], {K['KOR_PRIVAT']: "snittet"})}
</div>
<span class="gk-hint">Snittet för privatägda bilar 2025 enligt Trafikanalys. 1 mil = 10 km.</span>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Drivmedel</legend>
<div class="gk-seg" style="--n:3" id="typ" role="group" aria-label="Drivmedel">
{seg([("bensin", "Bensin"), ("diesel", "Diesel"), ("el", "El")], "bensin")}
</div>
</fieldset>

<div class="gk-grid2">
<div class="gk-field">
<label for="forbr">Förbrukning</label>
<div class="gk-input"><input id="forbr" inputmode="decimal" autocomplete="off" value="0,7"><span class="unit" id="forbrUnit">l/mil</span></div>
</div>
<div class="gk-field">
<label for="bpris" id="bprisLabel">Pris</label>
<div class="gk-input"><input id="bpris" inputmode="decimal" autocomplete="off" value="{p2(PB)}"><span class="unit" id="bprisUnit">kr/l</span></div>
</div>
</div>
<span class="gk-hint" id="dmHint" style="margin-top:-8px"></span>

<div class="gk-field">
<label for="fors">Försäkring</label>
<div class="gk-input"><input id="fors" inputmode="numeric" autocomplete="off" value="{k0(D['FORS'])}"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Exempel – fyll i ditt pris. Försäkringen beror på bil, ålder och var du bor.</span>
</div>

<div class="gk-field">
<label for="skatt">Fordonsskatt</label>
<div class="gk-input"><input id="skatt" inputmode="numeric" autocomplete="off" value="{k0(SKATT_EX)}"><span class="unit">kr/år</span></div>
<span class="gk-hint" id="skattHint"></span>
</div>

<div class="gk-field">
<label for="serv">Service och däck</label>
<div class="gk-input"><input id="serv" inputmode="numeric" autocomplete="off" value="{k0(D['SERV'])}"><span class="unit">kr/år</span></div>
<span class="gk-hint">Exempel – fyll i vad service, däck och däckbyte kostar dig per år.</span>
</div>

<details class="gk-more">
<summary>Parkering, lån och övrigt</summary>
<div class="gk-stack" style="gap:14px">
<div class="gk-field">
<label for="park">Parkering</label>
<div class="gk-input"><input id="park" inputmode="numeric" autocomplete="off" placeholder="0"><span class="unit">kr/mån</span></div>
</div>
<div class="gk-field">
<label for="ranta">Ränta på billån</label>
<div class="gk-input"><input id="ranta" inputmode="numeric" autocomplete="off" placeholder="0"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Bara räntan. Amorteringen betalar av bilen och räknas redan i värdeminskningen.</span>
</div>
<div class="gk-field">
<label for="ovr">Övrigt</label>
<div class="gk-input"><input id="ovr" inputmode="numeric" autocomplete="off" placeholder="0"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Till exempel trängselskatt, vägtullar och biltvätt.</span>
</div>
</div>
</details>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:14px" aria-labelledby="vH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="vH" style="font-size:22px">Värdeminskning – hur mycket tappar bilen?</h2>
<p class="gk-hint" id="vIntro"></p>
</div>
<div class="gk-field">
<label for="alder">Bilens ålder när du köper den</label>
<div class="gk-input"><input id="alder" inputmode="numeric" autocomplete="off" value="{D['ALDER']}"><span class="unit">år</span></div>
<div class="gk-seg" style="--n:3" id="alderq" role="group" aria-label="Bilens ålder vid köp">
{seg([(0, "Ny"), (3, "3 år"), (6, "6 år")], D['ALDER'])}
</div>
</div>
<div id="vRes" aria-live="polite"></div>
<figure style="margin:0">
<figcaption class="gk-hint" style="margin-bottom:8px" id="vCap"></figcaption>
<div id="vChart"></div>
</figure>
<details class="gk-more">
<summary>Visa år för år</summary>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="vTable"></table></div>
</details>
<details class="gk-more" id="hBox">
<summary>Räkna ut procentsatsen från annonspriser</summary>
<div class="gk-stack" style="gap:14px">
<p class="gk-hint">Leta upp samma modell i två åldrar, med ungefär lika långt körda bilar. Då ser du hur mycket modellen har tappat per år.</p>
<div class="gk-field">
<label for="hNy">Pris för den yngre bilen</label>
<div class="gk-input"><input id="hNy" inputmode="numeric" autocomplete="off" placeholder="t.ex. 300 000"><span class="unit">kr</span></div>
</div>
<div class="gk-field">
<label for="hGam">Pris för den äldre bilen</label>
<div class="gk-input"><input id="hGam" inputmode="numeric" autocomplete="off" placeholder="t.ex. 180 000"><span class="unit">kr</span></div>
</div>
<div class="gk-field">
<label for="hAr">Hur många år äldre?</label>
<div class="gk-input"><input id="hAr" inputmode="numeric" autocomplete="off" placeholder="t.ex. 4"><span class="unit">år</span></div>
</div>
<div id="hRes" aria-live="polite"></div>
</div>
</details>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Bilen kostar per månad</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån</span></div>
<p class="gk-hint" id="resSub"></p>
<div id="bar"></div>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="/kalkylatorer/leasingkalkylator"><span>Leasa i stället?<small>Leasingkalkylator – månadsavgift och jämförelse med köp</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/formansbilkalkylator"><span>Bil via jobbet?<small>Förmånsbilkalkylator – vad kostar förmånsbilen netto?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/milersattningskalkylator"><span>Kör du i tjänsten?<small>Milersättning – {K['MILERS']} kr/mil skattefritt 2026</small></span>{CHEV}</a>
<!--GK-PARTNER:bilforsakring:START--><!--GK-PARTNER:bilforsakring:END-->
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknar du ut bilkostnaden per månad</h2>
<p>Lägg ihop allt bilen kostar under ett år och dela med 12. En bilkalkyl har två sorters kostnader:</p>
<ul>
<li><strong>Rörliga</strong> – drivmedel, service och däck. De ökar ju mer du kör.</li>
<li><strong>Fasta</strong> – värdeminskning, försäkring, fordonsskatt, parkering och ränta på billån. Dem betalar du även när bilen står still.</li>
</ul>
<p>Delar du årskostnaden med antalet mil du kör får du kostnaden per mil. Privatägda personbilar körde i snitt <strong>{fmt(K['KOR_PRIVAT'])} mil</strong> 2025 enligt Trafikanalys. Som jämförelse är Skatteverkets skattefria milersättning för egen bil <strong>{K['MILERS']} kr per mil</strong> 2026.</p>

<h2>Hur mycket tappar en bil i värde per år?</h2>
<p>Det finns ingen officiell siffra – det beror på modell, körsträcka, skick och efterfrågan. Kalkylatorn räknar därför med en procentsats som du väljer, och bilen tappar samma andel av sitt värde varje år. Jämför annonspriser för samma modell i olika åldrar och räkna om dem till procent per år i kortet <a href="#vH">Värdeminskning</a>.</p>
<div class="gk-table-wrap"><table class="gk-table">
<thead><tr><th scope="col">Tappar per år</th><th scope="col">Värd efter 1 år</th><th scope="col">3 år</th><th scope="col">5 år</th></tr></thead>
<tbody>{rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Andel av inköpspriset. Räkneexempel – procentsatserna är antaganden, inte statistik.</caption>
</table></div>

<h2>Fordonsskatt: grundbelopp och koldioxidbelopp</h2>
<p>Fordonsskatten för en personbil är ett <strong>grundbelopp på {K['GRUND']} kr</strong> per år plus ett <strong>koldioxidbelopp på {K['CO2_KR']} kr per gram</strong> koldioxid över {K['CO2_GRANS']} g/km. En bensinbil som släpper ut {D['CO2_EX']} g/km betalar alltså {K['GRUND']} + {D['CO2_EX'] - K['CO2_GRANS']} × {K['CO2_KR']} = {fmt(SKATT_EX)} kr per år. Bensin- och dieselbilar som blivit skattepliktiga från 1 juni 2022 betalar ett högre koldioxidbelopp de tre första åren: {K['MALUS_KR1']} kr per gram över {K['MALUS_G1']} g och {K['MALUS_KR2']} kr per gram över {K['MALUS_G2']} g – samma bil betalar då {fmt(SKATT_MALUS)} kr per år. Dieselbilar betalar dessutom tillägg. <strong>En elbil betalar {K['GRUND']} kr per år</strong>, eftersom den inte släpper ut någon koldioxid. Din bils exakta skatt ser du i Transportstyrelsens e-tjänst <a href="{SRC['ts_skulder']}" target="_blank" rel="noopener">Fordonets skulder</a>.</p>

<h2>Vanliga frågor om bilkostnad</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['trafa']}" target="_blank" rel="noopener">Trafikanalys – Körsträckor 2025</a> (17 april 2026) – privatägda personbilar {fmt(K['KOR_PRIVAT'])} mil, alla personbilar {fmt(K['KOR_ALLA'])} mil, elbilar och laddhybrider ungefär {fmt(K['KOR_LADDBAR'])} mil</li>
<li><a href="{SRC['preem']}" target="_blank" rel="noopener">Preem – Drivmedelspriser för företagskunder</a> – listpris bensin 95 {p2(PB)} kr/l och diesel {p2(PD)} kr/l inkl. moms (bensin från 2 oktober, diesel från 1 oktober 2026, kontrollerat {K['PRIS_DATUM']}). Priset på din mack kan skilja.</li>
<li><a href="{SRC['skv']}" target="_blank" rel="noopener">Skatteverket – Belopp och procent 2026</a> – skattefri bilersättning för egen bil {K['MILERS']} kr per mil</li>
<li><a href="{SRC['vsl']}" target="_blank" rel="noopener">Vägtrafikskattelag (2006:227)</a> – grundbelopp {K['GRUND']} kr (2 kap. 8 §), koldioxidbelopp {K['CO2_KR']} kr/g över {K['CO2_GRANS']} g (2 kap. 9 §), högre belopp de tre första åren (2 kap. 9 a §)</li>
<li><a href="{SRC['ts_storlek']}" target="_blank" rel="noopener">Transportstyrelsen – Skattens storlek</a> och <a href="{SRC['ts_skatt']}" target="_blank" rel="noopener">Fordonsskatt</a> – hur skatten räknas och var du ser din bils skatt</li>
<li>Värdeminskningen räknas med samma procentsats varje år. Procentsatsen och exemplen för försäkring, service och däck är antaganden som du ändrar.</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/drivmedelskalkylator"><span>Drivmedelskalkylator<small>Vad kostar bilresan i bensin, diesel eller el?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/lanekalkylator"><span>Lånekalkylator<small>Månadskostnad och ränta för ett billån</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/privatleasing-eller-kopa-bil-2026"><span>Guide: privatleasing eller köpa bil<small>Det du ska ha koll på innan du bestämmer dig</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-bil" type="application/json">{json.dumps({"K": K, "D": D, "SKATT_EX": SKATT_EX})}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Vad kostar bilen per månad? Bilkostnad och värdeminskning", jsonld=ld)
            + S.header() + body + S.footer("Bilkostnaden är en uppskattning som bygger på de belopp du fyller i."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var CFG = JSON.parse(document.getElementById('gk-bil').textContent), C = CFG.K, D = CFG.D;
  var $ = function (id) { return document.getElementById(id); };
  var kr10 = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var d2 = function (v) { return GK.fmt(v, 2); };
  var pc = function (v) { return GK.fmt(v, 0) + ' %'; };
  var st = { typ: 'bensin' };

  /* Modell – samma som scripts/build_bilkostnad.py */
  function varde(pris, proc, ar) {
    var vals = [];
    for (var k = 0; k <= ar; k++) vals.push(pris * Math.pow(1 - proc / 100, k));
    var tapp = pris - vals[ar];
    return { vals: vals, slut: vals[ar], tapp: tapp, perAr: tapp / ar, perMan: tapp / ar / 12, forsta: pris * proc / 100, andel: tapp / pris * 100 };
  }
  function kostnad(pris, proc, ar, mil, forbr, bpris, fors, skatt, serv, park, ranta, ovr) {
    var v = varde(pris, proc, ar);
    var p = { varde: v.perAr, drivmedel: mil * forbr * bpris, forsakring: fors * 12, skatt: skatt, service: serv,
      parkering: (park || 0) * 12, ranta: (ranta || 0) * 12, ovrigt: (ovr || 0) * 12 };
    var tot = 0; for (var k in p) tot += p[k];
    return { poster: p, ar: tot, man: tot / 12, permil: mil > 0 ? tot / mil : null, v: v };
  }
  function procentFranPriser(yngre, aldre, ar) { return (1 - Math.pow(aldre / yngre, 1 / ar)) * 100; }
  window.GKBil = { varde: varde, kostnad: kostnad, procentFranPriser: procentFranPriser };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x.getAttribute('data-v') === String(v) ? 'true' : 'false'); }); }
  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }
  function arTxt(n) { return n === 1 ? '1 år' : n + ' år'; }

  /* Drivmedel: byt enheter, exempelvärden och fordonsskatt */
  function setTyp(t) {
    var prev = st.typ, el = t === 'el', f = GK.parse($('forbr').value), s = GK.parse($('skatt').value);
    st.typ = t;
    if ((prev === 'el') !== el || !isFinite(f) || f === D.FORBR[prev]) $('forbr').value = GK.fmt(D.FORBR[t], 1);
    $('bpris').value = el ? '' : d2(C.PRIS[t]);
    $('bpris').placeholder = el ? 'ditt elpris' : '';
    $('forbrUnit').textContent = el ? 'kWh/mil' : 'l/mil';
    $('bprisUnit').textContent = el ? 'kr/kWh' : 'kr/l';
    var skattDefault = !isFinite(s) || s === CFG.SKATT_EX || s === C.GRUND;
    if (skattDefault) $('skatt').value = el ? GK.fmt(C.GRUND, 0) : (t === 'bensin' ? GK.fmt(CFG.SKATT_EX, 0) : '');
    $('skatt').placeholder = t === 'diesel' ? 'din bils skatt' : '';
    $('dmHint').innerHTML = el
      ? 'Förbrukningen är ett exempel – fyll i din bils värde. Elpris: ditt pris per kWh med elnät, skatt och moms (<a href="/kalkylatorer/elkostnadskalkylator">räkna ut det</a>).'
      : 'Förbrukningen är ett exempel – fyll i din bils värde (7 l/100 km = 0,7 l/mil). Priset är Preems listpris för ' + (t === 'bensin' ? 'bensin 95' : 'diesel') + ' ' + C.PRIS_DATUM + '.';
    $('skattHint').innerHTML = el ? 'En elbil betalar bara grundbeloppet, ' + C.GRUND + ' kr per år.'
      : (t === 'bensin' ? 'Exempel: bensinbil som släpper ut ' + D.CO2_EX + ' g koldioxid per km och är äldre än tre år. '
        : 'Dieselbilar betalar dessutom tillägg. ') + 'Din bils skatt ser du hos <a href="https://www.transportstyrelsen.se/sv/vagtrafik/fordon/skatter-och-avgifter/fordonsskatt/" target="_blank" rel="noopener">Transportstyrelsen</a>.';
  }

  seg('typ', setTyp);
  seg('arq', function (v) { $('ar').value = v; });
  seg('milq', function (v) { $('mil').value = GK.fmt(+v, 0); });
  seg('alderq', function (v) { $('alder').value = v; });
  ['pris', 'proc', 'ar', 'mil', 'forbr', 'bpris', 'fors', 'skatt', 'serv', 'park', 'ranta', 'ovr', 'alder'].forEach(function (id) { $(id).addEventListener('input', calc); });
  $('ar').addEventListener('input', function () { press('arq', GK.parse($('ar').value)); });
  $('mil').addEventListener('input', function () { press('milq', GK.parse($('mil').value)); });
  $('alder').addEventListener('input', function () { press('alderq', GK.parse($('alder').value)); });
  ['hNy', 'hGam', 'hAr'].forEach(function (id) { $(id).addEventListener('input', helper); });
  ['pris', 'mil', 'fors', 'skatt', 'serv', 'park', 'ranta', 'ovr', 'hNy', 'hGam'].forEach(function (id) { GK.groupInput($(id)); });

  function clear(msg) {
    $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'verdict', 'how', 'bar'].forEach(function (id) { $(id).innerHTML = ''; });
  }
  function clearV(msg) {
    $('vIntro').textContent = msg;
    ['vRes', 'vChart', 'vCap', 'vTable'].forEach(function (id) { $(id).innerHTML = ''; });
  }

  function inputs() {
    var ar = val('ar');
    return { pris: val('pris'), proc: val('proc'), ar: ar ? Math.round(ar) : null, alder: Math.round(val('alder') || 0) };
  }

  function calc() {
    var I = inputs();
    var okV = I.pris && I.pris >= 1000 && I.proc != null && I.proc < 100 && I.ar && I.ar >= 1 && I.ar <= 30;
    if (okV) vcard(I); else clearV(!I.pris || I.pris < 1000 ? 'Fyll i bilens pris i formuläret.' : (I.proc == null || I.proc >= 100 ? 'Fyll i värdeminskningen i procent per år, till exempel 15.' : 'Fyll i hur många år du behåller bilen (1–30).'));

    var mil = val('mil'), f = val('forbr'), bp = val('bpris'), el = st.typ === 'el';
    var fors = val('fors') || 0, skatt = val('skatt') || 0, serv = val('serv') || 0;
    var park = val('park') || 0, ranta = val('ranta') || 0, ovr = val('ovr') || 0;
    if (!I.pris || I.pris < 1000) return clear('Fyll i bilens pris.');
    if (I.proc == null || I.proc >= 100) return clear('Fyll i värdeminskningen i procent per år.');
    if (!okV) return clear('Fyll i hur många år du behåller bilen (1–30).');
    if (mil == null) return clear('Fyll i hur många mil du kör per år.');
    if (f == null) return clear('Fyll i bilens förbrukning per mil.');
    if (!bp) return clear(el ? 'Fyll i ditt elpris per kWh.' : 'Fyll i priset per liter.');

    var r = kostnad(I.pris, I.proc, I.ar, mil, f, bp, fors, skatt, serv, park, ranta, ovr), P = r.poster;
    $('resBig').textContent = GK.fmt(Math.round(r.man / 10) * 10, 0);
    $('resSub').textContent = (r.permil != null ? GK.fmt(r.permil, 0) + ' kr per mil · ' : '') + kr10(r.ar) + ' per år · ' + GK.fmt(mil, 0) + ' mil per år, bilen i ' + arTxt(I.ar) + '.';

    var fast = P.forsakring + P.skatt, ovrigt = P.service + P.parkering + P.ranta + P.ovrigt;
    $('tiles').innerHTML = tile('Värdeminskning', kr10(P.varde / 12) + '/mån', r.ar > 0 ? pc(P.varde / r.ar * 100) + ' av kostnaden' : '') +
      tile('Drivmedel', kr10(P.drivmedel / 12) + '/mån', mil > 0 ? d2(f * bp) + ' kr per mil' : '') +
      tile('Försäkring och skatt', kr10(fast / 12) + '/mån', GK.fmt(P.forsakring, 0) + ' + ' + GK.fmt(P.skatt, 0) + ' kr per år') +
      tile('Service, däck och övrigt', kr10(ovrigt / 12) + '/mån', P.parkering + P.ranta + P.ovrigt > 0 ? 'Inkl. parkering, ränta och övrigt' : 'Service och däck');

    var parts = [['Värdeminskning', P.varde, 'var(--gk-accent)'], ['Drivmedel', P.drivmedel, 'var(--gk-ink-2)'], ['Försäkring och skatt', fast, 'var(--gk-warn-ink)'], ['Service, däck och övrigt', ovrigt, 'var(--gk-muted)']];
    $('bar').innerHTML = r.ar > 0 ? '<div role="img" aria-label="Fördelning: ' + parts.map(function (x) { return x[0] + ' ' + pc(x[1] / r.ar * 100); }).join(', ') + '" style="display:flex;height:14px;border-radius:7px;overflow:hidden;background:var(--gk-chip)">' +
      parts.map(function (x) { return x[1] > 0 ? '<span style="width:' + (x[1] / r.ar * 100).toFixed(2) + '%;background:' + x[2] + '"></span>' : ''; }).join('') + '</div>' +
      '<p class="gk-hint" style="margin:6px 0 0;display:flex;flex-wrap:wrap;gap:4px 12px">' + parts.map(function (x) { return '<span style="display:inline-flex;align-items:center;gap:5px"><i style="width:10px;height:10px;border-radius:3px;background:' + x[2] + ';display:inline-block"></i>' + x[0] + '</span>'; }).join('') + '</p>' : '';

    var v = '';
    if (r.permil != null) {
      var diff = r.permil - C.MILERS;
      v += verdict('info', 'Bilen kostar ' + GK.fmt(r.permil, 0) + ' kr per mil – ' + (diff >= 0 ? GK.fmt(diff, 0) + ' kr mer' : GK.fmt(-diff, 0) + ' kr mindre') + ' än milersättningen',
        'Skatteverkets skattefria milersättning för egen bil är ' + C.MILERS + ' kr per mil 2026. Det är ett jämförelsevärde – får du milersättning i jobbet täcker den ' + (diff > 0 ? 'inte hela din kostnad per mil.' : 'hela din kostnad per mil.'));
    }
    if (st.typ === 'diesel' && !val('skatt')) {
      v += verdict('warn', 'Fyll i fordonsskatten', 'Dieselbilar betalar koldioxidbelopp och tillägg. Din bils skatt ser du hos Transportstyrelsen.');
    }
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p><strong>Värdeminskning:</strong> ' + kr10(I.pris) + ' × (1 − ' + GK.fmt(I.proc, 1).replace(/,0$/, '') + ' %)<sup>' + I.ar + '</sup> = ' + kr10(r.v.slut) + ' efter ' + arTxt(I.ar) + '. Bilen tappar ' + kr10(r.v.tapp) + ', delat på ' + arTxt(I.ar) + ' = ' + kr10(P.varde) + ' per år.</p>' +
      '<p><strong>Drivmedel:</strong> ' + GK.fmt(mil, 0) + ' mil × ' + d2(f) + (el ? ' kWh/mil × ' + d2(bp) + ' kr/kWh' : ' l/mil × ' + d2(bp) + ' kr/l') + ' = ' + kr10(P.drivmedel) + ' per år.</p>' +
      '<p><strong>Övrigt per år:</strong> försäkring ' + kr10(P.forsakring) + ', fordonsskatt ' + kr10(P.skatt) + ', service och däck ' + kr10(P.service) +
      (P.parkering ? ', parkering ' + kr10(P.parkering) : '') + (P.ranta ? ', ränta ' + kr10(P.ranta) : '') + (P.ovrigt ? ', övrigt ' + kr10(P.ovrigt) : '') + '.</p>' +
      '<p>Summa ' + kr10(r.ar) + ' per år / 12 = ' + kr10(r.man) + ' per månad' + (r.permil != null ? ', och / ' + GK.fmt(mil, 0) + ' mil = ' + GK.fmt(r.permil, 1) + ' kr per mil' : '') + '. Amorteringen på ett billån räknas inte – den betalar av bilen, som redan finns med som värdeminskning.</p>';
  }

  function vcard(I) {
    var v = varde(I.pris, I.proc, I.ar), slutAlder = I.alder + I.ar;
    $('vIntro').textContent = 'Räknat på priset ' + kr10(I.pris) + ', ' + GK.fmt(I.proc, 1).replace(/,0$/, '') + ' % per år och ' + arTxt(I.ar) + ' från formuläret.';
    $('vRes').innerHTML = '<p style="margin:0;font-size:16px;line-height:1.5"><strong>Efter ' + arTxt(I.ar) + ' är bilen värd ca ' + kr10(v.slut) + '</strong> – den har tappat ' + kr10(v.tapp) + ', ' + pc(v.andel) + ' av priset.</p>' +
      '<div class="gk-tiles" style="margin-top:10px">' + tile('Första året', kr10(v.forsta), GK.fmt(I.proc, 1).replace(/,0$/, '') + ' % av priset') +
      tile('Snitt per år', kr10(v.perAr), kr10(v.perMan) + ' per månad') +
      tile('Tappar totalt', kr10(v.tapp), 'På ' + arTxt(I.ar)) +
      tile('Värd när du säljer', kr10(v.slut), 'Bilen är då ' + arTxt(slutAlder)) + '</div>';

    var W = Math.max(280, Math.min(560, $('vChart').clientWidth || 480)), H = 170, L = 6, R = 6, T = 22, B = 24;
    var n = I.ar + 1, gap = n > 12 ? 2 : 6, bw = (W - L - R - gap * (n - 1)) / n, y = function (x) { return T + (1 - x / I.pris) * (H - T - B); };
    var s = '';
    v.vals.forEach(function (x, k) {
      var x0 = L + k * (bw + gap);
      s += '<rect x="' + x0.toFixed(1) + '" y="' + y(x).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + (H - B - y(x)).toFixed(1) + '" rx="3" fill="' + (k === 0 ? 'var(--gk-ink-2)' : 'var(--gk-accent)') + '"/>';
      if (n <= 12 || k % 2 === 0 || k === n - 1) s += '<text x="' + (x0 + bw / 2).toFixed(1) + '" y="' + (H - 7) + '" text-anchor="middle" font-size="11" fill="var(--gk-muted)">' + (k === 0 ? 'Köp' : k) + '</text>';
      if (k === 0 || k === n - 1) s += '<text x="' + (k === 0 ? x0 : x0 + bw).toFixed(1) + '" y="' + (y(x) - 6).toFixed(1) + '" text-anchor="' + (k === 0 ? 'start' : 'end') + '" font-size="11" font-weight="700" fill="var(--gk-ink)">' + GK.fmt(Math.round(x / 1000), 0) + ' tkr</text>';
    });
    $('vCap').textContent = 'Bilens värde vid köpet och efter varje år du äger den.';
    $('vChart').innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Bilens värde: ' + kr10(I.pris) + ' vid köp, ' + kr10(v.slut) + ' efter ' + arTxt(I.ar) + '" style="display:block;font-family:inherit">' + s + '</svg>';

    var rows = '';
    for (var k = 1; k <= I.ar; k++) {
      rows += '<tr><td>' + k + '<small class="gk-hint" style="display:block">bilen ' + (I.alder + k) + ' år</small></td><td>' + GK.fmt(Math.round(v.vals[k] / 10) * 10, 0) + '</td><td>' + GK.fmt(Math.round((v.vals[k - 1] - v.vals[k]) / 10) * 10, 0) + '</td><td>' + GK.fmt((1 - v.vals[k] / I.pris) * 100, 0) + ' %</td></tr>';
    }
    $('vTable').innerHTML = '<thead><tr><th scope="col">År</th><th scope="col">Värde</th><th scope="col">Tappar</th><th scope="col">Totalt</th></tr></thead><tbody>' + rows +
      '</tbody><caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor. Tappar = värdeminskningen det året. Totalt = andel av priset som bilen har tappat.</caption>';
  }

  function helper() {
    var a = val('hNy'), b = val('hGam'), n = val('hAr');
    if (!a || !b || !n || n <= 0) { $('hRes').innerHTML = ''; return; }
    if (b >= a) { $('hRes').innerHTML = verdict('info', 'Den äldre bilen är inte billigare', 'Fyll i priset för den yngre bilen i första rutan och den äldre i andra.'); return; }
    var p = procentFranPriser(a, b, n), pr = Math.round(p * 10) / 10;
    $('hRes').innerHTML = '<div class="gk-tiles">' + tile('Tappar per år', GK.fmt(p, 1) + ' %', 'Samma andel varje år') + tile('Tappat totalt', kr10(a - b), 'På ' + GK.fmt(n, 0) + ' år') + '</div>' +
      '<button type="button" class="gk-btn" id="hUse" style="margin-top:12px">Använd ' + GK.fmt(pr, 1) + ' % i kalkylatorn</button>';
    $('hUse').addEventListener('click', function () {
      $('proc').value = GK.fmt(pr, 1); calc();
      var res = document.querySelector('.gk-result'); if (res && res.scrollIntoView) res.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  setTyp('bensin');
  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "bilkostnadsraknare.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    title = "Värdeminskning bil & bilkostnad per månad | GratisKalkyl"
    desc = ("Vad kostar bilen per månad och per mil? Räkna ut värdeminskningen per år, drivmedel, försäkring, "
            "skatt och service. Elbilar betalar 360 kr i fordonsskatt.")
    print("Titel", len(title), "tecken; description", len(desc), "tecken")
    print("Fordonsskatt 120 g:", SKATT_EX, "kr; med malus:", SKATT_MALUS, "kr; elbil:", fordonsskatt(0), "kr")
    for c in CASES:
        x = kostnad(*c)
        print(c, "->", "mån", kr10(x["man"]), "år", kr10(x["ar"]), "per mil", fmt(x["permil"], 0) if x["permil"] else "-",
              "värde slut", kr10(x["v"]["slut"]), "tapp", kr10(x["v"]["tapp"]), "per år", kr10(x["v"]["per_ar"]))
    for c in [(250000, 150000, 4), (300000, 180000, 4), (200000, 120000, 3)]:
        print("procent", c, "->", fmt(procent_fran_priser(*c), 1), "%")


# Räknefall (pris, proc, år, mil, förbrukning, pris/enhet, försäkring/mån, skatt/år, service/år, parkering, ränta, övrigt)
CASES = [
    (300000, 15, 5, 1155, 0.7, PB, 500, SKATT_EX, 6000, 0, 0, 0),
    (450000, 12, 3, 2000, 0.6, PD, 700, 2500, 8000, 500, 900, 200),
    (400000, 18, 8, 1700, 1.8, 1.9, 600, 360, 4000, 0, 0, 0),
    (80000, 10, 4, 800, 0.65, PB, 350, 1500, 5000, 0, 0, 0),
    (180000, 7.5, 10, 1243, 0.55, 17.2, 420, 900, 7000, 250, 0, 150),
]

if __name__ == "__main__":
    main()
