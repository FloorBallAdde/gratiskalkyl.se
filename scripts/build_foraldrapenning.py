#!/usr/bin/env python3
"""Bygger kalkylatorer/foraldrapenning.html i den nya verktygsmallen.

Regler och belopp 2026 (verifierade 1 oktober 2026, källor i SRC och på sidan):
  Föräldrapenning på sjukpenningnivå = SGI × 0,97 × 80 % ÷ 365 per dag (SFB 12 kap. 22 § → 28 kap. 7 §),
  lägst 250 kr/dag (grundnivå, 12 kap. 22–23 §§), högst 1 259 kr/dag (SGI-tak 10 pbb = 592 000 kr).
  Lägstanivå 180 kr/dag (12 kap. 24 §). 480 dagar per barn: 390 på sjukpenningnivå + 90 på lägstanivå,
  90 dagar per förälder reserverade. Sjukpenningnivå kräver SGI motsvarande minst 7 083 kr/mån i 240 dagar
  före beräknad födsel. Skatt: assets/skatt2026.js / scripts/skatt2026.py – föräldrapenning ger inget
  jobbskatteavdrag (Skatteverket).

    python3 scripts/build_foraldrapenning.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import skatt2026 as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/foraldrapenning"
UPDATED = "1 oktober 2026"

K = {
    "AR": 2026,
    "PBB": 59200,          # prisbasbelopp 2026
    "SGI_TAK": 592000,     # 10 prisbasbelopp
    "FAKTOR": 0.97,        # SGI × 0,97 (beräkningsunderlag, SFB 28 kap. 7 §)
    "NIVA": 0.80,          # 80 % av beräkningsunderlaget
    "MAX": 1259,           # högsta föräldrapenning per dag 2026
    "GRUND": 250,          # grundnivå, lägsta belopp på sjukpenningnivå
    "LAGSTA": 180,         # lägstanivå
    "VILLKOR_MAN": 7083,   # SGI motsvarande minst denna månadslön i 240 dagar för sjukpenningnivå
    "VILLKOR_DAGAR": 240,
    "DAGAR": 480, "DAGAR_SPN": 390, "DAGAR_LAG": 90, "RESERV": 90,
    "SNITT_KS": 32.38,
}

SRC = {
    "belopp": "https://www.forsakringskassan.se/privatperson/e-tjanster-blanketter-och-informationsmaterial/aktuella-belopp",
    "fp": "https://www.forsakringskassan.se/privatperson/familj-och-barn/foraldrapenning",
    "sgi": "https://www.forsakringskassan.se/privatperson/sjukpenninggrundande-inkomst-sgi",
    "helg": "https://www.forsakringskassan.se/nyhetsarkiv/nyheter-press/2025-04-01-nya-regler-for-foraldrapenning-under-helger",
    "sfb": "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/socialforsakringsbalk-2010110_sfs-2010-110/",
    "skv": "https://www.skatteverket.se/privat/skatter/arbeteochinkomst/skattereduktioner/jobbskatteavdrag.4.6fdde64a12cc4eee2308000107.html",
    "fpt": "https://www.afaforsakring.se/kundtjanst/fragor-och-svar/vad-aer-skillnaden-mellan-foeraeldrapenning-och-foeraeldrapenningtillaegg",
}


def fmt(n):
    """Tusentalsavgränsare med hårt mellanslag (bryts inte på mobil)."""
    return f"{n:,.0f}".replace(",", "\u00a0")


def plain(s):
    return s.replace("\u00a0", " ")


def rnd(x):
    """Avrundning som Math.round i JS (0,5 uppåt)."""
    return math.floor(x + 0.5)


def r10(x):
    return rnd(x / 10) * 10


def dag(lon):
    """Föräldrapenning per hel dag på sjukpenningnivå (kr), före skatt."""
    sgi = min(lon * 12, K["SGI_TAK"])
    return max(K["GRUND"], rnd(sgi * K["FAKTOR"] * K["NIVA"] / 365))


def fp(lon, dv=7, ks=K["SNITT_KS"]):
    """Python-referens – samma beräkning som sidans JS.
    lon = månadslön före skatt, dv = dagar med föräldrapenning per vecka, ks = kommunalskatt i procent.
    Räknar som att man är ledig på heltid utan lön och har samma inkomst hela året."""
    d = dag(lon)
    dagar_ar = dv * 365 / 7
    brutto_ar = d * dagar_ar
    netto_ar = T.skatt_ar(brutto_ar, kommunalskatt=ks, arbetsinkomst=0)["netto"]
    lon_netto = T.skatt_ar(lon * 12, kommunalskatt=ks)["netto"] / 12
    return {
        "dag": d,
        "dag_netto": rnd(netto_ar / dagar_ar),
        "man": r10(brutto_ar / 12),
        "man_netto": r10(netto_ar / 12),
        "lon_netto": r10(lon_netto),
    }


assert dag(10 ** 6) == K["MAX"], "SGI-taket ger inte Försäkringskassans maxbelopp"

EX = [(lon, fp(lon)) for lon in (25000, 35000, 45000, 60000)]
MAXF = fp(60000)
TAK_MAN = rnd(K["SGI_TAK"] / 12)
P35 = fp(35000)

FAQ = [
    ("Vad är maxtaket för föräldrapenning 2026?",
     f"Högst {fmt(K['MAX'])} kr per dag före skatt. Taket kommer från att SGI räknas på högst 10 prisbasbelopp, "
     f"{fmt(K['SGI_TAK'])} kr per år eller ca {fmt(TAK_MAN)} kr i månaden. Tar du ut föräldrapenning alla sju dagar i veckan "
     f"blir maxbeloppet ca {fmt(MAXF['man'])} kr i månaden före skatt och ca {fmt(MAXF['man_netto'])} kr efter skatt med genomsnittlig kommunalskatt."),
    ("Vad är max SGI 2026?",
     f"{fmt(K['SGI_TAK'])} kr per år, alltså 10 prisbasbelopp à {fmt(K['PBB'])} kr. Det motsvarar en månadslön på ca {fmt(TAK_MAN)} kr. "
     "Har du högre lön än så blir föräldrapenningen inte högre."),
    ("Hur mycket föräldrapenning får jag?",
     f"På sjukpenningnivå får du knappt 80 procent av lönen: SGI × 0,97 × 80 % ÷ 365 per dag. Med 35 000 kr i månadslön blir det "
     f"{fmt(P35['dag'])} kr per dag före skatt. Tar du ut sju dagar i veckan blir det ca {fmt(P35['man'])} kr i månaden före skatt "
     f"och ca {fmt(P35['man_netto'])} kr efter skatt."),
    ("Hur räknar man ut SGI för föräldrapenning?",
     "För de flesta anställda är SGI samma som årslönen, alltså månadslönen × 12, upp till taket på "
     f"{fmt(K['SGI_TAK'])} kr. Är du föräldraledig med ett barn under 1 år är din SGI skyddad. Försäkringskassan fastställer din SGI."),
    ("Vad är sjukpenningnivå?",
     f"Sjukpenningnivå betyder att föräldrapenningen räknas på din inkomst, som sjukpenningen. Av de {K['DAGAR']} dagarna är "
     f"{K['DAGAR_SPN']} på sjukpenningnivå, mellan {K['GRUND']} och {fmt(K['MAX'])} kr per dag. De andra {K['DAGAR_LAG']} dagarna är "
     f"på lägstanivå, {K['LAGSTA']} kr per dag för alla."),
    ("Hur mycket är föräldrapenningtillägget?",
     "Det beror på ditt kollektivavtal. Föräldrapenningtillägg är ett tillägg till föräldrapenningen som du kan ha via kollektivavtalet "
     "på din arbetsplats, och hur mycket och hur många dagar det gäller står i avtalet. Fråga din arbetsgivare eller ditt fack. "
     "Kalkylatorn räknar inte med tillägget."),
    ("Är föräldrapenning skattepliktig?",
     "Ja. Föräldrapenning beskattas som inkomst men ger inget jobbskatteavdrag. Därför betalar du mer skatt på föräldrapenning än "
     "på lika mycket i lön. Kalkylatorn räknar med det."),
    ("Hur många dagar föräldrapenning får man?",
     f"{K['DAGAR']} dagar per barn som föräldrarna delar på. {K['RESERV']} dagar på sjukpenningnivå per förälder är reserverade och kan "
     "inte föras över till den andra föräldern. Du kan också ta ut del av en dag, till exempel en halv eller en fjärdedels dag."),
]

CHEV = S.ICON_CHEV


def tile(label, value, sub=""):
    s = f'<small class="gk-hint" style="display:block;margin-top:2px">{sub}</small>' if sub else ""
    return f'<div class="gk-tile"><span>{label}</span><strong>{value}</strong>{s}</div>'


def page():
    with open(os.path.join(ROOT, "data", "kommunalskatt-2026.json"), encoding="utf-8") as f:
        kommuner = json.load(f)["kommuner"]
    opts = '<option value="32.38">Rikssnitt – 32,38 %</option>' + "".join(
        f'<option value="{v}">{S.e(n)} – {str(v).replace(".", ",")} %</option>' for n, v in kommuner)

    title = plain(f"Föräldrapenning 2026: maxtak {fmt(K['MAX'])} kr/dag | GratisKalkyl")
    desc = plain(f"Maxtaket för föräldrapenning 2026 är {fmt(K['MAX'])} kr/dag (max SGI {fmt(K['SGI_TAK'])} kr). "
                 "Räkna ut din föräldrapenning per dag och månad efter skatt.")
    crumbs = [("Hem", "/"), ("Familj & trygghet", "/familj-och-trygghet"), ("Föräldrapenning", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Föräldrapenningkalkylator 2026",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Familj & trygghet", "item": S.SITE + "/familj-och-trygghet"},
            {"@type": "ListItem", "position": 3, "name": "Föräldrapenningkalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    ex_rows = "".join(
        f"<tr><td>{fmt(l)} kr</td><td>{fmt(r['dag'])} kr</td><td>{fmt(r['man'])} kr</td>"
        f"<td>{fmt(r['man_netto'])} kr</td><td>{fmt(r['lon_netto'])} kr</td></tr>"
        for l, r in EX)
    max_tiles = (
        tile("Högsta föräldrapenning", f"{fmt(K['MAX'])} kr", "Per dag före skatt") +
        tile("Max SGI 2026", f"{fmt(K['SGI_TAK'])} kr", f"Per år = 10 × prisbasbeloppet {fmt(K['PBB'])} kr") +
        tile("Taket nås vid lön", f"{fmt(TAK_MAN)} kr", "Per månad. Mer lön ger inte mer föräldrapenning") +
        tile("Max per månad", f"{fmt(MAXF['man'])} kr", f"Före skatt, 7 dagar/vecka. Ca {fmt(MAXF['man_netto'])} kr efter skatt"))

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Föräldrapenningkalkylator 2026</div>
<h1>Hur mycket får du i föräldrapenning?</h1>
<p class="gk-lead">Knappt 80 procent av lönen, högst {fmt(K['MAX'])} kr per dag 2026 – se vad du får per dag och månad efter skatt.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Max SGI {fmt(K['SGI_TAK'])} kr · Källa: <a href="{SRC['belopp']}" target="_blank" rel="noopener">Försäkringskassan</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="fpform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="lon">Din lön per månad före skatt</label>
<div class="gk-input"><input id="lon" inputmode="numeric" autocomplete="off" value="35 000"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Exempel: 35 000 kr. Skriv in din egen lön.</span>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur många dagar i veckan tar du ut?</legend>
<div class="gk-seg" style="--n:4" id="dv" role="group" aria-label="Dagar med föräldrapenning per vecka">
<button type="button" data-v="7" aria-pressed="true">7<small>dagar</small></button>
<button type="button" data-v="5" aria-pressed="false">5<small>mån–fre</small></button>
<button type="button" data-v="4" aria-pressed="false">4<small>dagar</small></button>
<button type="button" data-v="3" aria-pressed="false">3<small>dagar</small></button>
</div>
<span class="gk-hint" style="display:block;margin-top:6px">Vi räknar som att du är ledig på heltid utan lön. Färre dagar i veckan = lägre belopp, men dagarna räcker längre.</span>
</fieldset>

<div class="gk-field">
<label for="kommun">Din kommun</label>
<div class="gk-input"><select id="kommun">{opts}</select></div>
<span class="gk-hint">Styr skatten. Kommunal- och regionskatt 2026.</span>
</div>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:12px" aria-labelledby="maxH">
<h2 id="maxH" style="font-size:22px">Maxtak 2026: {fmt(K['MAX'])} kr per dag</h2>
<p class="gk-hint">Föräldrapenningen räknas på högst 10 prisbasbelopp. Tjänar du mer blir den inte högre.</p>
<div class="gk-tiles">{max_tiles}</div>
<p class="gk-hint">Lägst {K['GRUND']} kr per dag på sjukpenningnivå (grundnivå). Lägstanivå: {K['LAGSTA']} kr per dag. Efter skatt med genomsnittlig kommunalskatt.</p>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Föräldrapenning efter skatt</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån</span></div>
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
<a class="gk-linkcard" href="{SRC['fp']}" target="_blank" rel="noopener"><span>Ansök om föräldrapenning<small>Regler och ansökan hos Försäkringskassan</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/rakna-ut-foraldrapenning-2026"><span>Guide: Räkna ut föräldrapenning 2026<small>Steg för steg med exempel</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/barnbidragskalkylator"><span>Barnbidragskalkylator<small>Barnbidrag och flerbarnstillägg</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknas föräldrapenningen ut</h2>
<p>Föräldrapenningen räknas på din <strong>sjukpenninggrundande inkomst (SGI)</strong>. För de flesta anställda är SGI månadslönen × 12.</p>
<p><strong>Föräldrapenning per dag = SGI × 0,97 × 80 % ÷ 365</strong></p>
<p>SGI kan som mest vara {fmt(K['SGI_TAK'])} kr per år 2026. Därför är föräldrapenningen högst <strong>{fmt(K['MAX'])} kr per dag</strong>. Så här blir det för några löner, sju dagar i veckan och genomsnittlig kommunalskatt:</p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight">
<thead><tr><th scope="col">Lön/mån</th><th scope="col">Per dag</th><th scope="col">Före skatt/mån</th><th scope="col">Efter skatt/mån</th><th scope="col">Nettolön</th></tr></thead>
<tbody>{ex_rows}</tbody></table></div>

<h2>Sjukpenningnivå, grundnivå och lägstanivå</h2>
<p>Ni får {K['DAGAR']} dagar per barn. <strong>{K['DAGAR_SPN']} dagar är på sjukpenningnivå</strong>, mellan {K['GRUND']} och {fmt(K['MAX'])} kr per dag. <strong>{K['DAGAR_LAG']} dagar är på lägstanivå</strong>, {K['LAGSTA']} kr per dag. {K['RESERV']} dagar på sjukpenningnivå per förälder kan inte föras över.</p>
<p>För att få sjukpenningnivå behöver du ha haft en SGI som motsvarar minst {fmt(K['VILLKOR_MAN'])} kr i månaden i minst {K['VILLKOR_DAGAR']} dagar före barnets beräknade födelse. Annars får du grundnivån, {K['GRUND']} kr per dag.</p>

<h2>Skatt på föräldrapenning</h2>
<p>Föräldrapenning är skattepliktig men ger inget jobbskatteavdrag. Du betalar alltså mer skatt på föräldrapenningen än på samma belopp i lön.</p>

<h2>Lön över taket och föräldrapenningtillägg</h2>
<p>Tjänar du mer än ca {fmt(TAK_MAN)} kr i månaden ersätter föräldrapenningen bara en del av lönen. Har din arbetsplats kollektivavtal kan du få <strong>föräldrapenningtillägg</strong> utöver föräldrapenningen. Hur mycket och hur länge beror på avtalet – fråga din arbetsgivare eller ditt fack.</p>

<h2>Vanliga frågor om föräldrapenning</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['belopp']}" target="_blank" rel="noopener">Försäkringskassan – Aktuella belopp 2026</a> (högst {fmt(K['MAX'])} kr/dag, lägstanivå {K['LAGSTA']} kr, SGI högst {fmt(K['SGI_TAK'])} kr, prisbasbelopp {fmt(K['PBB'])} kr)</li>
<li><a href="{SRC['fp']}" target="_blank" rel="noopener">Försäkringskassan – Föräldrapenning</a> ({K['DAGAR']}/{K['DAGAR_SPN']}/{K['DAGAR_LAG']} dagar, {K['GRUND']}–{fmt(K['MAX'])} kr, {K['VILLKOR_DAGAR']} dagar och {fmt(K['VILLKOR_MAN'])} kr, reserverade dagar)</li>
<li><a href="{SRC['sgi']}" target="_blank" rel="noopener">Försäkringskassan – SGI</a> (månadslön × 12, skyddad SGI under barnets första år)</li>
<li><a href="{SRC['helg']}" target="_blank" rel="noopener">Försäkringskassan – Nya regler för föräldrapenning under helger</a> (från 1 april 2025)</li>
<li><a href="{SRC['sfb']}" target="_blank" rel="noopener">Socialförsäkringsbalken 12 kap. 22–24 §§ och 28 kap. 7 §</a> (beräkning som sjukpenning, grundnivå {K['GRUND']} kr, lägstanivå {K['LAGSTA']} kr)</li>
<li><a href="{SRC['skv']}" target="_blank" rel="noopener">Skatteverket – Jobbskatteavdrag</a> (föräldrapenning ger inget jobbskatteavdrag)</li>
<li><a href="{SRC['fpt']}" target="_blank" rel="noopener">Afa Försäkring – Föräldrapenning och föräldrapenningtillägg</a> (tillägg via kollektivavtalet)</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/sjukpenningkalkylator"><span>Sjukpenningkalkylator<small>Samma SGI och tak som föräldrapenningen</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/loneraknare"><span>Löneräknare<small>Se din vanliga nettolön i detalj</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Hushållsbudget<small>Går budgeten ihop under föräldraledigheten?</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-fp" type="application/json">{json.dumps(K)}</script>
<script defer src="/assets/skatt2026.js?v=20261001"></script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Hur mycket får du i föräldrapenning? Kalkylator 2026", jsonld=ld)
            + S.header() + body
            + S.footer("Föräldrapenningen är en uppskattning – Försäkringskassan beslutar om din SGI och ersättning."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-fp').textContent);
  var T = window.GKSkatt2026;
  var $ = function (id) { return document.getElementById(id); };
  var r10 = function (v) { return Math.round(v / 10) * 10; };
  var kr = function (v) { return GK.fmt(v, 0) + ' kr'; };
  var st = { dv: 7 };

  $('dv').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    $('dv').querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    st.dv = +b.getAttribute('data-v'); calc();
  });
  $('lon').addEventListener('input', calc);
  $('kommun').addEventListener('change', calc);
  GK.groupInput($('lon'));

  function tile(l, v, s, id) { return '<div class="gk-tile"' + (id ? ' id="' + id + '"' : '') + '><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }

  /* Samma beräkning som fp() i scripts/build_foraldrapenning.py */
  function fp(L, dv, ks) {
    var sgi = Math.min(L * 12, C.SGI_TAK);
    var raw = Math.round(sgi * C.FAKTOR * C.NIVA / 365);
    var d = Math.max(C.GRUND, raw);
    var dagarAr = dv * 365 / 7;
    var bruttoAr = d * dagarAr;
    var nettoAr = T.skattAr(bruttoAr, { arbetsinkomst: 0, kommunalskatt: ks }).netto;
    var lonNetto = T.skattAr(L * 12, { kommunalskatt: ks }).netto / 12;
    return { sgi: sgi, raw: raw, dag: d, dagNetto: Math.round(nettoAr / dagarAr), man: r10(bruttoAr / 12),
             manNetto: r10(nettoAr / 12), lonNetto: r10(lonNetto), dagarMan: dagarAr / 12 };
  }

  function calc() {
    var L = GK.parse($('lon').value), ks = +$('kommun').value, dv = st.dv;
    if (!isFinite(L) || L < 1000) {
      $('resBig').textContent = '–'; $('resSub').textContent = 'Fyll i din lön per månad före skatt.';
      ['tiles', 'verdict', 'how'].forEach(function (id) { $(id).innerHTML = ''; });
      return;
    }
    var r = fp(L, dv, ks);
    var tapp = r.lonNetto - r.manNetto, pct = r.lonNetto > 0 ? r.manNetto / r.lonNetto * 100 : 0;

    $('resBig').textContent = GK.fmt(r.manNetto, 0);
    $('resSub').textContent = 'Med ' + dv + ' dagar i veckan (ca ' + GK.fmt(r.dagarMan, 0) + ' dagar i månaden). Din vanliga nettolön är ' + kr(r.lonNetto) +
      ' – du får ' + GK.fmt(pct, 0) + ' % av den och tappar ca ' + kr(Math.max(0, tapp)) + ' i månaden.';
    $('tiles').innerHTML =
      tile('Per dag före skatt', kr(r.dag), 'Sjukpenningnivå', 'tDag') +
      tile('Per dag efter skatt', kr(r.dagNetto), 'Inget jobbskatteavdrag', 'tDagNetto') +
      tile('Per månad före skatt', kr(r.man), dv + ' dagar/vecka', 'tMan') +
      tile('Vanlig nettolön', kr(r.lonNetto), 'Lön ' + GK.fmt(L, 0) + ' kr före skatt', 'tLon');

    var v;
    if (L * 12 > C.SGI_TAK) {
      v = verdict('warn', 'Din lön är över taket', 'Föräldrapenningen räknas bara på ' + GK.fmt(C.SGI_TAK, 0) + ' kr per år (ca ' + GK.fmt(Math.round(C.SGI_TAK / 12), 0) +
        ' kr i månaden), så du får maxbeloppet ' + kr(C.MAX) + ' per dag. För lönen över taket får du inget från Försäkringskassan – kolla om ditt kollektivavtal ger föräldrapenningtillägg.');
    } else if (r.raw <= C.GRUND) {
      v = verdict('info', 'Du får grundnivån, ' + C.GRUND + ' kr per dag', 'Med din lön blir föräldrapenningen inte högre än grundnivån. ' + C.GRUND +
        ' kr per dag är det lägsta du får på sjukpenningnivå. Maxtaket är ' + kr(C.MAX) + ' per dag.');
    } else if (r.dag >= C.MAX) {
      v = verdict('good', 'Du får maxbeloppet, ' + kr(C.MAX) + ' per dag', 'Din lön ligger precis vid taket på ' + GK.fmt(C.SGI_TAK, 0) +
        ' kr per år. Mer lön ger inte mer föräldrapenning. Har du kollektivavtal kan du dessutom få föräldrapenningtillägg, som inte är med här.');
    } else {
      v = verdict('good', 'Under taket – du får ' + GK.fmt(r.dag * 365 / 12 / L * 100, 1) + ' % av lönen före skatt', 'Maxtaket är ' + kr(C.MAX) + ' per dag – du ligger ' +
        kr(C.MAX - r.dag) + ' under. Har du kollektivavtal kan du dessutom få föräldrapenningtillägg, som inte är med här.');
    }
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p>SGI = din lön × 12, högst ' + GK.fmt(C.SGI_TAK, 0) + ' kr: ' + GK.fmt(r.sgi, 0) + ' kr. Föräldrapenning per dag = ' + GK.fmt(r.sgi, 0) + ' × 0,97 × 80 % ÷ 365 = ' +
        GK.fmt(r.raw, 0) + ' kr' + (r.raw < C.GRUND ? ', höjt till grundnivån ' + C.GRUND + ' kr' : '') + '.</p>' +
      '<p>' + dv + ' dagar i veckan = ' + GK.fmt(r.dagarMan, 1) + ' dagar i månaden: ' + GK.fmt(r.dag, 0) + ' × ' + dv + ' × 365 ÷ 7 ÷ 12 = ' + kr(r.man) + ' före skatt.' +
        (dv === 7 ? ' Jobbar du måndag–fredag måste du ta ut föräldrapenning dagen före eller efter helgen för att få det för lördag och söndag.' : '') + '</p>' +
      '<p>Skatten räknas med samma regler som Skatteverkets skattetabeller 2026 och ' + GK.fmt(ks, 2) + ' % kommunalskatt. Föräldrapenning ger inget jobbskatteavdrag, lön gör det. Vi räknar som om du har samma inkomst hela året och ingen lön under ledigheten.</p>' +
      '<p>Föräldrapenningtillägg från kollektivavtal är inte med. Försäkringskassan fastställer din SGI.</p>';
  }
  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "foraldrapenning.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    cases = [(35000, 7, 32.38), (25000, 5, 32.38), (45000, 3, 31.71), (60000, 7, 35.65), (8000, 4, 32.38), (49333, 5, 28.93)]
    for lon, dv, ks in cases:
        r = fp(lon, dv, ks)
        print(f"  lön {lon}, {dv} d/v, ks {ks}: {r['dag']} kr/dag ({r['dag_netto']} netto), "
              f"{r['man']} kr/mån brutto, {r['man_netto']} netto, nettolön {r['lon_netto']}")


if __name__ == "__main__":
    main()
