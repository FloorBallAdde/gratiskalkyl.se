#!/usr/bin/env python3
"""Bygger artiklar/csn-2026-belopp-och-regler.html (guide) i den nya verktygsmallen.

Alla belopp är CSN:s egna (verifierade på csn.se 1 oktober 2026, se SRC):
  - Studiemedel per vecka 2026: heltid 1 030 + 2 368, 75 % 775 + 1 776, 50 % 509 + 1 190 (bidrag + lån).
    Högre bidrag (heltid): 2 279 + 1 119. Studiemedel betalas vanligtvis ut för fyra veckor i taget.
  - Tilläggsbidrag per vecka 2026 för 1–5 barn vid 100/75/50 %. Tilläggslån 1 172 kr/vecka (heltid).
  - Fribelopp 2026 vid 20 veckor: 114 676 (100 %), 143 346 (75 %), 172 017 (50 %); minskning 61 % av
    överskjutande inkomst (heltid med bidrag och lån).
  - 2027 (CSN 25 sep 2026): 13 684 kr / 4 veckor, bidraget +28 kr och lånet +64 kr, tilläggslån 4 720,
    tilläggsbidrag 784 / 1 284 och därefter +260 kr per ytterligare barn, fribelopp 115 451, PBB 59 600.
  - Skatt: studiestöd enligt studiestödslagen ska inte tas upp (inkomstskattelagen 11 kap. 34 §).

    python3 scripts/build_csn_guide.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/artiklar/csn-2026-belopp-och-regler"
UPDATED = "1 oktober 2026"

# Konstanter – byt vid årsskiftet (kronor per vecka om inget annat anges)
K = {
    "AR": 2026,
    "V": {  # studiemedel per vecka: bidrag, lån
        "100": {"bidrag": 1030, "lan": 2368},
        "75": {"bidrag": 775, "lan": 1776},
        "50": {"bidrag": 509, "lan": 1190},
    },
    "HOGRE": {"bidrag": 2279, "lan": 1119},  # högre bidrag, heltid
    "TB": {  # tilläggsbidrag per vecka för 1–5 barn
        "100": [195, 319, 384, 449, 514],
        "75": [148, 242, 289, 336, 383],
        "50": [94, 159, 194, 229, 264],
    },
    "TL": {"100": 1172, "75": 882, "50": 586},  # tilläggslån per vecka
    "FRI": {"100": 114676, "75": 143346, "50": 172017},  # fribelopp per kalenderhalvår, 20 veckor
    "FRI_RED": 0.61,
    "RANTA": 2.135,
    "MIN_AR": 8880,  # minsta årsbelopp vid återbetalning 2026
    "V4": 4,  # utbetalning vanligtvis för fyra veckor i taget
    # 2027 enligt CSN 25 september 2026 (per fyra veckor, heltid)
    "N": {"AR": 2027, "TOT4": 13684, "BIDRAG_PLUS": 28, "LAN_PLUS": 64, "TL4": 4720,
          "TB4_1": 784, "TB4_2": 1284, "TB4_STEG": 260, "FRI": 115451, "PBB": 59600},
}
N = K["N"]
N["BIDRAG4"] = K["V"]["100"]["bidrag"] * 4 + N["BIDRAG_PLUS"]
N["LAN4"] = K["V"]["100"]["lan"] * 4 + N["LAN_PLUS"]
N["TB4"] = [N["TB4_1"], N["TB4_2"]] + [N["TB4_2"] + N["TB4_STEG"] * i for i in (1, 2, 3)]

SRC = {
    "studiemedel": "https://www.csn.se/bidrag-och-lan/studiemedel.html",
    "belopp": "https://www.csn.se/fragor-och-svar/hur-mycket-pengar-kan-jag-fa-eller-lana.html",
    "hogre": "https://www.csn.se/bidrag-och-lan/tillagg-till-studiestodet/for-studier-med-studiemedel/hogre-bidraget-for-vissa-studier.html",
    "tb": "https://www.csn.se/bidrag-och-lan/tillagg-till-studiestodet/for-studier-med-studiemedel/tillaggsbidrag.html",
    "tl": "https://www.csn.se/bidrag-och-lan/tillagg-till-studiestodet/for-studier-med-studiemedel/tillaggslan.html",
    "fri": "https://www.csn.se/fragor-och-svar/hur-stor-inkomst-far-jag-ha-nar-jag-studerar-med-studiemedel/inkomst-och-fribelopp.html",
    "n2027": "https://www.csn.se/om-csn/aktuellt/nyhetsflode/2026-09-25-studiemedlet-och-fribeloppet-hojs-till-2027.html",
    "betala": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan.html",
    "ansok": "https://www.csn.se/bidrag-och-lan/studiemedel/sa-ansoker-du-om-studiemedel.html",
    "skatt": "https://xn--svenskfrfattningssamling-roc.se/sites/default/files/sfs/2022-06/SFS2022-860.pdf",
}

# Kontroll mot CSN:s publicerade fyraveckorsbelopp
assert sum(K["V"]["100"].values()) * 4 == 13592
assert sum(K["V"]["75"].values()) * 4 == 10204 and sum(K["V"]["50"].values()) * 4 == 6796
assert K["HOGRE"]["bidrag"] * 4 == 9116 and K["HOGRE"]["lan"] * 4 == 4476
assert [x * 4 for x in K["TB"]["100"]] == [780, 1276, 1536, 1796, 2056]
assert [x * 4 for x in K["TB"]["75"]] == [592, 968, 1156, 1344, 1532]
assert [x * 4 for x in K["TB"]["50"]] == [376, 636, 776, 916, 1056]
assert K["TL"]["100"] * 4 == 4688
assert N["BIDRAG4"] + N["LAN4"] == N["TOT4"]


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def csn(takt, lan=True, barn=0):
    """Python-referens – samma som sidans JS. takt = "100", "75" eller "50"; barn 0–5."""
    v = K["V"][takt]
    b = v["bidrag"]
    l_ = v["lan"] if lan else 0
    t = K["TB"][takt][barn - 1] if barn > 0 else 0
    vecka = b + l_ + t
    return {"bidrag4": b * 4, "lan4": l_ * 4, "tb4": t * 4, "vecka": vecka, "tot4": vecka * 4,
            "bort4": (v["lan"] - l_) * 4, "fri": K["FRI"][takt]}


FULL4 = csn("100")["tot4"]
FRI_MAN = K["FRI"]["100"] / 6

FAQ = [
    ("Hur mycket är studiebidraget 2026?",
     f"På heltid är bidraget {fmt(K['V']['100']['bidrag'])} kr i veckan, {fmt(K['V']['100']['bidrag'] * 4)} kr per fyra veckor. "
     f"På 75 procent är det {fmt(K['V']['75']['bidrag'])} kr och på 50 procent {fmt(K['V']['50']['bidrag'])} kr i veckan. "
     "Bidraget är den del av studiemedlet som du inte betalar tillbaka."),
    ("Vad är fullt CSN 2026?",
     f"Fullt studiemedel är bidrag plus hela lånet på heltid: {fmt(sum(K['V']['100'].values()))} kr i veckan eller "
     f"{fmt(FULL4)} kr per fyra veckor 2026. Har du barn kan du få tilläggsbidrag ovanpå det, och från 25 år kan du "
     "i vissa fall få tilläggslån."),
    ("Hur mycket får man i CSN per månad?",
     f"CSN betalar vanligtvis ut studiemedlet för fyra veckor i taget, den 25:e varje månad du studerar. Med fullt "
     f"studiemedel blir det {fmt(FULL4)} kr per utbetalning, varav {fmt(K['V']['100']['bidrag'] * 4)} kr är bidrag. "
     f"Två barn ger {fmt(K['TB']['100'][1] * 4)} kr till i tilläggsbidrag."),
    ("Är CSN:s tilläggsbidrag skattefritt?",
     "Ja. Studiestöd enligt studiestödslagen ska inte tas upp till beskattning enligt inkomstskattelagen (11 kap. 34 §). "
     "Det gäller både bidraget, lånet och tilläggsbidraget för barn. Tilläggsbidraget påverkar inte heller bostadsbidraget."),
    ("Hur mycket är tilläggsbidraget för 2 barn 2026?",
     f"{K['TB']['100'][1]} kr per vecka på heltid, alltså {fmt(K['TB']['100'][1] * 4)} kr per fyra veckor. På 75 procent får du "
     f"{fmt(K['TB']['75'][1] * 4)} kr och på 50 procent {fmt(K['TB']['50'][1] * 4)} kr per fyra veckor. 2027 blir det "
     f"{fmt(N['TB4_2'])} kr per fyra veckor på heltid."),
    ("Höjs CSN 2027?",
     f"Ja. Från 1 januari 2027 ger fullt studiemedel {fmt(N['TOT4'])} kr per fyra veckor, {N['TOT4'] - FULL4} kr mer än i dag: "
     f"bidraget höjs med {N['BIDRAG_PLUS']} kr och lånet med {N['LAN_PLUS']} kr. Fribeloppet blir {fmt(N['FRI'])} kr per halvår. "
     f"Höjningen följer prisbasbeloppet, som blir {fmt(N['PBB'])} kr."),
    ("Vad är fribeloppet för CSN 2026?",
     f"{fmt(K['FRI']['100'])} kr per kalenderhalvår om du studerar heltid i 20 veckor. Studerar du färre veckor eller på deltid "
     "är gränsen högre. Alla skattepliktiga inkomster räknas, till exempel lön, a-kassa och föräldrapenning, men inte "
     "bostadsbidrag eller barnbidrag."),
]

CHEV = S.ICON_CHEV
A = 'target="_blank" rel="noopener"'


def cell(v4, v1):
    return f"<td><strong>{fmt(v4)}</strong><small>{fmt(v1)}/v</small></td>"


def page():
    title = "CSN 2026: Studiebidrag 4 120 kr, lån 9 472 kr | GratisKalkyl"
    desc = (f"Fullt CSN 2026 är {fmt(FULL4)} kr per 4 veckor: studiebidrag 4 120 kr och lån 9 472 kr. "
            "Deltid, tilläggsbidrag för barn, fribelopp och beloppen 2027.")
    h1 = "Hur mycket är CSN 2026? Studiebidrag och lån"
    crumbs = [("Hem", "/"), ("Guider", "/artiklar/"), ("CSN 2026", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": h1, "url": S.SITE + PATH,
         "inLanguage": "sv", "description": desc, "dateModified": "2026-10-01",
         "author": {"@type": "Organization", "name": "GratisKalkyl.se"},
         "publisher": {"@type": "Organization", "name": "GratisKalkyl.se"}},
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "CSN-räknare 2026 – vad får du per månad?",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv",
         "description": desc, "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guider", "item": S.SITE + "/artiklar/"},
            {"@type": "ListItem", "position": 3, "name": "CSN 2026", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    V = K["V"]
    rows = []
    for takt, namn in (("100", "Heltid 100 %"), ("75", "Deltid 75 %"), ("50", "Deltid 50 %")):
        b, l_ = V[takt]["bidrag"], V[takt]["lan"]
        rows.append(f"<tr><th scope=\"row\">{namn}</th>{cell(b * 4, b)}{cell(l_ * 4, l_)}{cell((b + l_) * 4, b + l_)}</tr>")
    hb, hl = K["HOGRE"]["bidrag"], K["HOGRE"]["lan"]
    rows.append(f"<tr><th scope=\"row\">Högre bidrag<small>heltid</small></th>{cell(hb * 4, hb)}{cell(hl * 4, hl)}{cell((hb + hl) * 4, hb + hl)}</tr>")
    main_rows = "".join(rows)

    tb_rows = "".join(
        f"<tr><th scope=\"row\">{i + 1} barn</th><td>{K['TB']['100'][i]}</td><td><strong>{fmt(K['TB']['100'][i] * 4)}</strong></td>"
        f"<td>{fmt(K['TB']['75'][i] * 4)}</td><td>{fmt(K['TB']['50'][i] * 4)}</td></tr>" for i in range(5))

    n_rows = "".join(
        f"<tr><th scope=\"row\">{n}</th><td>{fmt(a)}</td><td><strong>{fmt(b)}</strong></td></tr>" for n, a, b in [
            ("Bidrag", V["100"]["bidrag"] * 4, N["BIDRAG4"]),
            ("Lån", V["100"]["lan"] * 4, N["LAN4"]),
            ("Totalt, fullt studiemedel", FULL4, N["TOT4"]),
            ("Tilläggsbidrag, 1 barn", K["TB"]["100"][0] * 4, N["TB4_1"]),
            ("Tilläggsbidrag, 2 barn", K["TB"]["100"][1] * 4, N["TB4_2"]),
            ("Tilläggslån", K["TL"]["100"] * 4, N["TL4"]),
            ("Fribelopp per halvår (20 veckor)", K["FRI"]["100"], N["FRI"]),
        ])

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Guide · CSN 2026</div>
<h1>{h1}</h1>
<p class="gk-lead">Fullt studiemedel 2026 är <strong>{fmt(FULL4)} kr per fyra veckor</strong>: {fmt(V['100']['bidrag'] * 4)} kr i bidrag och {fmt(V['100']['lan'] * 4)} kr i lån.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Belopp för 2026 och 2027 · Källa: <a href="{SRC['belopp']}" {A}>CSN</a></p>
</div>

<section class="gk-card gk-stack csn-top" aria-labelledby="beloppH">
<h2 id="beloppH" style="font-size:22px">CSN 2026 per 4 veckor och per vecka</h2>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight csn-t">
<caption>Kronor 2026. Fet siffra = per 4 veckor, liten = per vecka (/v).</caption>
<thead><tr><th scope="col">Studietakt</th><th scope="col">Bidrag</th><th scope="col">Lån</th><th scope="col">Totalt</th></tr></thead>
<tbody>{main_rows}</tbody>
</table></div>
<p class="gk-hint">Bidraget betalar du inte tillbaka, lånet gör du. Du kan välja att låna mindre eller inte alls. <a href="#hogre">Högre bidrag</a> gäller vissa studier på grundskole- och gymnasienivå.</p>
</section>

<h2 class="csn-calc-h">Vad får du per månad?</h2>
<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="csnform" novalidate onsubmit="return false">
<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur mycket studerar du?</legend>
<div class="gk-seg" style="--n:3" id="takt" role="group" aria-label="Studietakt">
<button type="button" data-v="100" aria-pressed="true">100 %<small>heltid</small></button>
<button type="button" data-v="75" aria-pressed="false">75 %<small>deltid</small></button>
<button type="button" data-v="50" aria-pressed="false">50 %<small>halvtid</small></button>
</div>
</fieldset>
<fieldset class="gk-fieldset">
<legend class="gk-legend">Tar du lånet?</legend>
<div class="gk-seg" style="--n:2" id="lan" role="group" aria-label="Lån">
<button type="button" data-v="1" aria-pressed="true">Bidrag + lån</button>
<button type="button" data-v="0" aria-pressed="false">Bara bidrag</button>
</div>
</fieldset>
<fieldset class="gk-fieldset">
<legend class="gk-legend">Barn du har vårdnad om</legend>
<div class="gk-seg" style="--n:6" id="barn" role="group" aria-label="Antal barn">
<button type="button" data-v="0" aria-pressed="true">0</button>
<button type="button" data-v="1" aria-pressed="false">1</button>
<button type="button" data-v="2" aria-pressed="false">2</button>
<button type="button" data-v="3" aria-pressed="false">3</button>
<button type="button" data-v="4" aria-pressed="false">4</button>
<button type="button" data-v="5" aria-pressed="false">5</button>
</div>
<span class="gk-hint">Ger tilläggsbidrag. CSN:s tabell går upp till 5 barn.</span>
</fieldset>
</form>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Ditt studiemedel per 4 veckor</div>
<div class="gk-big"><strong id="resBig">{fmt(FULL4)}</strong><span>kr per 4 veckor</span></div>
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
<a class="gk-linkcard" href="/kalkylatorer/csn-kalkylator"><span>Vad kostar lånet att betala tillbaka?<small>CSN-kalkylator – årsbelopp och kostnad per månad</small></span>{CHEV}</a>
<a class="gk-linkcard" href="{SRC['ansok']}" {A}><span>Ansök om studiemedel<small>CSN – Mina sidor</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Gör en studentbudget<small>Hushållsbudget – få pengarna att räcka</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Hur mycket är studiebidraget 2026?</h2>
<p>Bidraget är <strong>{fmt(V['100']['bidrag'])} kr i veckan</strong>, {fmt(V['100']['bidrag'] * 4)} kr per fyra veckor på heltid. Det är ungefär 30 % av studiemedlet, resten är lån. CSN betalar vanligtvis ut fyra veckor i taget, den 25:e varje månad du studerar.</p>
<p id="hogre"><strong>Högre bidrag:</strong> läser du på grundskole- eller gymnasienivå, till exempel på komvux eller folkhögskola, kan du i vissa fall få {fmt(hb)} kr i veckan i bidrag. Totalbeloppet är detsamma, men lånet blir mindre. Det högre bidraget kräver bland annat att du är minst 25 år, eller 20–24 år och arbetslös utan slutbetyg.</p>

<h2>Tilläggsbidrag för barn 2026</h2>
<p>Är du vårdnadshavare kan du få tilläggsbidrag ovanpå studiemedlet. Det är <strong>skattefritt</strong>, betalas inte tillbaka och påverkar inte bostadsbidraget. Du kan få det till och med det kalenderhalvår barnet fyller 18 år. Studerar båda vårdnadshavarna kan bara en av er få det samtidigt.</p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight">
<caption>Tilläggsbidrag 2026 i kronor. Heltid per vecka och per 4 veckor, deltid per 4 veckor.</caption>
<thead><tr><th scope="col">Barn</th><th scope="col">Vecka</th><th scope="col">4 v</th><th scope="col">75 %</th><th scope="col">50 %</th></tr></thead>
<tbody>{tb_rows}</tbody>
</table></div>

<h2>CSN höjs 2027</h2>
<p>CSN har publicerat beloppen för 2027. Prisbasbeloppet höjs till {fmt(N['PBB'])} kr, och därför ger fullt studiemedel <strong>{fmt(N['TOT4'])} kr per fyra veckor</strong> från 1 januari 2027.</p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight">
<caption>Kronor per 4 veckor på heltid, om inget annat anges.</caption>
<thead><tr><th scope="col"></th><th scope="col">2026</th><th scope="col">2027</th></tr></thead>
<tbody>{n_rows}</tbody>
</table></div>
<p>Tilläggslån kan du få om du fyller minst 25 år och hade en viss inkomst före studierna.</p>

<h2>Fribelopp 2026 – så mycket får du tjäna</h2>
<p>Du får tjäna <strong>{fmt(K['FRI']['100'])} kr per kalenderhalvår</strong> vid 20 veckors heltidsstudier utan att studiemedlet minskar, ungefär {fmt(round(FRI_MAN, -2))} kr i månaden. På 75 % är gränsen {fmt(K['FRI']['75'])} kr och på 50 % {fmt(K['FRI']['50'])} kr. Tjänar du mer minskar studiemedlet med {round(K['FRI_RED'] * 100)} % av det som ligger över gränsen (heltid med bidrag och lån).</p>

<h2>Betala tillbaka lånet</h2>
<p>Du börjar betala vid ett årsskifte, tidigast sex månader efter att du senast hade studiestöd. Räntan är {str(K['RANTA']).replace('.', ',')} % 2026 och minsta årsbelopp {fmt(K['MIN_AR'])} kr. Lån från 2022 betalar du på i högst 25 år, och senast till det år du fyller 64. Räkna på din skuld i <a href="/kalkylatorer/csn-kalkylator">CSN-kalkylatorn</a>.</p>

<h2>Vanliga frågor om CSN 2026</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['belopp']}" {A}>CSN – Hur mycket pengar kan jag få eller låna?</a> – veckobelopp 2026 för 100, 75 och 50 %, utbetalning fyra veckor i taget, låna mindre eller inte alls</li>
<li><a href="{SRC['studiemedel']}" {A}>CSN – Studiemedel</a> – 4 120 + 9 472 = 13 592 kr per 4 veckor, ränta 2,135 %, bidrag och lån, utbetalning den 25:e</li>
<li><a href="{SRC['hogre']}" {A}>CSN – Högre bidraget för vissa studier</a> – 2 279 + 1 119 kr per vecka och villkoren</li>
<li><a href="{SRC['tb']}" {A}>CSN – Tilläggsbidrag</a> – belopp 2026 för 1–5 barn, bostadsbidrag, 18 år, en vårdnadshavare</li>
<li><a href="{SRC['tl']}" {A}>CSN – Tilläggslån</a> – 1 172 kr per vecka (4 688 kr per 4 veckor), från 25 år</li>
<li><a href="{SRC['fri']}" {A}>CSN – Inkomst och fribelopp</a> – 114 676 / 143 346 / 172 017 kr, minskning 61 %, vilka inkomster som räknas</li>
<li><a href="{SRC['n2027']}" {A}>CSN – Studiemedlet och fribeloppet höjs till 2027</a> (25 september 2026) – 13 684 kr, +28/+64 kr, tilläggslån 4 720 kr, tilläggsbidrag 784/1 284 kr + 260 kr per barn, fribelopp 115 451 kr, prisbasbelopp 59 600 kr</li>
<li><a href="{SRC['betala']}" {A}>CSN – Betala tillbaka studielån</a> – start, 25 år/64 år, ränta, minsta årsbelopp 8 880 kr</li>
<li><a href="{SRC['skatt']}" {A}>SFS 2022:860 – inkomstskattelagen 11 kap. 34 §</a> – studiestöd enligt studiestödslagen ska inte tas upp till beskattning</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/csn-kalkylator"><span>CSN-kalkylator<small>Vad du betalar tillbaka per år och månad</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/barnbidrag-2026"><span>Barnbidrag 2026<small>Belopp och flerbarnstillägg</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/loneraknare"><span>Löneräknare<small>Vad blir kvar av extrajobbet efter skatt?</small></span>{CHEV}</a>
</div>
</div>
</main>
"""
    body = re.sub(r"(\d) (\d{3})(?!\d)", "\\1&nbsp;\\2", body).replace(" %", "&nbsp;%")
    body += f'''<script id="gk-csn" type="application/json">{json.dumps(K)}</script>
<script>
{JS}
</script>
'''
    style = """<style>
.csn-top{margin-bottom:28px}
.csn-t td strong{display:block;font-size:16px}
.csn-t td small{display:block;font-size:12px;font-weight:500;color:var(--gk-muted)}
.csn-t tbody th{font-weight:600;text-align:left;padding:10px 6px;border-bottom:1px solid var(--gk-border)}
.csn-t tbody th small{display:block;font-size:12px;font-weight:500;color:var(--gk-muted)}
.gk-prose .gk-table-wrap{margin:16px 0}
.gk-prose .gk-table tbody th{font-weight:600;text-align:left;padding:10px 6px;border-bottom:1px solid var(--gk-border)}
.csn-calc-h{font-size:24px;margin:0 0 12px}
@media (min-width:900px){.csn-top{max-width:820px}.csn-calc-h{font-size:30px}}
</style>"""
    return (S.head(title, desc, PATH, og_title=h1, jsonld=ld, extra_head=style)
            + S.header() + body + S.footer("Beloppen kommer från CSN – CSN beslutar om ditt studiemedel."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-csn').textContent);
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(v, 0) + ' kr'; };
  var st = { takt: '100', lan: true, barn: 0 };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  seg('takt', function (v) { st.takt = v; });
  seg('lan', function (v) { st.lan = v === '1'; });
  seg('barn', function (v) { st.barn = +v; });

  /* Modell – samma som csn() i scripts/build_csn_guide.py */
  function csn(takt, lan, barn) {
    var v = C.V[takt], b = v.bidrag, l = lan ? v.lan : 0, t = barn > 0 ? C.TB[takt][barn - 1] : 0, w = b + l + t;
    return { bidrag4: b * 4, lan4: l * 4, tb4: t * 4, vecka: w, tot4: w * 4, bort4: (v.lan - l) * 4, fri: C.FRI[takt] };
  }
  window.gkCsn = csn;

  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  function calc() {
    var r = csn(st.takt, st.lan, st.barn), full = csn('100', true, 0), pct = st.takt + '\u00a0%';
    var fritt = r.bidrag4 + r.tb4;
    $('resBig').textContent = GK.fmt(r.tot4, 0);
    $('resSub').textContent = 'Ungefär en månadsutbetalning. ' + kr(r.vecka) + ' per vecka, och ' + GK.fmt(fritt / r.tot4 * 100, 0) + '\u00a0% (' + kr(fritt) + ') betalar du inte tillbaka.';
    $('tiles').innerHTML = tile('Bidrag', kr(r.bidrag4), 'Betalas inte tillbaka') +
      tile('Lån', kr(r.lan4), st.lan ? 'Betalas tillbaka' : 'Du tar inget lån') +
      tile('Tilläggsbidrag', kr(r.tb4), st.barn ? st.barn + ' barn, skattefritt' : 'Bara om du har barn') +
      tile('Per vecka', kr(r.vecka), 'Studietakt ' + pct);

    var v = '';
    if (st.takt === '100' && st.lan) {
      v += verdict('good', 'Fullt studiemedel: ' + kr(full.tot4), 'Det är det högsta grundbeloppet ' + C.AR + '. Från 1 januari ' + C.N.AR + ' blir det ' + kr(C.N.TOT4) + ' per 4 veckor, ' + kr(C.N.TOT4 - full.tot4) + ' mer.');
    } else {
      v += verdict('info', kr(full.tot4 - (r.tot4 - r.tb4)) + ' mindre än fullt studiemedel', 'Fullt studiemedel på heltid är ' + kr(full.tot4) + ' per 4 veckor ' + C.AR + '.' + (st.lan ? '' : ' Lånet hade gett dig ' + kr(r.bort4) + ' till, med ' + GK.fmt(C.RANTA, 3) + '\u00a0% ränta ' + C.AR + '.'));
    }
    v += verdict('info', 'Du får tjäna ' + kr(r.fri) + ' per halvår', 'Det är fribeloppet ' + C.AR + ' vid 20 veckors studier på ' + pct + ' – ungefär ' + kr(Math.round(r.fri / 6 / 100) * 100) + ' i månaden. Tjänar du mer minskar studiemedlet.');
    $('verdict').innerHTML = v;

    var V = C.V[st.takt];
    $('how').innerHTML =
      '<p>CSN:s veckobelopp ' + C.AR + ' på ' + pct + ': bidrag ' + kr(V.bidrag) + (st.lan ? ' + lån ' + kr(V.lan) : ' (inget lån)') +
      (st.barn ? ' + tilläggsbidrag ' + kr(r.tb4 / 4) + ' för ' + st.barn + ' barn' : '') + ' = ' + kr(r.vecka) + ' per vecka.</p>' +
      '<p>' + kr(r.vecka) + ' × 4 veckor = ' + kr(r.tot4) + '. CSN betalar vanligtvis ut studiemedlet för fyra veckor i taget, den 25:e varje månad du studerar.</p>' +
      '<p>Studiemedel och tilläggsbidrag är skattefria. Tilläggslån och högre bidrag ingår inte i räknaren.</p>';
  }

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "artiklar", "csn-2026-belopp-och-regler.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    for takt, lan, barn in [("100", True, 0), ("75", True, 2), ("50", False, 1), ("100", True, 5), ("100", False, 3)]:
        r = csn(takt, lan, barn)
        print(f"takt={takt} lån={lan} barn={barn}: per 4 v {r['tot4']}, per vecka {r['vecka']}, bidrag {r['bidrag4']}, "
              f"lån {r['lan4']}, tilläggsbidrag {r['tb4']}, fribelopp {r['fri']}")
    print("2027:", N["BIDRAG4"], N["LAN4"], N["TOT4"], N["TB4"])


if __name__ == "__main__":
    main()
