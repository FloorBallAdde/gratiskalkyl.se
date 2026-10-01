#!/usr/bin/env python3
"""Bygger kalkylatorer/sjukpenningkalkylator.html i den nya designen.

Regler och belopp 2026 (källor i SRC och på sidan):
  Sjukpenning = SGI × 0,97 × 80 % / 365 per kalenderdag, högst 1 259 kr/dag (SGI-tak 10 pbb = 592 000 kr).
  Efter 364 dagar inom 450 dagar: fortsättningsnivå 75 %, högst 1 180 kr/dag. Lägsta SGI 14 200 kr.
  Dag 1–14: sjuklön 80 % från arbetsgivaren minus karensavdrag (20 % av veckosjuklönen).
  Skatt: assets/skatt2026.js (samma modell som Skatteverkets tabeller). Sjukpenning ger inget jobbskatteavdrag.

    python3 scripts/build_sjukpenning.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import skatt2026 as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/sjukpenningkalkylator"
UPDATED = "1 oktober 2026"

K = {"AR": 2026, "PBB": 59200, "SGI_TAK": 592000, "SGI_MIN": 14200, "MAX80": 1259, "MAX75": 1180}

SRC = {
    "belopp": "https://www.forsakringskassan.se/privatperson/e-tjanster-blanketter-och-informationsmaterial/aktuella-belopp",
    "anstalld": "https://www.forsakringskassan.se/privatperson/sjuk/anstalld/sjukpenning-for-anstallda",
    "sgi": "https://www.forsakringskassan.se/privatperson/sjukpenninggrundande-inkomst-sgi",
    "sjuklon": "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/lag-19911047-om-sjuklon_sfs-1991-1047/",
    "sfb": "https://lagen.nu/2010:110",
}


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def dag80(lon):
    return round(min(lon * 12, K["SGI_TAK"]) * 0.97 * 0.80 / 365)


def netto_sjuk(lon):
    """Netto per månad om man är sjukskriven 100 % hela året (sjukpenning, inget jobbskatteavdrag)."""
    sp = dag80(lon) * 365
    return T.skatt_ar(sp, arbetsinkomst=0)["netto"] / 12


EX = []
for lon in (25000, 35000, 45000, 60000):
    d = dag80(lon)
    EX.append((lon, d, round(d * 365 / 12, -1), round(netto_sjuk(lon), -1), round(T.netto_manad(lon), -1)))

FAQ = [
    ("Hur mycket får man i sjukpenning?",
     f"Sjukpenningen är knappt 80 procent av din lön: Försäkringskassan räknar din sjukpenninggrundande inkomst (SGI) × 0,97 × 80 % "
     f"och delar med 365. Med 35 000 kr i månadslön blir det {fmt(EX[1][1])} kr per dag före skatt, ungefär {fmt(EX[1][2])} kr i månaden. "
     f"Sjukpenningen betalas för alla dagar i veckan, även helger. Högsta beloppet 2026 är 1 259 kr per dag."),
    ("Vad är max sjukpenning 2026?",
     "Högst 1 259 kr per dag före skatt, eftersom SGI är begränsad till 10 prisbasbelopp = 592 000 kr per år (ca 49 300 kr i månaden). "
     "Efter 364 dagar sänks ersättningen till 75 procent, högst 1 180 kr per dag. Tjänar du mer än taket täcker sjukpenningen bara en del av lönen."),
    ("Varför räknar Försäkringskassan med 0,97?",
     "Det är en omräkningsfaktor i socialförsäkringsbalken. Sjukpenningen är 80 procent av SGI efter att SGI har multiplicerats med 0,97 – "
     "i praktiken 77,6 procent av SGI. Formeln är SGI × 0,97 × 0,80 ÷ 365 = sjukpenning per dag."),
    ("Vad får man de första 14 dagarna?",
     "Då betalar arbetsgivaren sjuklön: 80 procent av lönen för de dagar du skulle ha jobbat, minus ett karensavdrag. Karensavdraget är "
     "20 procent av en genomsnittlig veckas sjuklön. Jobbar du heltid måndag–fredag motsvarar det ungefär en dags lön. Från dag 15 betalar "
     "Försäkringskassan sjukpenning."),
    ("Får man sjukpenning för helger?",
     "Ja. Sjukpenningen från Försäkringskassan betalas för alla kalenderdagar, även lördagar och söndagar. Det är därför formeln delar "
     "med 365. Sjuklönen från arbetsgivaren dag 1–14 betalas däremot bara för de dagar du skulle ha arbetat."),
    ("Hur länge kan man få sjukpenning?",
     "Sjukpenning på normalnivå (80 procent) kan du få i högst 364 dagar inom en period på 450 dagar. Därefter kan du få sjukpenning på "
     "fortsättningsnivå, 75 procent, högst 1 180 kr per dag 2026."),
    ("Är sjukpenning skattepliktig?",
     "Ja. Sjukpenning beskattas som inkomst, men ger inget jobbskatteavdrag. Därför betalar du mer skatt på sjukpenning än på lika mycket i lön. "
     "Kalkylatorn räknar med det."),
    ("Kan man vara sjukskriven på deltid?",
     "Ja. Du kan få sjukpenning på 25, 50, 75 eller 100 procent. Är du sjukskriven på deltid får du lön för den del du arbetar och "
     "sjukpenning för resten."),
]

CHEV = S.ICON_CHEV


def page():
    with open(os.path.join(ROOT, "data", "kommunalskatt-2026.json"), encoding="utf-8") as f:
        kommuner = json.load(f)["kommuner"]
    opts = '<option value="32.38">Rikssnitt – 32,38 %</option>' + "".join(
        f'<option value="{v}">{S.e(n)} – {str(v).replace(".", ",")} %</option>' for n, v in kommuner)

    title = "Sjukpenning 2026: räkna ut vad du får | GratisKalkyl"
    desc = ("Hur mycket får du i sjukpenning 2026? Räkna ut sjukpenning per dag och månad efter skatt, sjuklön dag 1–14 "
            "och vad du tappar mot lönen.")
    crumbs = [("Hem", "/"), ("Familj & trygghet", "/familj-och-trygghet"), ("Sjukpenning", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Sjukpenningkalkylator 2026",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Familj & trygghet", "item": S.SITE + "/familj-och-trygghet"},
            {"@type": "ListItem", "position": 3, "name": "Sjukpenningkalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    ex_rows = "".join(
        f"<tr><td>{fmt(l)} kr</td><td>{fmt(d)} kr</td><td>{fmt(m)} kr</td><td>{fmt(n)} kr</td><td>{fmt(nl)} kr</td></tr>"
        for l, d, m, n, nl in EX)

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Sjukpenningkalkylator 2026</div>
<h1>Hur mycket får du i sjukpenning?</h1>
<p class="gk-lead">Se vad du får per månad efter skatt om du blir sjukskriven – och vad du tappar jämfört med lönen.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Högst 1 259 kr/dag 2026 · Källa: <a href="{SRC['belopp']}" target="_blank" rel="noopener">Försäkringskassan</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="spform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="lon">Din lön per månad före skatt</label>
<div class="gk-input"><input id="lon" inputmode="numeric" autocomplete="off" value="35 000"><span class="unit">kr/mån</span></div>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur mycket är du sjukskriven?</legend>
<div class="gk-seg" style="--n:4" id="grad" role="group" aria-label="Sjukskrivningsgrad">
<button type="button" data-v="100" aria-pressed="true">100 %<small>heltid</small></button>
<button type="button" data-v="75" aria-pressed="false">75 %</button>
<button type="button" data-v="50" aria-pressed="false">50 %</button>
<button type="button" data-v="25" aria-pressed="false">25 %</button>
</div>
</fieldset>

<div class="gk-field">
<label for="kommun">Din kommun</label>
<div class="gk-input"><select id="kommun">{opts}</select></div>
<span class="gk-hint">Styr skatten. Kommunal- och regionskatt 2026.</span>
</div>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:12px" aria-labelledby="kortH">
<h2 id="kortH" style="font-size:22px">Sjuk kortare tid än två veckor?</h2>
<p class="gk-hint">Dag 1–14 betalar arbetsgivaren sjuklön, 80 % av lönen minus ett karensavdrag. Så mycket mindre får du ut:</p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="kortTable"></table></div>
<p class="gk-hint" id="kortNote"></p>
<a class="gk-linkcard" href="/kalkylatorer/karensavdragskalkylator"><span>Räkna exakt på karensavdraget<small>Med ditt eget schema och antal sjukdagar</small></span>{CHEV}</a>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Du får ungefär efter skatt</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-o4" style="gap:12px" aria-labelledby="langH">
<h2 id="langH" style="font-size:22px">Efter ett år sjukskriven</h2>
<p class="gk-hint">Efter 364 dagar sänks sjukpenningen från 80 till 75 procent (högst 1 180 kr per dag).</p>
<div class="gk-tiles" id="langTiles"></div>
</section>

<section class="gk-card gk-stack gk-no-print gk-o5" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="{SRC['anstalld']}" target="_blank" rel="noopener"><span>Ansök om sjukpenning hos Försäkringskassan<small>Från dag 15 – din arbetsgivare anmäler först</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/loneraknare"><span>Löneräknare<small>Se din vanliga nettolön i detalj</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Hushållsbudget<small>Går budgeten ihop med sjukpenning?</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknas sjukpenningen ut</h2>
<p>Från dag 15 betalar Försäkringskassan sjukpenning. Den räknas på din <strong>sjukpenninggrundande inkomst (SGI)</strong> – ungefär din årslön – och betalas för alla dagar i veckan, även helger:</p>
<p><strong>Sjukpenning per dag = SGI × 0,97 × 80 % ÷ 365</strong></p>
<p>SGI kan som mest vara 10 prisbasbelopp, <strong>592 000 kr</strong> per år 2026 (ca 49 300 kr i månaden). Därför är sjukpenningen högst <strong>1 259 kr per dag</strong>. Så här blir det för några vanliga löner vid heltidssjukskrivning, med genomsnittlig kommunalskatt:</p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight">
<thead><tr><th scope="col">Lön/mån</th><th scope="col">Per dag</th><th scope="col">Per mån före skatt</th><th scope="col">Per mån efter skatt</th><th scope="col">Vanlig nettolön</th></tr></thead>
<tbody>{ex_rows}</tbody></table></div>
<p>Sjukpenningen är skattepliktig men ger inget jobbskatteavdrag. Du betalar alltså mer skatt på sjukpenningen än på samma belopp i lön – det är därför skillnaden efter skatt blir större än 20 procent.</p>

<h2>Dag 1–14: sjuklön och karensavdrag</h2>
<p>De första 14 dagarna betalar din arbetsgivare <strong>sjuklön</strong> med 80 procent av lönen för de dagar du skulle ha arbetat. Från sjuklönen dras ett <strong>karensavdrag</strong> på 20 procent av en genomsnittlig veckas sjuklön. Jobbar du heltid måndag–fredag motsvarar det ungefär en dags lön. Från dag 8 behöver du normalt ett läkarintyg. Är du sjuk längre än 14 dagar anmäler arbetsgivaren det till Försäkringskassan, och sedan ansöker du själv om sjukpenning.</p>

<h2>Efter ett år: fortsättningsnivå</h2>
<p>Sjukpenning på normalnivå, 80 procent, kan du få i högst 364 dagar inom en period på 450 dagar. Därefter kan du få sjukpenning på <strong>fortsättningsnivå, 75 procent</strong> – högst 1 180 kr per dag 2026.</p>

<h2>Tjänar du mer än taket?</h2>
<p>Har du högre lön än ca 49 300 kr i månaden ersätter sjukpenningen bara en del av lönen. Har din arbetsplats kollektivavtal kan du få ett tillägg genom avtalets sjukförsäkring, och en privat sjukförsäkring kan täcka mer. Hur mycket beror på avtalet – fråga din arbetsgivare eller ditt fack. Fackets inkomstförsäkring gäller vid arbetslöshet, inte vid sjukdom.</p>

<h2>Vanliga frågor om sjukpenning</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['belopp']}" target="_blank" rel="noopener">Försäkringskassan – Aktuella belopp 2026</a> (1 259 / 1 180 kr per dag, SGI 592 000 kr)</li>
<li><a href="{SRC['anstalld']}" target="_blank" rel="noopener">Försäkringskassan – Sjukpenning för anställda</a> (dag 15, 25/50/75/100 %)</li>
<li><a href="{SRC['sjuklon']}" target="_blank" rel="noopener">Lag om sjuklön (1991:1047)</a> (80 %, karensavdrag, läkarintyg)</li>
<li><a href="{SRC['sfb']}" target="_blank" rel="noopener">Socialförsäkringsbalken 27 kap.</a> (364 dagar inom 450)</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/artiklar/rakna-ut-sjuklon-2026"><span>Guide: Räkna ut sjuklön 2026<small>Formel och exempel för månadslön och timlön</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/karensavdragskalkylator"><span>Karensavdragskalkylator<small>Vad kostar en sjukdag?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/foraldrapenning"><span>Föräldrapenning<small>Samma SGI och tak som sjukpenningen</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/akassa-kalkylator"><span>A-kassa<small>Ersättning om du blir arbetslös</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-sp" type="application/json">{json.dumps(K)}</script>
<script defer src="/assets/skatt2026.js?v=20261001"></script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Hur mycket får du i sjukpenning? Kalkylator 2026", jsonld=ld)
            + S.header() + body + S.footer("Sjukpenningen är en uppskattning – Försäkringskassan beslutar om din SGI och ersättning."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-sp').textContent);
  var T = window.GKSkatt2026;
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var st = { grad: 100 };

  $('grad').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    $('grad').querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    st.grad = +b.getAttribute('data-v'); calc();
  });
  $('lon').addEventListener('input', calc);
  $('kommun').addEventListener('change', calc);
  GK.groupInput($('lon'));

  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function netto(arslon, sjuk, ks) { return T.skattAr(arslon + sjuk, { arbetsinkomst: arslon, kommunalskatt: ks }).netto; }

  function calc() {
    var L = GK.parse($('lon').value), ks = +$('kommun').value, g = st.grad / 100;
    if (!isFinite(L) || L < 1000) {
      $('resBig').textContent = '–'; $('resSub').textContent = 'Fyll i din lön per månad före skatt.';
      ['tiles', 'verdict', 'how', 'langTiles', 'kortTable', 'kortNote'].forEach(function (id) { $(id).innerHTML = ''; });
      return;
    }
    var sgi = Math.min(L * 12, C.SGI_TAK);
    var d80 = L * 12 < C.SGI_MIN ? 0 : Math.round(sgi * 0.97 * 0.80 / 365);
    var d75 = L * 12 < C.SGI_MIN ? 0 : Math.round(sgi * 0.97 * 0.75 / 365);
    var lonDel = L * 12 * (1 - g);                    /* lön för den del du arbetar, per år */
    var n0 = netto(L * 12, 0, ks) / 12;               /* vanlig nettolön per månad */
    var n80 = netto(lonDel, d80 * g * 365, ks) / 12;  /* netto per månad som sjukskriven, dag 15+ */
    var n75 = netto(lonDel, d75 * g * 365, ks) / 12;
    var spMan = d80 * g * 365 / 12;
    var tapp = n0 - n80, pct = n0 > 0 ? n80 / n0 * 100 : 0;

    $('resLabel').textContent = g < 1 ? 'Lön + sjukpenning efter skatt, sjukskriven ' + st.grad + ' %' : 'Sjukpenning efter skatt';
    $('resBig').textContent = GK.fmt(Math.round(n80 / 10) * 10, 0);
    $('resSub').textContent = 'Från dag 15. Din vanliga nettolön är ' + kr(n0) + ' – du får ' + GK.fmt(pct, 0) + ' % av den och tappar ca ' + kr(tapp) + ' i månaden.';
    $('tiles').innerHTML =
      tile('Sjukpenning per dag', GK.fmt(Math.round(d80 * g), 0) + ' kr', 'Före skatt, alla dagar i veckan') +
      tile('Sjukpenning per månad', kr(spMan), 'Före skatt' + (g < 1 ? ', plus lön för ' + (100 - st.grad) + ' %' : '')) +
      tile('Vanlig nettolön', kr(n0), 'Lön ' + GK.fmt(L, 0) + ' kr före skatt') +
      tile('Du tappar per månad', kr(tapp), 'Efter skatt');

    var v = '';
    if (L * 12 < C.SGI_MIN) {
      v = verdict('info', 'För låg inkomst för sjukpenning', 'Din SGI måste vara minst ' + GK.fmt(C.SGI_MIN, 0) + ' kr per år (24 % av prisbasbeloppet) för att du ska kunna få sjukpenning.');
    } else if (L * 12 > C.SGI_TAK) {
      v = verdict('warn', 'Din lön är över taket', 'Sjukpenningen räknas bara på ' + GK.fmt(C.SGI_TAK, 0) + ' kr per år (ca ' + GK.fmt(Math.round(C.SGI_TAK / 12 / 100) * 100, 0) + ' kr i månaden). För resten av lönen får du inget från Försäkringskassan. Kolla om ditt kollektivavtal eller en sjukförsäkring ger ett tillägg.');
    } else {
      v = verdict('info', 'Kolla ditt kollektivavtal', 'Har din arbetsplats kollektivavtal kan du få ett tillägg utöver sjukpenningen. Det är inte med här.');
    }
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p>SGI = din årslön, högst ' + GK.fmt(C.SGI_TAK, 0) + ' kr: ' + GK.fmt(sgi, 0) + ' kr. Sjukpenning per dag = ' + GK.fmt(sgi, 0) + ' × 0,97 × 80 % ÷ 365 = ' + GK.fmt(d80, 0) + ' kr' + (g < 1 ? ', × ' + st.grad + ' % = ' + GK.fmt(Math.round(d80 * g), 0) + ' kr' : '') + '. Den betalas för alla dagar i veckan: × 365 ÷ 12 = ' + kr(spMan) + ' i månaden.</p>' +
      '<p>Skatten räknas med samma regler som Skatteverkets skattetabeller 2026 och ' + GK.fmt(ks, 2) + ' % kommunalskatt. Sjukpenning ger inget jobbskatteavdrag, lön gör det. Vi räknar som om du har samma inkomst hela året.</p>' +
      '<p>Kollektivavtalets tillägg och eventuell privat sjukförsäkring är inte med.</p>';

    $('langTiles').innerHTML =
      tile('Per dag före skatt', GK.fmt(Math.round(d75 * g), 0) + ' kr', '75 % i stället för 80 %') +
      tile('Per månad efter skatt', kr(n75), 'Ca ' + kr(n80 - n75) + ' mindre än första året');

    /* Kort sjukdom: heltid mån–fre, första sjukdagen en måndag */
    var dag = L * 12 / 260, karens = 0.2 * 0.8 * L * 12 / 52;
    var rows = [[1, '1 dag'], [3, '3 dagar'], [5, '1 vecka'], [10, '2 veckor']];
    var nAr = netto(L * 12, 0, ks);
    $('kortTable').innerHTML = '<thead><tr><th scope="col">Sjuk</th><th scope="col">Sjuklön</th><th scope="col">Du tappar</th></tr></thead><tbody>' +
      rows.map(function (r) {
        var full = r[0] * dag, sl = Math.max(0, 0.8 * full - karens), loss = full - sl;
        var lossNet = nAr - netto(L * 12 - loss, 0, ks);
        return '<tr><td>' + r[1] + '</td><td>' + kr(sl) + '</td><td><strong>' + kr(lossNet) + '</strong></td></tr>';
      }).join('') + '</tbody>';
    $('kortNote').textContent = 'Sjuklön före skatt. Du tappar = så mycket mindre du får ut efter skatt än om du hade jobbat. Heltid måndag–fredag. Karensavdraget är ' + kr(karens) + ' – ungefär en dags lön.';
  }
  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "sjukpenningkalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    for row in EX:
        print("  lön %s: %s kr/dag, %s kr/mån brutto, %s netto sjuk, %s netto lön" % row)


if __name__ == "__main__":
    main()
