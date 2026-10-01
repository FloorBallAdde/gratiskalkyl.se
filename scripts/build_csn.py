#!/usr/bin/env python3
"""Bygger kalkylatorer/csn-kalkylator.html i den nya designen.

Regler och belopp för 2026 (källor i SOURCES och i sidans text):
  CSN-ränta 2,135 %, årsbeloppet räknas upp med 2 % per år, minsta årsbelopp 8 880 kr,
  avgift 150 kr/år, högst 25 år och senast det år man fyller 64 (lån från 2022) eller 60 (lån 2001–2021),
  nedsättning till 5 % (under 50 år) eller 7 % (från 50 år) av inkomsten om det sänker årsbeloppet
  med minst 1 776 kr (2026).

    python3 scripts/build_csn.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/csn-kalkylator"
UPDATED = "30 september 2026"

# Konstanter 2026 – ändra här vid årsskiftet (se arsskifte-2027.md)
K = {
    "AR": 2026,
    "RANTA": 2.135,        # CSN-ränta 2026, %
    "UPPRAKNING": 0.02,    # årsbeloppet räknas upp med ca 2 % per år
    "MIN": 8880,           # minsta årsbelopp 2026 (0,15 × prisbasbeloppet 59 200)
    "AVGIFT": 150,         # avgift per år
    "NED_DIFF": 1776,      # nedsättning kräver att årsbeloppet sänks med minst så mycket (2026)
    "SNITT": 230000,       # genomsnittlig skuld enligt CSN
}

SRC = {
    "ranta": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan/ranta-och-avgifter.html",
    "arsbelopp": "https://www.csn.se/fragor-och-svar/hur-har-ni-raknat-ut-vad-jag-ska-betala-tillbaka-pa-mitt-studielan-i-ar.html",
    "tid": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan/sa-lange-betalar-du-pa-ditt-studielan.html",
    "mindre": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan/betala-mindre-under-en-tid.html",
    "extra": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan/extra-inbetalning.html",
    "avskrivning": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan/avskrivning-av-studielan.html",
    "paminnelse": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan/paminnelseavgift.html",
    "start": "https://www.csn.se/betala-tillbaka/betala-tillbaka-studielan.html",
    "snitt": "https://www.csn.se/om-csn/aktuellt/nyhetsflode/2025-08-15-fem-vanliga-missuppfattningar-om-csn-rantan.html",
}


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def annuitet(d, r, n, g=K["UPPRAKNING"]):
    if n <= 0:
        return d * (1 + r)
    if abs(r - g) < 1e-9:
        return d * (1 + r) / n
    return d * (r - g) / (1 - ((1 + g) / (1 + r)) ** n)


def forsta_ar(d, r=K["RANTA"] / 100, n=25):
    return max(annuitet(d, r, n), K["MIN"])


EX300 = round(forsta_ar(300000) / 12, -1)
EX230 = round(forsta_ar(K["SNITT"]) / 12, -1)
EX300Y = round(forsta_ar(300000), -1)

FAQ = [
    ("Hur mycket betalar man tillbaka på CSN-lånet per månad?",
     f"Det beror på hur stor skulden är, räntan och hur många år du har kvar att betala. Med CSN-räntan 2026 (2,135 %) och "
     f"25 år betalar du ungefär {fmt(EX230)} kr i månaden första året för en skuld på 230 000 kr, som är en genomsnittlig skuld enligt CSN, "
     f"och ungefär {fmt(EX300)} kr i månaden för 300 000 kr. Beloppet ökar med cirka 2 procent per år. Det minsta årsbeloppet 2026 är "
     f"8 880 kr (740 kr i månaden). Till det kommer en avgift på 150 kr per år."),
    ("Hur länge måste man betala tillbaka CSN-lånet?",
     "Som längst 25 år. Lånet ska också vara betalt senast det år du fyller 64 om det betalades ut från 2022, eller 60 om det "
     "betalades ut mellan 1 juli 2001 och 2021. Är skulden liten blir tiden kortare, eftersom du alltid betalar minst 8 880 kr per år (2026). "
     "Lånet skrivs inte av efter 25 år. Det som finns kvar skrivs av i början av det år du fyller 72 (lån från 2022) eller 68 (lån 2001–2021)."),
    ("Vad är CSN-räntan 2026?",
     "CSN-räntan för 2026 är 2,135 procent. Den bygger på statens upplåningskostnad de senaste tre åren och är redan nedsatt med "
     "30 procent. Därför får du inte dra av räntan i deklarationen. Regeringen bestämmer räntan för nästa år i slutet av varje år."),
    ("När börjar man betala tillbaka CSN?",
     "Återbetalningen börjar vid ett årsskifte, tidigast sex månader efter att du hade studiestöd sista gången. Slutar du plugga "
     "på våren börjar du alltså betala året därpå, och slutar du på hösten börjar du ett år senare. Vanligtvis betalar du fyra "
     "gånger per år (februari, maj, augusti och november), men du kan ändra till att betala varje månad."),
    ("Kan man betala mindre på CSN-lånet om man har låg inkomst?",
     "Ja, du kan ansöka om att betala mindre. Årsbeloppet sätts då till 5 procent av din inkomst om du är under 50 år och "
     "7 procent från 50 år. För 2026 måste det nya årsbeloppet vara minst 1 776 kr lägre än det vanliga, och ansökan ska ha kommit "
     "in till CSN senast den 30 november 2026. Skulden minskar då långsammare, så lånet blir dyrare på sikt."),
    ("Kan man betala extra på CSN-lånet?",
     "Ja. En extra inbetalning räknas i första hand av mot det du ska betala i år. Har du redan betalat hela årsbeloppet minskar "
     "den i stället skulden, och då blir kommande årsbelopp lägre. En extra inbetalning under 2026 räknas inte av mot årsbeloppet för 2027."),
    ("Varför blir årsbeloppet högre för varje år?",
     "CSN räknar med en särskild annuitetsformel där årsbeloppet räknas upp med cirka 2 procent per år. Du betalar alltså lite "
     "mindre i början och lite mer i slutet. Varje år räknar CSN om beloppet utifrån skulden, räntan och antalet år som är kvar."),
    ("Vad händer om man inte betalar CSN i tid?",
     "Då skickar CSN en påminnelse och lägger på en avgift på 450 kr. Betalar du fortfarande inte kommer en ny påminnelse med "
     "ytterligare 450 kr i avgift. Kan du inte betala är det bättre att i tid ansöka om att betala mindre."),
]

CHEV = S.ICON_CHEV


def page():
    title = "CSN-kalkylator: räkna ut återbetalning | GratisKalkyl"
    desc = ("Hur mycket betalar du tillbaka på CSN-lånet? Räkna ut månadsbelopp, årsbelopp, när du är klar och total ränta "
            "med CSN:s regler 2026. Se om du kan betala mindre.")
    crumbs = [("Hem", "/"), ("Sparande & pension", "/sparande-och-pension"), ("CSN-kalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "CSN-kalkylator 2026 – återbetalning av studielån",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-09-30"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Sparande & pension", "item": S.SITE + "/sparande-och-pension"},
            {"@type": "ListItem", "position": 3, "name": "CSN-kalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    years = "".join(
        f'<option value="{y}"{" selected" if y == 2027 else ""}>{y}{" – nästa år" if y == 2027 else (" – i år" if y == 2026 else "")}</option>'
        for y in range(2034, 2001, -1))

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">CSN-kalkylator 2026</div>
<h1>Hur mycket betalar du tillbaka på CSN-lånet?</h1>
<p class="gk-lead">Räkna ut vad du betalar per månad, när du är klar och vad lånet kostar i ränta – med CSN:s regler för 2026.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · CSN-ränta 2,135 % · Källa: <a href="{SRC['ranta']}" target="_blank" rel="noopener">CSN</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="csnform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="skuld">Din skuld hos CSN</label>
<div class="gk-input"><input id="skuld" inputmode="numeric" autocomplete="off" value="230 000"><span class="unit">kr</span></div>
<div class="gk-seg" style="--n:3" id="skuldq" role="group" aria-label="Vanliga skulder">
<button type="button" data-v="100000" aria-pressed="false">100 000</button>
<button type="button" data-v="230000" aria-pressed="true">230 000<small>snittet</small></button>
<button type="button" data-v="400000" aria-pressed="false">400 000</button>
</div>
<span class="gk-hint">Står på Mina sidor hos CSN. Har du inte börjat betala: ta skulden när du slutar plugga.</span>
</div>

<div class="gk-field">
<label for="alder">Din ålder i år</label>
<div class="gk-input"><input id="alder" inputmode="numeric" autocomplete="off" value="25"><span class="unit">år</span></div>
</div>

<div class="gk-field">
<label for="start">Första året du betalar</label>
<div class="gk-input"><select id="start">{years}</select></div>
<span class="gk-hint">Slutar du plugga i vår börjar du betala nästa år, i höst året därpå. Betalar du redan: välj året du började.</span>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">När betalades lånet ut?</legend>
<div class="gk-seg" style="--n:2" id="period" role="group" aria-label="När lånet betalades ut">
<button type="button" data-v="64" aria-pressed="true">Från 2022<small>betalt senast vid 64</small></button>
<button type="button" data-v="60" aria-pressed="false">2001–2021<small>betalt senast vid 60</small></button>
</div>
</fieldset>

<details class="gk-more">
<summary>Ändra räntan</summary>
<div>
<div class="gk-field">
<label for="ranta">CSN-ränta</label>
<div class="gk-input"><input id="ranta" inputmode="decimal" autocomplete="off" value="2,135"><span class="unit">% per år</span></div>
<span class="gk-hint">2,135 % gäller 2026. Räntan för kommande år bestäms i slutet av varje år – vi räknar som om den ligger kvar.</span>
</div>
</div>
</details>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:14px" aria-labelledby="lonH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="lonH" style="font-size:22px">Hur mycket av lönen går till CSN?</h2>
<p class="gk-hint">Fyll i din lön så ser du om du kan ansöka om att betala mindre.</p>
</div>
<div class="gk-field">
<label for="lon">Din lön per månad före skatt</label>
<div class="gk-input"><input id="lon" inputmode="numeric" autocomplete="off" placeholder="t.ex. 32 000"><span class="unit">kr/mån</span></div>
</div>
<div id="lonRes" aria-live="polite"></div>
</section>

<section class="gk-card gk-stack gk-o4" style="gap:14px" aria-labelledby="extraH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="extraH" style="font-size:22px">Betala extra?</h2>
<p class="gk-hint">Se vad du sparar i ränta om du betalar in extra varje år.</p>
</div>
<div class="gk-field">
<label for="extra">Extra inbetalning per år</label>
<div class="gk-input"><input id="extra" inputmode="numeric" autocomplete="off" placeholder="t.ex. 6 000"><span class="unit">kr/år</span></div>
<div class="gk-seg" style="--n:3" id="extraq" role="group" aria-label="Vanliga extra belopp">
<button type="button" data-v="3000" aria-pressed="false">3 000<small>250 kr/mån</small></button>
<button type="button" data-v="6000" aria-pressed="false">6 000<small>500 kr/mån</small></button>
<button type="button" data-v="12000" aria-pressed="false">12 000<small>1 000 kr/mån</small></button>
</div>
</div>
<div id="extraRes" aria-live="polite"></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Ditt månadsbelopp</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-o5" style="gap:12px" aria-labelledby="planH">
<h2 id="planH" style="font-size:22px">Så minskar skulden</h2>
<figure style="margin:0">
<figcaption class="gk-hint" style="margin-bottom:6px" id="chartCap"></figcaption>
<div id="chart"></div>
</figure>
<details class="gk-more">
<summary>Visa planen år för år</summary>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="planTable"></table></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="https://www.csn.se/mina-sidor.html" target="_blank" rel="noopener"><span>Se din skuld och ditt årsbelopp hos CSN<small>Mina sidor på csn.se – där står exakt vad du ska betala</small></span>{CHEV}</a>
<a class="gk-linkcard" href="{SRC['mindre']}" target="_blank" rel="noopener"><span>Ansök om att betala mindre<small>Om din inkomst är låg – CSN:s regler och ansökan</small></span>{CHEV}</a>
<div style="display:flex;flex-direction:column;gap:6px;padding:14px;border-radius:12px;background:var(--gk-soft);color:var(--gk-good-ink)">
<strong style="font-size:15px">Spara i Min ekonomi</strong>
<span style="font-size:14px;line-height:1.45">Då ser du ditt CSN-lån på startsidan nästa gång. Sparas bara i din webbläsare – vi ser inte dina siffror.</span>
<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:4px">
<button class="gk-btn" type="button" id="saveBtn">Spara mina siffror</button>
<span id="saveMsg" style="font-size:14px;font-weight:600" role="status"></span>
</div>
</div>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknar CSN ut vad du ska betala</h2>
<p>Har du tagit studielån efter 30 juni 2001 är det ett så kallat annuitetslån. CSN räknar då ut ett <strong>årsbelopp</strong> utifrån hur stor skulden är, räntan och hur många år du har kvar att betala. Beloppet räknas upp med cirka 2 procent per år, så du betalar lite mindre i början och lite mer i slutet. Årsbeloppet beror alltså inte på din lön.</p>
<ul>
<li>Minsta årsbelopp 2026 är <strong>8 880 kr</strong> (740 kr i månaden). Är skulden liten blir du därför klar snabbare än 25 år.</li>
<li>Till årsbeloppet kommer en avgift på <strong>150 kr per år</strong>.</li>
<li>Du betalar vanligtvis fyra gånger per år – i februari, maj, augusti och november – men kan ändra till att betala varje månad.</li>
<li>Återbetalningen börjar vid ett årsskifte, tidigast sex månader efter att du hade studiestöd sista gången.</li>
</ul>
<p>Kalkylatorn använder samma princip. CSN räknar på din exakta skuld och ränta, så beloppet på Mina sidor kan skilja något.</p>

<h2>Hur länge betalar man på CSN-lånet?</h2>
<p>Du har som längst <strong>25 år</strong> på dig. Lånet ska också vara betalt senast det år du fyller <strong>64</strong> om det betalades ut från 2022, eller <strong>60</strong> om det betalades ut mellan 1 juli 2001 och 2021. Börjar du betala sent får du alltså färre år på dig, och då blir årsbeloppet högre. Lånet skrivs inte av efter 25 år – det som eventuellt finns kvar skrivs av i början av det år du fyller 72 (lån från 2022) eller 68 (lån 2001–2021).</p>

<h2>Kan du betala mindre?</h2>
<p>Har du låg inkomst kan du ansöka om att betala mindre ett år. Årsbeloppet blir då <strong>5 procent av din inkomst</strong> om du är under 50 år och <strong>7 procent</strong> från 50 år. Som inkomst räknas bland annat lön, a-kassa, föräldrapenning, sjukpenning och pension, men inte bostadsbidrag, barnbidrag eller studiebidrag. Från 50 år räknas även en del av dina tillgångar in.</p>
<p>För 2026 måste det nya årsbeloppet vara minst 1 776 kr lägre än det vanliga, och ansökan ska ha kommit in till CSN senast den <strong>30 november 2026</strong>. Skulden minskar då långsammare, så lånet blir dyrare på sikt.</p>

<h2>CSN-räntan 2026 och 2027</h2>
<p>CSN-räntan är <strong>2,135 procent</strong> för 2026. Den bygger på statens upplåningskostnad de senaste tre åren och är redan nedsatt med 30 procent, och därför får du inte dra av räntan i deklarationen. Räntan för 2027 bestäms av regeringen i slutet av 2026. Kalkylatorn räknar som om räntan ligger kvar – du kan ändra den under <em>Ändra räntan</em>.</p>

<h2>Vanliga frågor om CSN-lånet</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['ranta']}" target="_blank" rel="noopener">CSN – Ränta och avgifter</a> (ränta 2,135 %, avgift 150 kr/år)</li>
<li><a href="{SRC['arsbelopp']}" target="_blank" rel="noopener">CSN – Hur har ni räknat ut vad jag ska betala?</a> (annuitetsformel, minsta årsbelopp 8 880 kr)</li>
<li><a href="{SRC['tid']}" target="_blank" rel="noopener">CSN – Så länge betalar du på ditt studielån</a> (25 år, 60/64 år)</li>
<li><a href="{SRC['mindre']}" target="_blank" rel="noopener">CSN – Betala mindre under en tid</a> (5 %/7 %, 1 776 kr)</li>
<li><a href="{SRC['extra']}" target="_blank" rel="noopener">CSN – Extra inbetalning</a></li>
<li><a href="{SRC['avskrivning']}" target="_blank" rel="noopener">CSN – Avskrivning av studielån</a> (68/72 år)</li>
<li><a href="{SRC['snitt']}" target="_blank" rel="noopener">CSN – Fem vanliga missuppfattningar om CSN-räntan</a> (genomsnittlig skuld 230 000 kr)</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/artiklar/csn-2026-belopp-och-regler"><span>Guide: CSN 2026 – belopp och regler<small>Studiemedel, bidrag, lån och fribelopp</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/loneraknare"><span>Löneräknare<small>Vad blir kvar efter skatt?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Hushållsbudget<small>Få med CSN-lånet i din budget</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-csn" type="application/json">{{"ar":{K['AR']},"ranta":{K['RANTA']},"g":{K['UPPRAKNING']},"min":{K['MIN']},"avgift":{K['AVGIFT']},"nedDiff":{K['NED_DIFF']},"snitt":{K['SNITT']}}}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="CSN-kalkylator 2026 – hur mycket betalar du tillbaka?", jsonld=ld)
            + S.header() + body + S.footer("CSN-beräkningen är en uppskattning – exakt belopp står på Mina sidor hos CSN."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-csn').textContent);
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var st = { period: 64, periodTouched: false };

  function annuitet(D, r, n) {
    if (n <= 0) return D * (1 + r);
    if (Math.abs(r - C.g) < 1e-9) return D * (1 + r) / n;
    return D * (r - C.g) / (1 - Math.pow((1 + C.g) / (1 + r), n));
  }
  /* Plan år för år. Varje år räknar CSN om årsbeloppet på skulden och antalet år som är kvar. */
  function plan(D, r, n, y0, a0, X) {
    var rows = [], debt = D, ti = 0, tp = 0;
    for (var k = 0; k < n && debt > 0.5; k++) {
      var i = debt * r;
      var bas = Math.min(Math.max(annuitet(debt, r, n - k), C.min), debt + i);
      var pay = Math.min(bas + X, debt + i);
      debt = Math.max(0, debt - (pay - i));
      ti += i; tp += pay;
      rows.push({ ar: y0 + k, alder: a0 + k, belopp: pay, bas: bas, ranta: i, skuld: debt });
    }
    return { rows: rows, ranta: ti, betalt: tp, avgift: rows.length * C.avgift };
  }

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', String(+x.getAttribute('data-v')) === String(v) ? 'true' : 'false'); }); }
  seg('skuldq', function (v) { $('skuld').value = GK.fmt(+v, 0); });
  seg('extraq', function (v) { $('extra').value = GK.fmt(+v, 0); });
  seg('period', function (v) { st.period = +v; st.periodTouched = true; });
  ['skuld', 'alder', 'lon', 'ranta', 'extra'].forEach(function (id) { $(id).addEventListener('input', calc); });
  $('start').addEventListener('change', function () {
    if (!st.periodTouched) { st.period = +$('start').value <= 2022 ? 60 : 64; press('period', st.period); }
    calc();
  });
  $('skuld').addEventListener('input', function () { press('skuldq', GK.parse($('skuld').value)); });
  $('extra').addEventListener('input', function () { press('extraq', GK.parse($('extra').value)); });
  ['skuld', 'lon', 'extra'].forEach(function (id) { GK.groupInput($(id)); });

  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  var last = null;
  function calc() {
    var D = val('skuld'), age = val('alder'), r = val('ranta'), X = val('extra') || 0, lon = val('lon');
    var start = +$('start').value, L = st.period;
    if (r == null || r > 20) r = C.ranta;
    r = r / 100;
    if (!D || D < 100 || age == null || age < 15 || age > 80) {
      $('resBig').textContent = '–';
      $('resSub').textContent = !D || D < 100 ? 'Fyll i din skuld hos CSN.' : 'Fyll i din ålder.';
      ['tiles', 'verdict', 'how', 'chart', 'planTable', 'extraRes', 'chartCap', 'lonRes'].forEach(function (id) { $(id).innerHTML = ''; });
      last = null; return;
    }
    age = Math.round(age);
    var a0 = age + (start - C.ar);                 /* ålder första återbetalningsåret */
    var nTot = Math.max(1, Math.min(25, L - a0 + 1));
    var betalar = start <= C.ar;
    var y0 = betalar ? C.ar : start;
    var gjort = betalar ? C.ar - start : 0;
    var n = nTot - gjort, passerat = false;
    if (n < 1) { n = 1; passerat = true; }
    var aNu = betalar ? age : a0;

    var p = plan(D, r, n, y0, aNu, 0);
    var first = p.rows[0], sist = p.rows[p.rows.length - 1];
    var ars = first.belopp;
    $('resLabel').textContent = 'Ditt månadsbelopp ' + (betalar ? 'i år' : y0);
    $('resBig').textContent = GK.fmt(Math.round(ars / 12 / 10) * 10, 0);
    var snittM = Math.max(annuitet(C.snitt, C.ranta / 100, 25), C.min) / 12;
    $('resSub').textContent = 'Årsbelopp ' + y0 + ': ' + kr(ars) + ' plus avgift ' + C.avgift + ' kr. Ökar med ca 2 % per år. Jämför: en genomsnittlig låntagare med 230 000 kr i skuld och 25 år betalar ca ' + kr(snittM) + '/mån.';
    $('tiles').innerHTML = tile('Klar med lånet', String(sist.ar), 'Det år du fyller ' + sist.alder) +
      tile('Ränta totalt', kr(p.ranta), 'Plus avgifter ' + kr(p.avgift)) +
      tile('Totalt att betala', kr(p.betalt + p.avgift), 'Skuld + ränta + avgifter') +
      tile('Per inbetalning', kr(ars / 4), '4 gånger per år, plus avgiften');

    /* Besked */
    var v = '';
    if (passerat) {
      v += verdict('info', 'Kontrollera din återbetalningstid', 'Enligt reglerna ska lånet vara betalt senast det år du fyller ' + L + '. Vi räknar med att resten betalas i år – se ditt årsbelopp på Mina sidor hos CSN.');
    } else if (nTot < 25) {
      v += verdict('info', 'Du har ' + nTot + ' år på dig, inte 25', 'Lånet ska vara betalt senast det år du fyller ' + L + '. Det gör årsbeloppet högre än om du hade haft 25 år.');
    }
    if (first.bas <= C.min + 0.5 && D > C.min) {
      v += verdict('good', 'Du betalar minsta årsbeloppet', 'Din skuld är så liten att du betalar minsta årsbeloppet 8 880 kr (2026). Därför blir du klar redan ' + sist.ar + '.');
    }
    $('verdict').innerHTML = v;

    /* Andel av lönen och nedsättning */
    var lh = '';
    if (lon && lon >= 1000) {
      var andel = ars / (lon * 12) * 100, pct = aNu >= 50 ? 7 : 5, ned = lon * 12 * pct / 100;
      lh = '<div class="gk-tiles">' + tile('Andel av lönen', GK.fmt(andel, 1) + ' %', 'Årsbeloppet delat med din lön före skatt') +
        tile('Du kan få betala mindre om lönen är under', GK.fmt(Math.floor((ars - C.nedDiff) / pct * 100 / 12 / 100) * 100, 0) + ' kr/mån', 'Lön före skatt, ' + pct + ' %-regeln') + '</div>';
      if (ned <= ars - C.nedDiff) {
        lh += verdict('warn', 'Du kan ha rätt att betala mindre', 'Med din lön kan årsbeloppet sättas ned till ' + pct + ' % av inkomsten, ungefär ' + kr(ned) + ' per år (' + kr(ned / 12) + '/mån) i stället för ' + kr(ars) + '. Du måste ansöka hos CSN – för 2026 senast den 30 november. Skulden minskar då långsammare.');
      } else {
        lh += verdict('good', 'Du betalar det vanliga årsbeloppet', 'Med din lön kan du inte få årsbeloppet nedsatt: ' + pct + ' % av lönen blir ' + kr(ned) + ' per år, och det måste vara minst ' + GK.fmt(C.nedDiff, 0) + ' kr lägre än årsbeloppet ' + kr(ars) + '.');
      }
    }
    $('lonRes').innerHTML = lh;

    $('how').innerHTML =
      '<p>Årsbeloppet räknas med CSN:s annuitetsformel med 2 % uppräkning per år: skuld × (ränta − 2 %) / (1 − (1,02 / (1 + ränta))<sup>år kvar</sup>). ' +
      'Med ' + kr(D) + ', räntan ' + GK.fmt(r * 100, 3) + ' % och ' + n + ' år kvar blir det ' + kr(first.bas) + (first.bas <= C.min + 0.5 ? ' (minsta årsbeloppet ' + GK.fmt(C.min, 0) + ' kr)' : '') + '. Varje år räknas beloppet om på den skuld och de år som är kvar.</p>' +
      '<p>Antal år: högst 25 och senast det år du fyller ' + L + '. Du är ' + a0 + ' år första återbetalningsåret (' + start + ')' + (gjort > 0 ? ', och har betalat i ' + gjort + ' år' : '') + ' – alltså ' + n + ' år kvar från ' + y0 + '.</p>' +
      '<p>Har du lån från båda perioderna (före och från 2022) räknar CSN på dem var för sig. Vi räknar på hela skulden med den åldersgräns du valt.</p>' +
      '<p>Vi räknar som om räntan ligger kvar på ' + GK.fmt(r * 100, 3) + ' % och avgiften på ' + C.avgift + ' kr per år. CSN räknar på din exakta skuld och ränta, så beloppet på Mina sidor kan skilja något.</p>';

    /* Extra inbetalning */
    var px = X > 0 ? plan(D, r, n, y0, aNu, X) : null;
    if (px) {
      var sparR = p.ranta - px.ranta, sistX = px.rows[px.rows.length - 1];
      $('extraRes').innerHTML = verdict('good', 'Du sparar ca ' + kr(sparR + (p.avgift - px.avgift)) + ' i ränta och avgifter',
        'Om du betalar ' + kr(X) + ' extra varje år utöver årsbeloppet' + (sistX.ar < sist.ar ? ' är lånet betalt ' + sistX.ar + ' i stället för ' + sist.ar : '') + '. En extra inbetalning räknas först av mot det du ska betala i år – först när hela årsbeloppet är betalt minskar den skulden.');
    } else {
      $('extraRes').innerHTML = '';
    }

    chart(p, px, D);
    var tb = (px || p).rows.map(function (x) {
      return '<tr><td>' + x.ar + '</td><td>' + x.alder + '</td><td>' + GK.fmt(Math.round(x.belopp), 0) + '</td><td>' + GK.fmt(Math.round(x.ranta), 0) + '</td><td>' + GK.fmt(Math.round(x.skuld), 0) + '</td></tr>';
    }).join('');
    $('planTable').innerHTML = '<thead><tr><th scope="col">År</th><th scope="col">Ålder</th><th scope="col">Betalar</th><th scope="col">Varav ränta</th><th scope="col">Skuld efter</th></tr></thead><tbody>' + tb + '</tbody>' +
      '<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor per år' + (px ? ', med extra inbetalning' : '') + '. Plus avgift ' + C.avgift + ' kr per år.</caption>';

    last = { skuld: Math.round(D), alder: age, start: start, period: L, manadKr: Math.round(ars / 12), arsbelopp: Math.round(ars), ar: y0, klarAr: sist.ar, klarAlder: sist.alder };
  }

  function chart(p, px, D) {
    var rows = p.rows, n = rows.length + 1;
    var W = Math.max(300, Math.min(760, $('chart').clientWidth || 600)), H = W < 500 ? 190 : 220, Lp = 44, R = 14, T = 12, B = 28;
    var step = [10000, 20000, 25000, 50000, 100000, 200000, 250000, 500000].filter(function (s) { return D / s <= 5; })[0] || 500000;
    var hi = Math.ceil(D / step) * step;
    var x = function (i) { return Lp + i * (W - Lp - R) / Math.max(1, n - 1); }, y = function (v) { return T + (hi - v) / hi * (H - T - B); };
    var g = '', last = rows[rows.length - 1].ar;
    for (var t = 0; t <= hi + 1; t += step) g += '<line x1="' + Lp + '" x2="' + (W - R) + '" y1="' + y(t) + '" y2="' + y(t) + '" stroke="var(--gk-border)"/><text x="' + (Lp - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end" font-size="11" fill="var(--gk-muted)">' + (t >= 1000 ? Math.round(t / 1000) + ' tkr' : '0') + '</text>';
    var every = n > 20 ? 5 : (n > 10 ? 3 : 1);
    for (var i = 0; i < n; i += every) if (rows[0].ar + i <= last) g += '<text x="' + x(i) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="var(--gk-muted)">' + (rows[0].ar + i) + '</text>';
    function pts(rs) { return [x(0).toFixed(1) + ',' + y(D).toFixed(1)].concat(rs.map(function (r, i) { return x(i + 1).toFixed(1) + ',' + y(r.skuld).toFixed(1); })).join(' '); }
    var main = px || p;
    var area = '<polygon fill="var(--gk-soft)" points="' + x(0) + ',' + y(0) + ' ' + pts(main.rows) + ' ' + x(main.rows.length) + ',' + y(0) + '"/>';
    var line = '<polyline fill="none" stroke="var(--gk-accent)" stroke-width="2.5" stroke-linejoin="round" points="' + pts(main.rows) + '"/>';
    var base = px ? '<polyline fill="none" stroke="var(--gk-ink-2)" stroke-width="2" stroke-dasharray="6 4" points="' + pts(p.rows) + '"/>' : '';
    var legend = px ? '<div class="gk-hint" style="margin-top:6px"><span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px"><svg width="22" height="8" aria-hidden="true"><line x1="1" x2="21" y1="4" y2="4" stroke="var(--gk-accent)" stroke-width="2.5"/></svg>Med extra inbetalning</span><span style="display:inline-flex;align-items:center;gap:6px"><svg width="22" height="8" aria-hidden="true"><line x1="1" x2="21" y1="4" y2="4" stroke="var(--gk-ink-2)" stroke-width="2" stroke-dasharray="6 4"/></svg>Utan</span></div>' : '';
    $('chartCap').textContent = 'Din skuld hos CSN år för år, ' + rows[0].ar + '–' + last + '.';
    $('chart').innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Skulden minskar från ' + kr(D) + ' till 0 kr år ' + main.rows[main.rows.length - 1].ar + '" style="display:block;font-family:inherit">' + g + area + base + line + '</svg>' + legend;
  }

  /* Min ekonomi */
  $('saveBtn').addEventListener('click', function () {
    if (!last) return;
    var ok = GK.ekonomi.set('csn', last);
    $('saveMsg').textContent = ok ? 'Sparat på den här enheten.' : 'Det gick inte att spara i den här webbläsaren.';
  });
  var saved = GK.ekonomi.get('csn');
  if (saved && saved.skuld) {
    $('skuld').value = GK.fmt(saved.skuld, 0); press('skuldq', saved.skuld);
    if (saved.alder) $('alder').value = saved.alder + (C.ar - +(saved.sparad || String(C.ar)).slice(0, 4));
    if (saved.start) $('start').value = saved.start;
    if (saved.period) { st.period = saved.period; st.periodTouched = true; press('period', saved.period); }
    $('saveMsg').textContent = 'Dina sparade siffror från ' + saved.sparad + ' är ifyllda.';
  }
  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "csn-kalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    print("Exempel: 230 000 kr ->", EX230, "kr/mån; 300 000 kr ->", EX300, "kr/mån (", EX300Y, "kr/år)")


if __name__ == "__main__":
    main()
