#!/usr/bin/env python3
"""Bygger kalkylatorer/elkostnadskalkylator.html i den nya designen.

Siffrorna läggs in från data/elpriser.json. Månadsuppdateringen
(update_elpriser.py) byter sedan bara ut innehållet mellan markörerna.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import update_elpriser as U  # noqa: E402

ROOT = U.ROOT
PATH = "/kalkylatorer/elkostnadskalkylator"

FAQ = [
    ("Varifrån kommer siffrorna?",
     "Snittpriserna kommer från SCB:s och Energimyndighetens officiella statistik över elhandelspriser för nytecknade avtal. "
     "Den publiceras varje månad per elområde, avtalstyp och typ av hushåll. Vi hämtar de nya siffrorna automatiskt när de "
     "publiceras och visar alltid vilken månad de gäller. Elnätspriserna kommer från SCB:s statistik per den 1 januari och "
     "energiskatten från Skatteverket."),
    ("Vilket elområde tillhör jag?",
     "Sverige är indelat i fyra elområden: SE1 (Luleå) i norra Norrland, SE2 (Sundsvall) i södra Norrland, SE3 (Stockholm) "
     "i Mellansverige och SE4 (Malmö) i Sydsverige. Gränserna följer inte länsgränserna exakt. Ditt elområde står på din elfaktura."),
    ("Hur mycket el förbrukar ett vanligt hushåll?",
     "En lägenhet utan elvärme använder ofta 2 000–3 500 kWh per år och en villa utan elvärme 4 000–7 000 kWh. "
     "En villa med värmepump ligger ofta på 8 000–15 000 kWh och en villa med direktverkande el på 18 000–28 000 kWh. "
     "Din exakta förbrukning står på elfakturan eller hos ditt elnätsföretag."),
    ("Vad är skillnaden mellan rörligt och fast elpris?",
     "Med rörligt pris följer elpriset elbörsen och ändras varje månad (eller varje timme och kvart med tim- och kvartsprisavtal). "
     "Med fast pris är elpriset låst i 1–3 år. Rörligt har ofta varit billigare i snitt, men kan bli betydligt dyrare "
     "under kalla vintrar. Fast pris ger en förutsägbar räkning."),
    ("Vad är ett anvisat avtal?",
     "Om du flyttar in och inte väljer elhandlare får du ett anvisat avtal från den elhandlare som nätbolaget har utsett. "
     "Anvisat avtal är i regel dyrare än ett avtal du väljer själv. Du kan byta när som helst."),
    ("Vad ingår i min elkostnad?",
     "Elräkningen består av tre delar: elhandeln (själva elen, från din elhandlare), elnätet (överföringen, från ditt nätbolag) "
     "och skatter. Energiskatten är 36,0 öre/kWh exklusive moms 2026 och 25 procent moms läggs på allt. "
     "Bara elhandeln kan du påverka genom att byta avtal."),
    ("Vad är energiskatten på el 2026?",
     "Energiskatten är 36,0 öre per kWh exklusive moms från den 1 januari 2026, sänkt från 43,9 öre 2025. Inklusive moms blir "
     "det 45,0 öre. Hushåll i vissa kommuner i norra Sverige får ett avdrag på 9,6 öre och betalar 26,4 öre per kWh exklusive moms."),
]

CHEV = S.ICON_CHEV


def page(blocks):
    title = "Elkostnadskalkylator 2026 – vad borde elen kosta? | SE1–SE4"
    desc = ("Räkna ut din elkostnad och se om du betalar för mycket. Jämför ditt elpris med SCB:s snittpris för nya "
            "avtal i ditt elområde – uppdateras varje månad.")
    crumbs = [("Hem", "/"), ("Bil & energi", "/bil-och-energi"), ("Elkostnad", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Elkostnadskalkylator – vad borde elen kosta?",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv",
         "description": desc},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Elkostnadskalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Elkostnadskalkylator 2026</div>
<h1>Vad borde elen kosta?</h1>
<p class="gk-lead">Se vad elen kostar för ditt hushåll, om du betalar mer än andra och vilket avtal som varit billigast.</p>
<p class="gk-meta"><!--ELMETA:START-->{blocks['ELMETA']}<!--ELMETA:END--></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="elform" novalidate onsubmit="return false">
<fieldset class="gk-fieldset">
<legend class="gk-legend">Elområde</legend>
<div class="gk-seg" style="--n:4" id="omr" role="group" aria-label="Elområde">
<button type="button" data-v="SE1" aria-pressed="false">SE1<small>Luleå</small></button>
<button type="button" data-v="SE2" aria-pressed="false">SE2<small>Sundsvall</small></button>
<button type="button" data-v="SE3" aria-pressed="true">SE3<small>Stockholm</small></button>
<button type="button" data-v="SE4" aria-pressed="false">SE4<small>Malmö</small></button>
</div>
<span class="gk-hint">Står på din elfaktura.</span>
</fieldset>

<div class="gk-field">
<label for="kwh">Förbrukning per år</label>
<div class="gk-input"><input id="kwh" inputmode="numeric" autocomplete="off" value="5 000"><span class="unit">kWh/år</span></div>
<div class="gk-seg" style="--n:3" id="kwhq" role="group" aria-label="Vanlig förbrukning">
<button type="button" data-v="2000" aria-pressed="false">Lägenhet<small>2 000</small></button>
<button type="button" data-v="5000" aria-pressed="true">Villa<small>5 000</small></button>
<button type="button" data-v="20000" aria-pressed="false">Villa elvärme<small>20 000</small></button>
</div>
</div>

<div class="gk-field">
<label for="avtal">Ditt elavtal</label>
<div class="gk-input"><select id="avtal">
<option value="rorligt">Rörligt månadspris</option>
<option value="timpris">Tim- eller kvartspris</option>
<option value="avtal1ar">Fast pris 1 år</option>
<option value="avtal2ar">Fast pris 2 år</option>
<option value="avtal3ar">Fast pris 3 år</option>
<option value="anvisat">Vet inte – har aldrig valt</option>
</select></div>
</div>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:14px" aria-labelledby="youH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="youH" style="font-size:22px">Betalar du för mycket?</h2>
<p class="gk-hint" id="youSub">Fyll i priset från din elfaktura så jämför vi med snittet.</p>
</div>
<div class="gk-stack" id="minpris" style="gap:14px">
<div class="gk-field" id="manadWrap">
<label for="manad">Fakturan gäller</label>
<div class="gk-input"><select id="manad"></select></div>
</div>
<div class="gk-field">
<label for="pris">Ditt elpris</label>
<div class="gk-input"><input id="pris" inputmode="decimal" autocomplete="off" placeholder="t.ex. 85,5"><span class="unit">öre/kWh</span></div>
<span class="gk-hint" id="prisHint">Lägg ihop alla rader för elen per kWh: spotpris, påslag, elcertifikat och liknande. Inte elnät eller energiskatt.</span>
<div class="gk-seg" style="--n:2" id="moms" role="group" aria-label="Moms i priset">
<button type="button" data-v="exkl" aria-pressed="true">Exkl. moms</button>
<button type="button" data-v="inkl" aria-pressed="false">Inkl. moms</button>
</div>
</div>
<div class="gk-field">
<label for="avgift">Fast avgift till elhandlaren</label>
<div class="gk-input"><input id="avgift" inputmode="decimal" autocomplete="off" placeholder="t.ex. 39"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Kallas ofta månadsavgift eller fast påslag. Ange 0 om du inte har någon.</span>
</div>
</div>
<div id="verdict" aria-live="polite"></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Snittpris för nya avtal</div>
<div class="gk-big"><strong id="resBig">–</strong><span id="resUnit">öre/kWh</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-o4" style="gap:12px" aria-labelledby="cmpH">
<h2 id="cmpH" style="font-size:22px">Vilket avtal är billigast för dig?</h2>
<p class="gk-hint" id="cmpSub"></p>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="cmpTable"></table></div>
<p class="gk-hint" id="cmpNote"></p>
<figure style="margin:4px 0 0">
<figcaption class="gk-hint" style="margin-bottom:6px" id="chartCap"></figcaption>
<div id="chart"></div>
</figure>
</section>

<section class="gk-card gk-stack gk-o5" style="gap:12px" aria-labelledby="billH">
<h2 id="billH" style="font-size:22px">Hela elräkningen per år</h2>
<div class="gk-big"><strong id="billBig">–</strong><span id="billUnit">kr/år inkl. moms</span></div>
<div id="billBar" style="display:flex;height:14px;border-radius:7px;overflow:hidden;background:var(--gk-chip)"></div>
<div class="gk-tiles" id="billTiles"></div>
<p class="gk-hint" id="billNote"></p>
<details class="gk-more">
<summary>Ändra elnät och energiskatt</summary>
<div>
<div class="gk-field">
<label for="nat">Din elnätskostnad</label>
<div class="gk-input"><input id="nat" inputmode="numeric" autocomplete="off" placeholder="snitt används"><span class="unit">kr/mån inkl. moms</span></div>
<span class="gk-hint">Står på fakturan från ditt elnätsföretag. Lämnar du tomt använder vi SCB:s snitt.</span>
</div>
<label class="gk-check"><input type="checkbox" id="norr"> <span>Jag bor i en kommun med sänkt energiskatt (vissa kommuner i norra Sverige)</span></label>
</div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="https://www.elpriskollen.se/" target="_blank" rel="noopener"><span>Jämför alla elavtal på Elpriskollen<small>Energimarknadsinspektionens jämförelsetjänst – alla elhandlare, utan annonser</small></span>{CHEV}</a>
<!--GK-PARTNER:el:START--><!--GK-PARTNER:el:END-->
<div style="display:flex;flex-direction:column;gap:6px;padding:14px;border-radius:12px;background:var(--gk-soft);color:var(--gk-good-ink)">
<strong style="font-size:15px">Spara i Min ekonomi</strong>
<span style="font-size:14px;line-height:1.45">Då ser du direkt nästa gång om ditt avtal fortfarande är rimligt. Sparas bara i din webbläsare – vi ser inte dina siffror.</span>
<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:4px">
<button class="gk-btn" type="button" id="saveBtn">Spara mina siffror</button>
<span id="saveMsg" style="font-size:14px;font-weight:600" role="status"></span>
</div>
</div>
</section>
</div>
</div>

<div class="gk-prose">
<section class="gk-section"><!--ELTEXT:START-->{blocks['ELTEXT']}<!--ELTEXT:END--></section>

<h2>Vad ingår i elräkningen?</h2>
<p>Elräkningen består av tre delar. Bara den första kan du påverka genom att byta avtal:</p>
<ul>
<li><strong>Elhandel</strong> – själva elen, från din elhandlare. Rörligt pris, fast pris eller tim- och kvartspris, plus eventuell fast avgift.</li>
<li><strong>Elnät</strong> – överföringen till ditt hus, från ditt lokala elnätsföretag. En fast avgift och en avgift per kWh. Du kan inte välja nätbolag.</li>
<li><strong>Skatter</strong> – energiskatt på 36,0 öre/kWh exklusive moms 2026 (sänkt från 43,9 öre 2025) och 25 procent moms på allt.</li>
</ul>

<h2>Rörligt eller fast elpris?</h2>
<p>Med rörligt pris betalar du ungefär vad elen kostade på elbörsen den månaden plus elhandlarens påslag. Det har ofta varit billigast i snitt, men priset kan dubblas under en kall vinter. Med fast pris betalar du samma pris i 1–3 år och vet vad elen kommer att kosta. Tabellen ovan visar hur det har sett ut i ditt elområde det senaste året.</p>
<p>Tim- och kvartsprisavtal följer elbörsen, där priset sedan 1 oktober 2025 sätts per kvart. De kan löna sig om du kan flytta förbrukning, till exempel laddning av elbil, till billiga timmar. SCB publicerar inget eget snittpris för dem, så vi jämför dem med rörligt månadspris.</p>

<h2>Så sänker du elkostnaden</h2>
<ul>
<li>Har du aldrig valt elavtal? Då har du troligen ett anvisat avtal, som i regel är dyrare än ett du väljer själv.</li>
<li>Jämför ditt påslag och din fasta avgift med andra elhandlare på Elpriskollen.</li>
<li>Sänk inomhustemperaturen en grad och se över värmepumpens inställningar.</li>
<li>Har du tim- eller kvartspris: kör tvätt, disk och laddning när elen är billig.</li>
</ul>

<h2>Vanliga frågor</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/artiklar/elkostnad-2026-sa-raknar-du"><span>Guide: Elkostnad 2026 – så räknar du<small>Energiskatt, elnät, moms och normal förbrukning</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/solcellskalkylator"><span>Solcellskalkylator<small>Vad sparar du med egna solceller?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/bilkostnadsraknare"><span>Bilkostnadsräknare<small>Vad kostar bilen per mil och månad?</small></span>{CHEV}</a>
</div>
</div>
<!--ELDATA:START-->{blocks['ELDATA']}<!--ELDATA:END-->
</main>
<script>
{JS}
</script>
"""
    return S.head(title, desc, PATH, og_title="Vad borde elen kosta? Elkostnadskalkylator 2026", jsonld=ld) + S.header() + body + S.footer(
        "Elpriserna är snitt för nytecknade avtal enligt SCB och Energimyndigheten.")


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var D = JSON.parse(document.getElementById('gk-eldata').textContent);
  var MN = ['januari','februari','mars','april','maj','juni','juli','augusti','september','oktober','november','december'];
  var AVTAL_NAMN = { rorligt: 'rörligt månadspris', timpris: 'tim- eller kvartspris', avtal1ar: 'fast pris 1 år', avtal2ar: 'fast pris 2 år', avtal3ar: 'fast pris 3 år', anvisat: 'anvisat avtal' };
  var RAD_NAMN = { rorligt: 'Rörligt', avtal1ar: 'Fast 1 år', avtal2ar: 'Fast 2 år', avtal3ar: 'Fast 3 år', anvisat: 'Anvisat' };
  var KAT = ['1','2','3','4'];
  var KAT_NAMN = { '1': 'lägenhet, 2 000 kWh', '2': 'villa utan elvärme, 5 000 kWh', '3': 'villa med elvärme, 20 000 kWh', '4': 'större hushåll, 30 000 kWh' };
  var MOMS = 1.25;
  var n = D.manader.length, LAST = n - 1;
  var $ = function (id) { return document.getElementById(id); };
  var f0 = function (v) { return GK.fmt(v, 0); }, f1 = function (v) { return GK.fmt(v, 1); };
  var kr = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  function mtext(i) { var p = D.manader[i].split('-'); return MN[+p[1] - 1] + ' ' + p[0]; }

  /* Snittpris = E + F/kWh, anpassat till SCB:s fyra typhushåll (minsta kvadrat) */
  function fit(a, o, i) {
    var xs = KAT.map(function (k) { return 1 / D.typkundKwh[k]; });
    var ys = KAT.map(function (k) { return D.pris[a][o][k][i] / 100; });
    var mx = xs.reduce(function (s, x) { return s + x; }, 0) / 4, my = ys.reduce(function (s, y) { return s + y; }, 0) / 4;
    var num = 0, den = 0;
    for (var j = 0; j < 4; j++) { num += (xs[j] - mx) * (ys[j] - my); den += (xs[j] - mx) * (xs[j] - mx); }
    var F = num / den; return { E: (my - F * mx) * 100, F: F };
  }
  function bench(a, o, i, K) {
    var k = Math.min(60000, Math.max(800, K)); var r = fit(a, o, i); return r.E + r.F * 100 / k;
  }
  function avg12(a, o, K) { var s = 0; for (var i = LAST - 11; i <= LAST; i++) s += bench(a, o, i, K); return s / 12; }
  function nearestKat(K) {
    var best = '1', d = 1e9; KAT.forEach(function (k) { var x = Math.abs(Math.log(K / D.typkundKwh[k])); if (x < d) { d = x; best = k; } }); return best;
  }
  function elnatKr(K) { /* SCB:s viktade snitt per typhushåll, kr/år exkl. moms, linjärt mellan punkterna */
    var pts = KAT.map(function (k) { return [D.typkundKwh[k], D.elnat.ore[k] * D.typkundKwh[k] / 100]; });
    if (K <= pts[0][0]) return D.elnat.ore['1'] * K / 100;
    for (var j = 1; j < pts.length; j++) if (K <= pts[j][0]) { var t = (K - pts[j-1][0]) / (pts[j][0] - pts[j-1][0]); return pts[j-1][1] + t * (pts[j][1] - pts[j-1][1]); }
    return pts[3][1] * K / pts[3][0];
  }

  /* ── Tillstånd och formulär ── */
  var st = { omr: 'SE3', moms: 'exkl' };
  function seg(id, key, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      if (key) st[key] = b.getAttribute('data-v');
      if (cb) cb(b.getAttribute('data-v'));
      calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x.getAttribute('data-v') === String(v) ? 'true' : 'false'); }); }
  seg('omr', 'omr'); seg('moms', 'moms');
  seg('kwhq', null, function (v) { $('kwh').value = GK.fmt(+v, 0); });
  var ms = $('manad');
  for (var i = LAST; i >= 0; i--) { var o = document.createElement('option'); o.value = i; o.textContent = mtext(i).charAt(0).toUpperCase() + mtext(i).slice(1); ms.appendChild(o); }
  ['kwh','pris','avgift','nat'].forEach(function (id) { $(id).addEventListener('input', calc); });
  ['avtal','manad','norr'].forEach(function (id) { $(id).addEventListener('change', calc); });
  $('kwh').addEventListener('input', function () { var K = GK.parse($('kwh').value); press('kwhq', K); });
  GK.groupInput($('kwh'));

  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }

  function verdictHtml(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }

  var last = null;
  function calc() {
    var K = val('kwh'); if (!K || K < 100) K = null;
    var o = st.omr, av = $('avtal').value;
    var a = av === 'timpris' ? 'rorligt' : av;
    var isFast = a.indexOf('avtal') === 0;
    var mi = isFast || a === 'anvisat' ? LAST : +ms.value;
    $('manadWrap').style.display = (a === 'rorligt') ? '' : 'none';
    $('minpris').style.display = (av === 'anvisat') ? 'none' : '';
    $('youSub').style.display = (av === 'anvisat') ? 'none' : '';
    if (!K) { $('resBig').textContent = '–'; $('resSub').textContent = 'Ange din förbrukning per år.'; return; }

    var b = bench(a, o, mi, K);
    var kat = nearestKat(K);
    $('resLabel').textContent = 'Snittpris för nya avtal med ' + AVTAL_NAMN[a] + ' · ' + o + ' · ' + mtext(mi);
    $('resBig').textContent = f1(b);
    $('resUnit').textContent = 'öre/kWh';
    $('resSub').textContent = 'Exkl. moms, inkl. fasta avgifter för ' + f0(K) + ' kWh/år. Inkl. moms: ' + f1(b * MOMS) + ' öre/kWh.';

    /* Användarens pris */
    var p = val('pris'), fee = val('avgift');
    var inkl = st.moms === 'inkl';
    var you = null;
    var vh = '';
    if (av !== 'anvisat' && p != null && p > 0) {
      var pEx = inkl ? p / MOMS : p;
      var feeEx = fee != null ? (inkl ? fee / MOMS : fee) : 0;
      you = pEx + feeEx * 12 * 100 / K;
      var d = you - b, dk = d / 100 * K * MOMS;
      var basis = (isFast ? 'vad ett nytt ' + AVTAL_NAMN[a] + ' kostar i ' + mtext(mi) : 'snittet för nya avtal i ' + mtext(mi));
      if (you > b * 2.5 || you < b * 0.35) {
        vh = verdictHtml('info', 'Kontrollera priset', 'Ditt pris (' + f1(you) + ' öre/kWh exkl. moms inkl. avgift) skiljer sig mycket från ' + basis + ' (' + f1(b) + ' öre). Har du råkat ta med elnät eller energiskatt, eller valt fel moms?');
      } else if (d >= 2) {
        vh = verdictHtml('warn', 'Du betalar mer än snittet', 'Ditt elpris är ' + f1(d) + ' öre/kWh högre än ' + basis + '. Det motsvarar ungefär ' + kr(dk) + ' mer per år inkl. moms.');
      } else if (d <= -2) {
        vh = verdictHtml('good', 'Du ligger bra till', 'Ditt elpris är ' + f1(-d) + ' öre/kWh lägre än ' + basis + '. Det motsvarar ungefär ' + kr(-dk) + ' mindre per år inkl. moms.');
      } else {
        vh = verdictHtml('good', 'Du ligger i nivå med snittet', 'Ditt elpris skiljer sig mindre än 2 öre/kWh från ' + basis + '.');
      }
      if (fee == null) vh += '<p class="gk-hint" style="margin-top:8px">Du har inte angett någon fast avgift. Har du en blir ditt pris högre.</p>';
      if (av === 'timpris') vh += '<p class="gk-hint" style="margin-top:8px">SCB publicerar inget snittpris för tim- och kvartsprisavtal, så vi jämför med rörligt månadspris samma månad.</p>';
    } else if (av === 'anvisat') {
      var r = bench('rorligt', o, LAST, K);
      var s12 = (avg12('anvisat', o, K) - avg12('rorligt', o, K)) / 100 * K * MOMS;
      vh = (b - r > 0 && s12 > 0)
        ? verdictHtml('warn', 'Anvisat avtal är dyrare än rörligt pris', 'Har du aldrig valt elavtal har du troligen ett anvisat avtal. Det kostade ' + f1(b - r) + ' öre/kWh mer än rörligt pris i ' + mtext(LAST) + '. De senaste 12 månaderna motsvarar skillnaden ungefär ' + kr(s12) + ' per år för dig.')
        : verdictHtml('info', 'Har du aldrig valt elavtal?', 'Då har du troligen ett anvisat avtal. Jämför med tabellen nedan och på Elpriskollen.');
    } else {
      vh = '';
    }
    $('verdict').innerHTML = vh;

    var costYear = (you != null ? you : (isFast ? b : avg12(a, o, K))) / 100 * K * MOMS;
    $('tiles').innerHTML =
      '<div class="gk-tile"><span>Elhandel per år' + (you != null ? ', ditt pris' : '') + '</span><strong>' + kr(costYear) + '</strong></div>' +
      '<div class="gk-tile"><span>Per månad i snitt</span><strong>' + kr(costYear / 12) + '</strong></div>';

    var fr = fit(a, o, mi);
    $('how').innerHTML =
      '<p>Snittpriset kommer från SCB och Energimyndigheten: <a href="' + D.tabellUrl + '" target="_blank" rel="noopener">Elhandelspriser för nytecknade avtal</a>, ' + mtext(mi) + '. Det gäller själva elen och inkluderar elhandlarens fasta avgifter, men inte elnät, energiskatt och moms.</p>' +
      '<p>SCB redovisar snittet för fyra typer av hushåll. För ' + KAT_NAMN[kat] + ' i ' + o + ' var det ' + f1(D.pris[a][o][kat][mi]) + ' öre/kWh. Eftersom de fasta avgifterna slås ut på fler kWh ju mer du använder räknar vi fram priset för just din förbrukning: ' + f1(fr.E) + ' öre/kWh plus ca ' + f0(fr.F) + ' kr/år i fasta avgifter, delat på ' + f0(K) + ' kWh = ' + f1(b) + ' öre/kWh.</p>' +
      (you != null ? '<p>Ditt pris: ' + f1(inkl ? p / MOMS : p) + ' öre/kWh exkl. moms' + (fee ? ' plus ' + GK.fmt(inkl ? fee / MOMS : fee, 0) + ' kr/mån × 12 / ' + f0(K) + ' kWh' : '') + ' = ' + f1(you) + ' öre/kWh.</p>' : '') +
      '<p>Kronor per år = öre/kWh × förbrukning × 1,25 (moms).' + (!isFast && you == null ? ' För rörligt och anvisat pris använder vi snittet de senaste 12 månaderna.' : '') + '</p>';

    /* Jämförelse mellan avtalstyper */
    var rows = ['rorligt','avtal1ar','avtal2ar','avtal3ar','anvisat'];
    var yr = {};
    var mshort = MN[+D.manader[LAST].split('-')[1] - 1].slice(0, 3) + ' ' + D.manader[LAST].slice(0, 4);
    var th = '<thead><tr><th scope="col">Avtal</th><th scope="col"><abbr title="' + mtext(LAST) + '" style="text-decoration:none">' + mshort + '</abbr></th><th scope="col">12 mån</th><th scope="col">Per år*</th></tr></thead>';
    var tb = rows.map(function (x) {
      var now = bench(x, o, LAST, K), a12 = avg12(x, o, K);
      var y = (x.indexOf('avtal') === 0 ? now : a12) / 100 * K * MOMS; yr[x] = y;
      return '<tr' + (x === a ? ' class="is-you"' : '') + '><td>' + RAD_NAMN[x] + (x === a ? ' <span class="gk-sr">(ditt avtal)</span>' : '') + '</td><td>' + f1(now) + '</td><td>' + f1(a12) + '</td><td>' + kr(y) + '</td></tr>';
    }).join('');
    $('cmpTable').innerHTML = th + '<tbody>' + tb + '</tbody>';
    var cheapest = rows.reduce(function (m, x) { return yr[x] < yr[m] ? x : m; }, 'rorligt');
    $('cmpSub').textContent = 'Snittpris för nya avtal i ' + o + ' för ' + f0(K) + ' kWh/år. Öre/kWh exkl. moms: senaste månaden och snittet de senaste 12 månaderna.';
    $('cmpNote').textContent = '*Inkl. moms. Fast pris: dagens pris gäller hela avtalstiden. Rörligt och anvisat: snittet de senaste 12 månaderna – framtiden kan bli dyrare eller billigare. Lägst kostnad i tabellen: ' + RAD_NAMN[cheapest].toLowerCase() + '.';

    chart(o, K, a, you, mi);

    /* Hela räkningen */
    var natIn = val('nat');
    var natEx = natIn != null && natIn > 0 ? natIn * 12 / MOMS : elnatKr(K);
    var skattOre = D.energiskatt.ore - ($('norr').checked ? D.energiskatt.avdragNorr : 0);
    var handelEx = costYear / MOMS, skattEx = skattOre / 100 * K;
    var parts = [
      ['Elhandel', handelEx * MOMS, 'var(--gk-accent)'],
      ['Elnät', natEx * MOMS, 'var(--gk-ink-2)'],
      ['Energiskatt', skattEx * MOMS, 'var(--gk-warn)']
    ];
    var tot = parts.reduce(function (s, x) { return s + x[1]; }, 0);
    $('billBig').textContent = GK.fmt(Math.round(tot / 100) * 100, 0);
    $('billBar').innerHTML = parts.map(function (x) { return '<i title="' + x[0] + '" style="display:block;width:' + (x[1] / tot * 100).toFixed(1) + '%;background:' + x[2] + '"></i>'; }).join('');
    $('billTiles').innerHTML = parts.map(function (x) {
      return '<div class="gk-tile"><span><i style="display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;background:' + x[2] + '"></i>' + x[0] + '</span><strong>' + kr(x[1]) + '</strong></div>';
    }).join('') + '<div class="gk-tile"><span>Per månad i snitt</span><strong>' + kr(tot / 12) + '</strong></div>';
    $('billNote').textContent = 'Alla belopp inkl. moms. ' + (natIn ? 'Elnät enligt din uppgift. ' : 'Elnät är SCB:s snitt för Sverige ' + D.elnat.ar + ' – ditt nätbolag kan ligga betydligt högre eller lägre. ') +
      'Energiskatt ' + f1(skattOre) + ' öre/kWh exkl. moms (' + D.energiskatt.ar + ').';

    last = { omr: o, kwh: K, avtal: av, prisOre: you, snittOre: b, diffKrAr: you != null ? (you - b) / 100 * K * MOMS : null, manad: D.manader[mi], kostnadKrAr: Math.round(costYear) };
  }

  /* ── Diagram: rörligt och fast 1 år senaste 13 månaderna ── */
  function chart(o, K, a, you, mi) {
    var series = [['rorligt', 'Rörligt', 'var(--gk-accent)', ''], ['avtal1ar', 'Fast 1 år', 'var(--gk-ink-2)', '6 4']];
    if (a !== 'rorligt' && a !== 'avtal1ar') series.push([a, RAD_NAMN[a], 'var(--gk-warn)', '2 3']);
    var data = series.map(function (s) { var v = []; for (var i = 0; i < n; i++) v.push(bench(s[0], o, i, K)); return v; });
    var all = [].concat.apply([], data); if (you != null) all.push(you);
    var lo = Math.floor(Math.min.apply(null, all) / 20) * 20, hi = Math.ceil(Math.max.apply(null, all) / 20) * 20;
    var W = Math.max(300, Math.min(760, $('chart').clientWidth || 600)), H = W < 500 ? 200 : 230, L = 34, R = 26, T = 12, B = 28;
    var x = function (i) { return L + i * (W - L - R) / (n - 1); }, y = function (v) { return T + (hi - v) / (hi - lo) * (H - T - B); };
    var g = '';
    for (var t = lo; t <= hi; t += 20) g += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(t) + '" y2="' + y(t) + '" stroke="var(--gk-border)"/><text x="' + (L - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end" font-size="11" fill="var(--gk-muted)">' + t + '</text>';
    for (var i = 0; i < n; i += (W < 500 ? 4 : 3)) { var p = D.manader[i].split('-'); g += '<text x="' + x(i) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="var(--gk-muted)">' + MN[+p[1] - 1].slice(0, 3) + ' ' + p[0].slice(2) + '</text>'; }
    var lines = data.map(function (v, si) {
      var s = series[si];
      return '<polyline fill="none" stroke="' + s[2] + '" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"' + (s[3] ? ' stroke-dasharray="' + s[3] + '"' : '') + ' points="' + v.map(function (vv, i) { return x(i).toFixed(1) + ',' + y(vv).toFixed(1); }).join(' ') + '"/>';
    }).join('');
    var dot = you != null ? '<circle cx="' + x(mi) + '" cy="' + y(you) + '" r="6" fill="var(--gk-surface)" stroke="var(--gk-ink)" stroke-width="2.5"/>' : '';
    var legend = series.map(function (s) { return '<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px"><svg width="22" height="8" aria-hidden="true"><line x1="1" x2="21" y1="4" y2="4" stroke="' + s[2] + '" stroke-width="2.5"' + (s[3] ? ' stroke-dasharray="' + s[3] + '"' : '') + '/></svg>' + s[1] + '</span>'; }).join('') +
      (you != null ? '<span style="display:inline-flex;align-items:center;gap:6px"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="var(--gk-ink)" stroke-width="2"/></svg>Ditt pris</span>' : '');
    var desc = series.map(function (s, si) { return s[1] + ' ' + f1(data[si][0]) + ' till ' + f1(data[si][n - 1]) + ' öre'; }).join(', ');
    $('chartCap').textContent = 'Snittpris för nya avtal senaste 13 månaderna, öre/kWh exkl. moms, ' + o + ', ' + f0(K) + ' kWh/år.';
    $('chart').innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + desc + '" style="display:block;font-family:inherit">' + g + lines + dot + '</svg><div class="gk-hint" style="margin-top:6px">' + legend + '</div>';
  }

  /* ── Min ekonomi ── */
  $('saveBtn').addEventListener('click', function () {
    if (!last) return;
    var ok = GK.ekonomi.set('el', last);
    $('saveMsg').textContent = ok ? 'Sparat på den här enheten.' : 'Det gick inte att spara i den här webbläsaren.';
  });
  var saved = GK.ekonomi.get('el');
  if (saved) {
    st.omr = saved.omr || 'SE3'; press('omr', st.omr);
    if (saved.kwh) { $('kwh').value = GK.fmt(saved.kwh, 0); press('kwhq', saved.kwh); }
    if (saved.avtal) $('avtal').value = saved.avtal;
    if (saved.prisOre != null) { $('pris').value = GK.fmt(saved.prisOre, 1); $('avgift').value = '0'; st.moms = 'exkl'; press('moms', 'exkl'); }
    $('saveMsg').textContent = 'Dina sparade siffror från ' + saved.sparad + ' är ifyllda.';
  }
  calc();
});
"""


def main():
    data_file = os.path.join(ROOT, "data", "elpriser.json")
    with open(data_file, encoding="utf-8") as f:
        payload = json.load(f)
    html_text = page(U.render_blocks(payload))
    out = os.path.join(ROOT, "kalkylatorer", "elkostnadskalkylator.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")


if __name__ == "__main__":
    main()
