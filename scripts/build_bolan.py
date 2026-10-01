#!/usr/bin/env python3
"""Bygger kalkylatorer/bolanekalkylator.html i den nya verktygsmallen.

Regler (kontrollerade 1 oktober 2026):
  - Lag (2026:226) om begränsning av bostadskrediter, gäller från 1 april 2026 och ersätter FI:s föreskrifter
    (FFFS 2016:16 och 2016:33 upphävda 31 mars 2026):
      4 §  belåningsgrad högst 90 % när en bostadskredit lämnas (bolånetaket),
      5 §  högst 80 % när en kredit utökas,
      7 §  amortering minst 1 % per år av det högsta kreditbeloppet om belåningsgraden är över 50 men högst 70 %,
           minst 2 % om den är över 70 %,
      2 §  belåningsgrad = aktuellt totalt kreditbelopp / bostadens marknadsvärde,
      13 § marknadsvärdet vid köpet, omvärdering tidigast efter fem år,
      9–10 §§ undantag vid särskilda skäl och för nyproducerad bostad (högst fem år),
      övergångsbestämmelser: 7 § gäller inte krediter lämnade före 1 juni 2016 (kreditinstitut).
  - Regeringen 5 mars 2026: det skärpta kravet (upp till 3 % när lånet är över 4,5 gånger bruttoårsinkomsten)
    tas bort, men upphör inte automatiskt för lån som omfattas av det i dag.
  - Skatteverket: skattereduktion 30 % av underskott av kapital upp till 100 000 kr och 21 % över, per person,
    och högst så mycket skatt som personen betalar. Från inkomstår 2026 bara lån med säkerhet (bolån ingår).
  - SCB/Riksbanken, Finansmarknadsstatistik augusti 2026 (publicerad 25 september 2026): snittränta nya bolån.

Modell (samma i Python-referensen och i sidans JS):
  Belåningsgrad = lån / värde. Kravet = 2 % (över 70 %), 1 % (över 50 %), annars 0, av det högsta lånebeloppet
  (= lånet när det tas). Månadskostnad första månaden = lån × ränta / 12 + lån × amortering / 12.
  Ränteavdrag = 30 % av årsräntan upp till 100 000 kr per låntagare + 21 % över (räntan delas lika).
  Plan år för år: skulden vid årets början avgör belåningsgraden och därmed kravet det året. Bostadens värde
  antas oförändrat (ingen omvärdering).

    python3 scripts/build_bolan.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/bolanekalkylator"
UPDATED = "1 oktober 2026"

# Regler och statistik – byt här vid regeländring eller ny månadsstatistik
K = {
    "TAK": 90,            # bolånetak, % av värdet (lag 2026:226 4 §)
    "TAK_UTOK": 80,       # vid utökning (5 §)
    "GR_HOG": 70,         # belåningsgrad över 70 % -> 2 % (7 §)
    "GR_LAG": 50,         # över 50 % -> 1 % (7 §)
    "AM_HOG": 2,
    "AM_LAG": 1,
    "SKARPT_KVOT": 4.5,   # gamla skärpta kravet, lån > 4,5 × bruttoårsinkomst (bara äldre lån)
    "SKARPT_EXTRA": 1,    # ... gav upp till 3 % i stället för 2 %
    "AVDRAG_LAG": 30,     # skattereduktion % upp till gränsen (Skatteverket)
    "AVDRAG_HOG": 21,     # över gränsen
    "AVDRAG_GRANS": 100000,
    "OMV_AR": 5,          # omvärdering tidigast efter 5 år (13 §)
    "SNITT": 2.78,        # SCB/Riksbanken: nya bolån, augusti 2026
    "SNITT_RORLIG": 2.73,
    "SNITT_1_5": 3.18,
    "SNITT_5": 3.34,
    "SNITT_MAN": "augusti 2026",
    "SNITT_PUBL": "25 september 2026",
}
# Förval i formuläret – exempel, inga marknadssiffror
D = {"PRIS": 3000000, "KPCT": 10, "RANTA": 3.0}

SRC = {
    "lag": "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/lag-2026226-om-begransning-av-bostadskrediter_sfs-2026-226/",
    "reg": "https://regeringen.se/pressmeddelanden/2026/03/nya-lagandringar-ska-ge-fler-mojlighet-att-aga-sin-bostad/",
    "fi": "https://fi.se/globalassets/media/dokument/fffs-bilagor/2026/beslutspm-fs2601-03.pdf",
    "skv": "https://www.skatteverket.se/privat/deklaration/avdragforprivatpersoner/avdragforranteutgifter.106.1b39a64a1919eabb488b87.html",
    "scb": "https://www.scb.se/hitta-statistik/statistik-efter-amne/finansmarknad/finansmarknadsstatistik/finansmarknadsstatistik/pong/statistiknyhet/finansmarknadsstatistik-augusti-2026/",
}


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def r10(v):
    """Avrundar till närmaste 10 kr som JS Math.round(v / 10) * 10."""
    return math.floor(v / 10 + 0.5) * 10


def kr(v):
    return fmt(r10(v)) + " kr"


def pct(v):
    s = f"{v:.2f}".replace(".", ",").rstrip("0").rstrip(",")
    return s + " %"


def krav(ltv):
    """Amorteringskrav i % per år för en belåningsgrad i % (lag 2026:226 7 §)."""
    return K["AM_HOG"] if ltv > K["GR_HOG"] else K["AM_LAG"] if ltv > K["GR_LAG"] else 0


def avdrag(ranta_ar, pers=1):
    """Skattereduktion för ränta per år, räntan delad lika på pers låntagare."""
    p = ranta_ar / pers
    return pers * (K["AVDRAG_LAG"] / 100 * min(p, K["AVDRAG_GRANS"]) + K["AVDRAG_HOG"] / 100 * max(0, p - K["AVDRAG_GRANS"]))


def bolan(V, L, r, egen=None, pers=1, skarpt=False, ink=0):
    """Python-referens – samma logik som sidans JS. V = värde, L = lån, r = ränta %, egen = egen amortering %/år
    (None = kravet), pers = antal låntagare, skarpt/ink = äldre lån som har kvar det skärpta kravet."""
    ltv = L / V * 100
    extra = K["SKARPT_EXTRA"] if (skarpt and ink > 0 and L > K["SKARPT_KVOT"] * ink) else 0
    k0 = krav(ltv)
    apct = egen if egen is not None else k0 + extra
    ranta = L * r / 100 / 12
    amort = min(L, L * apct / 100) / 12
    av = avdrag(ranta * 12, pers) / 12
    rows = []
    s, y = L, 0
    while s > 0.5 and y < 60:
        y += 1
        k = krav(s / V * 100)
        ex = K["SKARPT_EXTRA"] if (skarpt and ink > 0 and s > K["SKARPT_KVOT"] * ink) else 0
        p = egen if egen is not None else k + ex
        a = min(s, L * p / 100)
        rows.append({"ar": y, "skuld": s, "ranta": s * r / 100 / 12, "amort": a / 12, "p": p})
        if a <= 0:
            break
        s -= a
    return {"ltv": ltv, "krav": k0, "extra": extra, "apct": apct, "ranta": ranta, "amort": amort,
            "manad": ranta + amort, "avdrag": av, "efter": ranta + amort - av, "rows": rows, "rest": s}


def faser(rows):
    """Grupperar planen i perioder med samma amorteringsprocent: [(från år, till år, procent)]."""
    out = []
    for x in rows:
        if out and out[-1][2] == x["p"]:
            out[-1][1] = x["ar"]
        else:
            out.append([x["ar"], x["ar"], x["p"]])
    return out


EX = bolan(D["PRIS"], D["PRIS"] * (1 - D["KPCT"] / 100), D["RANTA"])
EX3M = bolan(3750000, 3000000, 3.0)                      # 80 %
EX2M = bolan(2500000, 2000000, 2.0)                      # 80 %, för amorteringsexemplet
EXSN = bolan(2500000, 2000000, K["SNITT"])               # snitträntan
AV5_1 = avdrag(5000000 * 0.03, 1)
AV5_2 = avdrag(5000000 * 0.03, 2)
EX_FAS = faser(EX["rows"])

FAQ = [
    ("Hur räknar man ut månadskostnaden för ett bolån?",
     "Lägg ihop räntan och amorteringen. Räntan per månad är lånet gånger räntan delat med 12, och amorteringen är lånet "
     "gånger amorteringskravet delat med 12. Ett lån på 3 000 000 kr med 3 % ränta och 2 % amortering kostar "
     f"{fmt(EX3M['ranta'])} + {fmt(EX3M['amort'])} = {fmt(EX3M['manad'])} kr i månaden. Ränteavdraget sänker kostnaden med "
     f"{fmt(EX3M['avdrag'])} kr i månaden. Avgift till föreningen, drift och försäkring tillkommer."),
    ("Hur räknar man ut amortering på bolån?",
     "Amorteringen är en procent av lånet per år: 2 % om lånet är mer än 70 % av bostadens värde och 1 % om det är mer än 50 %. "
     "Lånar du 2 000 000 kr till en bostad värd 2 500 000 kr är belåningsgraden 80 %. Då ska du amortera minst 40 000 kr om året, "
     f"alltså {fmt(EX2M['amort'])} kr i månaden. Under 50 % finns inget krav."),
    ("Hur räknar man ut räntan på ett bolån?",
     "Multiplicera lånet med räntan och dela med 12. Med 2 000 000 kr i lån och snitträntan för nya bolån, "
     f"{pct(K['SNITT'])}, blir räntan {fmt(2000000 * K['SNITT'] / 100)} kr om året eller {fmt(EXSN['ranta'])} kr i månaden. "
     f"Efter ränteavdraget på 30 % blir det {fmt(EXSN['ranta'] - EXSN['avdrag'])} kr. Räntan sjunker i takt med att du amorterar."),
    ("Vad är amorteringskravet 2026?",
     "Sedan 1 april 2026 står amorteringskravet i lagen om begränsning av bostadskrediter. Är belåningsgraden över 70 % ska du "
     "amortera minst 2 % av lånet per år, och över 50 % minst 1 %. Procenten räknas på det högsta lånebeloppet efter den senaste "
     "värderingen och belåningsgraden på bostadens värde när du köpte den. Banken får värdera om bostaden tidigast efter fem år. "
     "Banken kan medge uppehåll om det finns särskilda skäl, och för en nyproducerad bostad i högst fem år. "
     "Lån som togs före 1 juni 2016 omfattas inte."),
    ("Finns det skärpta amorteringskravet kvar?",
     "Inte för nya lån. Tidigare fick den som lånade mer än 4,5 gånger hushållets årsinkomst före skatt amortera upp till 3 % "
     "per år. Kravet togs bort 1 april 2026, men på lån som redan omfattades av det upphör det inte automatiskt – du behöver "
     "be banken ändra villkoren. Under Fler val i kalkylatorn ser du hur mycket det sänker amorteringen."),
    ("Hur mycket är ränteavdraget på bolån?",
     "Du får en skattereduktion på 30 % av räntan upp till 100 000 kr om året och 21 % på det som är över. Gränsen gäller per "
     "person. Betalar du 150 000 kr i ränta och står ensam på lånet blir avdraget "
     f"{fmt(AV5_1)} kr. Är ni två som delar lika får ni {fmt(AV5_2)} kr tillsammans. Avdraget kan inte bli större än "
     "den skatt du betalar."),
    ("Vad är bolåneräntan just nu?",
     f"Enligt SCB:s finansmarknadsstatistik var snitträntan för hushållens nya bolån {pct(K['SNITT'])} i {K['SNITT_MAN']}. "
     f"Rörlig ränta var i snitt {pct(K['SNITT_RORLIG'])}, bunden 1–5 år {pct(K['SNITT_1_5'])} och bunden över 5 år "
     f"{pct(K['SNITT_5'])}. Din ränta beror bland annat på bank och bindningstid."),
    ("Hur mycket kontantinsats behöver man?",
     "Minst 10 % av bostadens pris, eftersom du får låna högst 90 % sedan 1 april 2026 (tidigare 85 %). Köper du en bostad för "
     "3 000 000 kr behöver du alltså minst 300 000 kr. Utökar du ett lån senare får det bli högst 80 % av bostadens värde."),
]

CHEV = S.ICON_CHEV


def seg_btns(items, pressed):
    out = []
    for v, txt, small in items:
        sm = f"<small>{small}</small>" if small else ""
        out.append(f'<button type="button" data-v="{v}" aria-pressed="{"true" if v == pressed else "false"}">{txt}{sm}</button>')
    return "".join(out)


def page():
    title = "Bolånekalkylator: räkna ut ränta & amortering | GratisKalkyl"
    desc = (f"Räkna ut ränta, amortering och ränteavdrag på ditt bolån med reglerna 2026. Exempel: 2,7 miljoner till 3 % "
            f"kostar {fmt(EX['manad'])} kr/mån före ränteavdrag.")
    crumbs = [("Hem", "/"), ("Boende & lån", "/boende-och-lan"), ("Bolånekalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Bolånekalkylator 2026",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Boende & lån", "item": S.SITE + "/boende-och-lan"},
            {"@type": "ListItem", "position": 3, "name": "Bolånekalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    ex = []
    for L in (2000000, 3000000, 4000000, 5000000):
        b = bolan(L / 0.9, L, 3.0)
        ex.append(f"<tr><td>{fmt(L)}</td><td>{fmt(r10(b['ranta']))}</td><td>{fmt(r10(b['amort']))}</td>"
                  f"<td><strong>{fmt(r10(b['manad']))}</strong></td></tr>")
    ex_rows = "".join(ex)
    f1, f2 = EX_FAS[0], EX_FAS[1]

    kbtn = seg_btns([(10, "10 %", "kontantinsats"), (30, "30 %", "kontantinsats"), (50, "50 %", "kontantinsats")], D["KPCT"])
    rbtn = seg_btns([(K["SNITT_RORLIG"], pct(K["SNITT_RORLIG"]), "rörlig"), (K["SNITT_1_5"], pct(K["SNITT_1_5"]), "1–5 år"),
                     (K["SNITT_5"], pct(K["SNITT_5"]), "över 5 år")], None)
    pbtn = seg_btns([(1, "En", "står på lånet"), (2, "Två", "delar lika")], 1)
    lan0 = D["PRIS"] * (1 - D["KPCT"] / 100)

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Bolånekalkylator 2026</div>
<h1>Vad kostar bolånet per månad?</h1>
<p class="gk-lead">Räkna ut ränta, amortering och ränteavdrag – och vilket amorteringskrav som gäller för ditt lån.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Regler från 1 april 2026 · Källa: <a href="{SRC['lag']}" target="_blank" rel="noopener">lag (2026:226) om begränsning av bostadskrediter</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="bform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="pris">Bostadens pris eller värde</label>
<div class="gk-input"><input id="pris" inputmode="numeric" autocomplete="off" value="{fmt(D['PRIS'])}"><span class="unit">kr</span></div>
</div>

<div class="gk-field">
<label for="lan">Lånebelopp</label>
<div class="gk-input"><input id="lan" inputmode="numeric" autocomplete="off" value="{fmt(lan0)}"><span class="unit">kr</span></div>
<div class="gk-seg" style="--n:3" id="kq" role="group" aria-label="Kontantinsats">
{kbtn}
</div>
<span class="gk-hint" id="kHint"></span>
</div>

<div class="gk-field">
<label for="ranta">Ränta</label>
<div class="gk-input"><input id="ranta" inputmode="decimal" autocomplete="off" value="{pct(D['RANTA'])[:-2]}"><span class="unit">% per år</span></div>
<div class="gk-seg" style="--n:3" id="rq" role="group" aria-label="Snitträntor för nya bolån {K['SNITT_MAN']}">
{rbtn}
</div>
<span class="gk-hint">{pct(D['RANTA'])} är ett exempel – skriv din ränta. Knapparna är snitträntor för nya bolån i {K['SNITT_MAN']} (<a href="{SRC['scb']}" target="_blank" rel="noopener">SCB</a>).</span>
</div>

<details class="gk-more">
<summary>Fler val: två låntagare, äldre lån</summary>
<div>
<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur många står på lånet?</legend>
<div class="gk-seg" style="--n:2" id="pq" role="group" aria-label="Antal låntagare">
{pbtn}
</div>
<span class="gk-hint">Gränsen 100 000 kr för ränteavdraget på 30 % gäller per person.</span>
</fieldset>
<div class="gk-field">
<label for="egen">Egen amortering</label>
<div class="gk-input"><input id="egen" inputmode="decimal" autocomplete="off" placeholder="kravet"><span class="unit">% per år</span></div>
<span class="gk-hint">Lämna tomt så räknar vi med amorteringskravet. Fyll i om du vill amortera mer.</span>
</div>
<label class="gk-check"><input type="checkbox" id="skarpt"> <span>Mitt lån har kvar det skärpta amorteringskravet (lån över 4,5 gånger hushållets årsinkomst, taget före 1 april 2026)</span></label>
<div class="gk-field">
<label for="ink">Hushållets årsinkomst före skatt</label>
<div class="gk-input"><input id="ink" inputmode="numeric" autocomplete="off" placeholder="t.ex. 600 000"><span class="unit">kr/år</span></div>
<span class="gk-hint">Behövs bara för det skärpta kravet. Nya lån har inget sådant krav sedan 1 april 2026.</span>
</div>
</div>
</details>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:12px" aria-labelledby="sensH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="sensH" style="font-size:22px">Om räntan ändras</h2>
<p class="gk-hint">Samma lån och amortering, första månaden.</p>
</div>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="sensTable"></table></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Ditt bolån kostar</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-o4" style="gap:12px" aria-labelledby="planH">
<h2 id="planH" style="font-size:22px">Så minskar skulden</h2>
<p class="gk-hint" id="planSum"></p>
<details class="gk-more">
<summary>Visa år för år</summary>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="planTable"></table></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="/artiklar/hur-mycket-far-jag-lana-2026"><span>Hur mycket får du låna?<small>Så räknar banken med inkomst, kalkylränta och bolånetak</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/amorteringskalkylator"><span>Har du redan ett lån?<small>Amorteringskalkylator – räkna på det ursprungliga lånet</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Går budgeten ihop?<small>Hushållsbudget med boendekostnaden inräknad</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknar du ut ränta och amortering</h2>
<p>Månadskostnaden för ett bolån är ränta plus amortering. <strong>Ränta per månad</strong> = lånet × räntan / 12. <strong>Amortering per månad</strong> = lånet × amorteringskravet / 12. Ett lån på {fmt(lan0)} kr med {pct(D['RANTA'])} ränta och 2 % amortering kostar {fmt(EX['ranta'])} + {fmt(EX['amort'])} = <strong>{fmt(EX['manad'])} kr i månaden</strong>, eller ungefär {kr(EX['efter'])} efter ränteavdraget.</p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight">
<thead><tr><th scope="col">Lån</th><th scope="col">Ränta</th><th scope="col">Amortering</th><th scope="col">Totalt</th></tr></thead>
<tbody>{ex_rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor per månad, första månaden, före ränteavdrag. 3 % ränta (exempel) och 10 % kontantinsats, alltså 2 % amortering.</caption>
</table></div>

<h2>Amorteringskrav 2026</h2>
<ul>
<li>Lånet är mer än <strong>70 %</strong> av bostadens värde: amortera minst <strong>2 %</strong> av lånet per år.</li>
<li>Mer än <strong>50 %</strong>: minst <strong>1 %</strong>.</li>
<li>50 % eller mindre: inget krav.</li>
</ul>
<p>Procenten räknas på det högsta lånebeloppet och belåningsgraden på bostadens värde när du köpte den. När skulden har minskat sjunker kravet – med 10 % kontantinsats efter {f1[1]} år till 1 % och efter {f2[1]} år till noll, om värdet är oförändrat. Banken får värdera om bostaden tidigast efter fem år. Det <strong>skärpta kravet</strong> för lån över 4,5 gånger hushållets årsinkomst togs bort 1 april 2026. På äldre lån försvinner det inte automatiskt – be banken ändra villkoren.</p>

<h2>Bolånetaket: minst 10 % kontantinsats</h2>
<p>Sedan 1 april 2026 får du låna högst <strong>90 %</strong> av bostadens värde när du köper, mot 85 % tidigare. Utökar du lånet senare får belåningsgraden bli högst 80 %.</p>

<h2>Ränteavdrag på bolånet</h2>
<p>Du får en skattereduktion på <strong>30 %</strong> av räntan upp till 100 000 kr per år och 21 % på det som är över. Gränsen gäller per person, och avdraget kan inte bli större än den skatt du betalar.</p>

<h2>Bolåneräntan just nu</h2>
<p>Snitträntan för nya bolån var <strong>{pct(K['SNITT'])}</strong> i {K['SNITT_MAN']} enligt SCB. Rörlig ränta låg på {pct(K['SNITT_RORLIG'])} och bunden ränta på {pct(K['SNITT_1_5'])} (1–5 år) och {pct(K['SNITT_5'])} (över 5 år). Räntan i kalkylatorn är ett exempel – byt till din egen.</p>

<h2>Vanliga frågor om bolån</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['lag']}" target="_blank" rel="noopener">Lag (2026:226) om begränsning av bostadskrediter</a> – bolånetak 90&nbsp;% (4&nbsp;§), 80&nbsp;% vid utökning (5&nbsp;§), amortering 2&nbsp;% och 1&nbsp;% av det högsta kreditbeloppet (7&nbsp;§), belåningsgrad (2&nbsp;§), uppehåll vid särskilda skäl och nyproduktion (9–10&nbsp;§§), värdering och omvärdering efter fem år (13&nbsp;§), lån före 1 juni 2016 (övergångsbestämmelser)</li>
<li><a href="{SRC['reg']}" target="_blank" rel="noopener">Regeringen, 5 mars 2026 – Nya lagändringar ska ge fler möjlighet att äga sin bostad</a> – bolånetaket höjs från 85 till 90 %, det skärpta amorteringskravet tas bort men upphör inte automatiskt för befintliga lån</li>
<li><a href="{SRC['fi']}" target="_blank" rel="noopener">Finansinspektionen – beslut att upphäva föreskrifterna om amortering och bolånetak</a> från 31 mars 2026</li>
<li><a href="{SRC['skv']}" target="_blank" rel="noopener">Skatteverket – Avdrag för ränteutgifter</a> – skattereduktion 30 % upp till 100 000 kr och 21 % över, begränsad av din skatt</li>
<li><a href="{SRC['scb']}" target="_blank" rel="noopener">SCB, Finansmarknadsstatistik {K['SNITT_MAN']}</a> (publicerad {K['SNITT_PUBL']}, statistikansvarig Riksbanken) – snitträntor för hushållens nya bolån</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/hyra-vs-kopa-kalkylator"><span>Hyra eller köpa?<small>Jämför boendekostnaden över tid</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/amorteringskrav-2026"><span>Guide: Amorteringskrav 2026<small>De nya reglerna och räkneexempel</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/uthyrningskalkylator"><span>Uthyrningskalkylator<small>Hyr ut en del av bostaden</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-bolan" type="application/json">{json.dumps(K, ensure_ascii=False)}</script>
<script>
{JS}
</script>
"""
    head = S.head(title, desc, PATH, og_title="Vad kostar bolånet per månad? Bolånekalkylator 2026", jsonld=ld)
    # Inga annonser på bolånesidan (kreditreklam): ta bort AdSense-skriptet från standardhuvudet.
    ads = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={S.ADSENSE}" '
           'crossorigin="anonymous"></script>\n')
    assert ads in head, "AdSense-raden i gk2_shell.head har ändrats – uppdatera build_bolan.py"
    head = head.replace(ads, "")
    return (head + S.header() + body
            + S.footer("Bolåneberäkningen är en uppskattning – din bank beslutar om ränta och amortering."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-bolan').textContent);
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var rp = function (v) { return GK.fmt(v, 2).replace(/,?0+$/, ''); };
  var lp = function (v) { return GK.fmt(v, 1).replace(/,0$/, ''); };
  var st = { kpct: 10, pers: 1 };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', v != null && Math.abs(+x.getAttribute('data-v') - v) < 1e-9 ? 'true' : 'false'); }); }
  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function setLan() { var V = val('pris'); if (V && st.kpct != null) $('lan').value = GK.fmt(Math.round(V * (1 - st.kpct / 100)), 0); }

  seg('kq', function (v) { st.kpct = +v; setLan(); });
  seg('rq', function (v) { $('ranta').value = GK.fmt(+v, 2); });
  seg('pq', function (v) { st.pers = +v; });
  $('pris').addEventListener('input', function () { setLan(); calc(); });
  $('lan').addEventListener('input', function () {
    var V = val('pris'), L = val('lan');
    st.kpct = null;
    press('kq', V && L != null ? Math.round((1 - L / V) * 1000) / 10 : null);
    calc();
  });
  $('ranta').addEventListener('input', function () { press('rq', val('ranta')); calc(); });
  ['egen', 'ink'].forEach(function (id) { $(id).addEventListener('input', calc); });
  $('skarpt').addEventListener('change', calc);
  ['pris', 'lan', 'ink'].forEach(function (id) { GK.groupInput($(id)); });

  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  /* Modell – samma som scripts/build_bolan.py */
  function krav(ltv) { return ltv > C.GR_HOG ? C.AM_HOG : (ltv > C.GR_LAG ? C.AM_LAG : 0); }
  function avdrag(rantaAr, pers) {
    var p = rantaAr / pers;
    return pers * (C.AVDRAG_LAG / 100 * Math.min(p, C.AVDRAG_GRANS) + C.AVDRAG_HOG / 100 * Math.max(0, p - C.AVDRAG_GRANS));
  }
  function bolan(V, L, r, egen, pers, skarpt, ink) {
    var ltv = L / V * 100;
    var extra = (skarpt && ink > 0 && L > C.SKARPT_KVOT * ink) ? C.SKARPT_EXTRA : 0;
    var k0 = krav(ltv), apct = egen != null ? egen : k0 + extra;
    var ranta = L * r / 100 / 12, amort = Math.min(L, L * apct / 100) / 12, av = avdrag(ranta * 12, pers) / 12;
    var rows = [], s = L, y = 0;
    while (s > 0.5 && y < 60) {
      y += 1;
      var k = krav(s / V * 100), ex = (skarpt && ink > 0 && s > C.SKARPT_KVOT * ink) ? C.SKARPT_EXTRA : 0;
      var p = egen != null ? egen : k + ex, a = Math.min(s, L * p / 100);
      rows.push({ ar: y, skuld: s, ranta: s * r / 100 / 12, amort: a / 12, p: p });
      if (a <= 0) break;
      s -= a;
    }
    return { ltv: ltv, krav: k0, extra: extra, apct: apct, ranta: ranta, amort: amort, manad: ranta + amort, avdrag: av, efter: ranta + amort - av, rows: rows, rest: s };
  }
  function faser(rows) {
    var out = [];
    rows.forEach(function (x) { if (out.length && out[out.length - 1][2] === x.p) out[out.length - 1][1] = x.ar; else out.push([x.ar, x.ar, x.p]); });
    return out;
  }
  function clear(msg) {
    $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'verdict', 'how', 'sensTable', 'planTable', 'planSum'].forEach(function (id) { $(id).innerHTML = ''; });
  }

  function calc() {
    var V = val('pris'), L = val('lan'), r = val('ranta'), ink = val('ink') || 0, sk = $('skarpt').checked;
    var egen = $('egen').value.trim() === '' ? null : val('egen');
    if (V && L != null && L <= V) $('kHint').textContent = 'Kontantinsats ' + kr(V - L) + ' (' + lp((V - L) / V * 100) + ' % av priset). Har du redan lån: skriv skulden i dag.';
    else $('kHint').textContent = 'Har du redan lån: skriv skulden i dag.';
    if (!V || V < 100000) return clear('Fyll i bostadens pris eller värde.');
    if (L == null || L < 10000) return clear('Fyll i hur mycket du lånar.');
    if (L > V) return clear('Lånet kan inte vara större än bostadens värde.');
    if (r == null || r > 20) return clear('Fyll i räntan, till exempel 3.');
    if (egen != null && egen > 50) egen = null;
    var b = bolan(V, L, r, egen, st.pers, sk, ink);

    $('resBig').textContent = GK.fmt(Math.round(b.manad / 10) * 10, 0);
    $('resSub').textContent = 'Ränta + amortering första månaden. Efter ränteavdraget ungefär ' + kr(b.efter) + ' i månaden.';
    var amSub = egen != null ? 'Eget val ' + rp(egen) + ' % · kravet ' + (b.krav + b.extra) + ' %'
      : b.extra ? 'Krav ' + b.krav + ' % + ' + b.extra + ' % skärpt krav'
      : b.krav === C.AM_HOG ? 'Krav ' + b.krav + ' % – lånet är över ' + C.GR_HOG + ' %'
      : b.krav === C.AM_LAG ? 'Krav ' + b.krav + ' % – lånet är över ' + C.GR_LAG + ' %'
      : 'Inget krav – högst ' + C.GR_LAG + ' % belåning';
    $('tiles').innerHTML = tile('Ränta', kr(b.ranta) + '/mån', rp(r) + ' % på ' + kr(L)) +
      tile('Ränta efter avdrag', kr(b.ranta - b.avdrag) + '/mån', 'Ränteavdrag ' + kr(b.avdrag) + '/mån') +
      tile('Amortering', kr(b.amort) + '/mån', amSub) +
      tile('Belåningsgrad', lp(b.ltv) + ' %', 'Kontantinsats ' + kr(V - L));

    var v = '';
    if (b.ltv > C.TAK) {
      v += verdict('warn', 'Över bolånetaket på ' + C.TAK + ' %', 'När du köper får du låna högst ' + C.TAK + ' % av bostadens värde, alltså ' + kr(V * C.TAK / 100) + '. Du behöver minst ' + kr(V * (100 - C.TAK) / 100) + ' i kontantinsats – ' + kr(L - V * C.TAK / 100) + ' mer än du har räknat med.');
    }
    if (b.extra) {
      var utan = bolan(V, L, r, null, st.pers, false, 0);
      v += verdict('warn', 'Det skärpta kravet kostar ' + kr(b.amort - utan.amort) + ' i månaden', 'Nya lån har inte det skärpta kravet sedan 1 april 2026, men på äldre lån försvinner det inte automatiskt. Ber du banken ändra villkoren blir amorteringen ' + kr(utan.amort) + ' i månaden.');
    } else if (sk && ink > 0) {
      v += verdict('info', 'Det skärpta kravet påverkar inte ditt lån', 'Lånet är ' + GK.fmt(L / ink, 1) + ' gånger hushållets årsinkomst – det skärpta kravet gällde bara över ' + GK.fmt(C.SKARPT_KVOT, 1) + ' gånger.');
    }
    if (egen != null && egen < b.krav + b.extra) {
      v += verdict('warn', 'Lägre än amorteringskravet', 'Kravet för ditt lån är ' + (b.krav + b.extra) + ' % per år, ' + kr(L * (b.krav + b.extra) / 100 / 12) + ' i månaden. Banken får bara medge mindre om det finns särskilda skäl eller om bostaden är nyproducerad.');
    } else if (egen == null && b.krav === 0 && !b.extra) {
      v += verdict('good', 'Inget amorteringskrav', 'Lånet är högst ' + C.GR_LAG + ' % av bostadens värde. Du väljer själv om du vill amortera – fyll i egen amortering under Fler val.');
    }
    var d = r - C.SNITT, tiondel = L * 0.1 / 100 / 12;
    var ref = 'Snitträntan för nya bolån var ' + rp(C.SNITT) + ' % i ' + C.SNITT_MAN + ' (rörlig ' + rp(C.SNITT_RORLIG) + ' %). En tiondels procentenhet på ditt lån är ' + kr(tiondel) + ' i månaden före ränteavdrag.';
    if (Math.abs(d) < 0.005) v += verdict('good', 'Samma som snitträntan', ref);
    else if (d < 0) v += verdict('good', 'Din ränta är ' + rp(-d) + ' procentenheter under snittet', ref);
    else v += verdict('info', 'Din ränta är ' + rp(d) + ' procentenheter över snittet', ref);
    $('verdict').innerHTML = v;

    var ra = b.ranta * 12;
    $('how').innerHTML =
      '<p><strong>Belåningsgrad:</strong> ' + kr(L) + ' / ' + kr(V) + ' = ' + lp(b.ltv) + ' %.</p>' +
      '<p><strong>Ränta:</strong> ' + kr(L) + ' × ' + rp(r) + ' % / 12 = ' + kr(b.ranta) + ' i månaden. Räntan sjunker när skulden minskar.</p>' +
      '<p><strong>Amortering:</strong> ' + (egen != null ? 'ditt val, ' + rp(egen) + ' %' : b.apct + ' %') + ' av ' + kr(L) + ' per år = ' + kr(b.amort * 12) + ' om året, ' + kr(b.amort) + ' i månaden. Kravet är 2 % när lånet är över 70 % av bostadens värde och 1 % över 50 %. Procenten räknas på det högsta lånebeloppet. Har du redan lån och skriver dagens skuld kan banken räkna på ett högre belopp.</p>' +
      '<p><strong>Ränteavdrag:</strong> ' + kr(ra) + ' i ränta om året' + (st.pers === 2 ? ', delat på två' : '') + '. 30 % upp till 100 000 kr per person och 21 % över ger ' + kr(b.avdrag * 12) + ' om året, ' + kr(b.avdrag) + ' i månaden – om du betalar minst så mycket i skatt.</p>' +
      '<p>Vi räknar inte med månadsavgift, driftkostnader eller försäkring.</p>';

    var sens = [-1, 0, 1, 2].map(function (dd) { return r + dd; }).filter(function (x) { return x >= 0; });
    $('sensTable').innerHTML = '<thead><tr><th scope="col">Ränta</th><th scope="col">Per månad</th><th scope="col">Efter avdrag</th></tr></thead><tbody>' +
      sens.map(function (rr) {
        var x = bolan(V, L, rr, egen, st.pers, sk, ink), me = Math.abs(rr - r) < 1e-9;
        var c = function (t) { return me ? '<strong>' + t + '</strong>' : t; };
        return '<tr><td>' + c(rp(rr) + ' %') + '</td><td>' + c(GK.fmt(Math.round(x.manad / 10) * 10, 0)) + '<small class="gk-hint" style="display:block">varav ränta ' + GK.fmt(Math.round(x.ranta / 10) * 10, 0) + '</small></td><td>' + c(GK.fmt(Math.round(x.efter / 10) * 10, 0)) + '</td></tr>';
      }).join('') + '</tbody><caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor per månad. Amortering ' + kr(b.amort) + ' i alla rader.</caption>';

    var f = faser(b.rows), last = b.rows[b.rows.length - 1], sum = [];
    f.forEach(function (x) {
      var tid = x[0] === x[1] ? 'År ' + x[0] : 'År ' + x[0] + '–' + x[1];
      if (x[2] > 0) sum.push(tid + ': ' + rp(x[2]) + ' % (' + kr(L * x[2] / 100 / 12) + '/mån)');
      else if (x[0] === 1) sum.push((egen != null ? 'Ingen amortering' : 'Inget amorteringskrav') + ' – skulden ligger kvar på ' + kr(last.skuld));
      else sum.push('Från år ' + x[0] + ': ' + (egen != null ? 'ingen amortering' : 'inget krav') + ' – skulden är då ' + kr(last.skuld));
    });
    if (last.p > 0) sum.push(b.rest <= 0.5 ? 'Lånet är betalt efter ' + last.ar + ' år' : 'Efter ' + last.ar + ' år är skulden ' + kr(b.rest));
    $('planSum').textContent = sum.join('. ') + '.' + (egen == null ? ' Bostadens värde antas vara oförändrat.' : '');
    $('planTable').innerHTML = '<thead><tr><th scope="col">År</th><th scope="col">Skuld</th><th scope="col">Ränta/mån</th><th scope="col">Amort./mån</th></tr></thead><tbody>' +
      b.rows.map(function (x) { return '<tr><td>' + x.ar + '</td><td>' + GK.fmt(Math.round(x.skuld / 1000) * 1000, 0) + '</td><td>' + GK.fmt(Math.round(x.ranta / 10) * 10, 0) + '</td><td>' + GK.fmt(Math.round(x.amort / 10) * 10, 0) + '</td></tr>'; }).join('') +
      '</tbody><caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor. Skulden vid årets början, ränta med samma ränta hela tiden.</caption>';
  }

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "bolanekalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    cases = [
        ("Förval", 3000000, 2700000, 3.0, None, 1, False, 0),
        ("65 %, snittränta", 4000000, 2600000, K["SNITT"], None, 1, False, 0),
        ("Stort lån, en låntagare", 6000000, 5400000, K["SNITT_5"], None, 1, False, 0),
        ("Stort lån, två låntagare", 6000000, 5400000, K["SNITT_5"], None, 2, False, 0),
        ("Skärpt krav", 3500000, 3000000, 3.0, None, 1, True, 600000),
        ("40 %, inget krav", 5000000, 2000000, 2.5, None, 1, False, 0),
        ("Egen amortering 1,5 %", 3000000, 2700000, 3.0, 1.5, 1, False, 0),
    ]
    for name, V, L, r, eg, p, sk, ink in cases:
        b = bolan(V, L, r, eg, p, sk, ink)
        print(f"{name}: belåning {b['ltv']:.1f} %, krav {b['krav']}+{b['extra']} %, ränta {r10(b['ranta'])}, amort {r10(b['amort'])}, "
              f"totalt {r10(b['manad'])}, avdrag {r10(b['avdrag'])}, efter {r10(b['efter'])}, år {len(b['rows'])}, faser {faser(b['rows'])}")


if __name__ == "__main__":
    main()
