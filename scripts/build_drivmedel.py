#!/usr/bin/env python3
"""Bygger kalkylatorer/drivmedelskalkylator.html i den nya verktygsmallen.

Modell (samma i Python-referensen nedan och i sidans JS):
  mil       = sträcka / 10 om den anges i km, × 2 vid tur och retur
  mängd     = mil × förbrukning (l/mil eller kWh/mil)
  kostnad   = mängd × pris (kr/l eller kr/kWh)
  per mil   = förbrukning × pris, per person = kostnad / antal personer
  förbrukning (extrakortet) = tankade liter / körda mil

Priser: Preems publicerade listpriser (företagskort, inkl. moms) – hämtade 1 oktober 2026.
Bensin 95 18,89 kr/l (från 2 oktober 2026) och diesel 23,14 kr/l (från 1 oktober 2026). Kontrollerat 3 oktober 2026.
Inget elpris förifylls (det beror på elavtal och nätbolag). Byt K vid ny prisuppdatering.

    python3 scripts/build_drivmedel.py
"""
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/drivmedelskalkylator"
UPDATED = "3 oktober 2026"

# Konstanter – byt här när priser eller statistik uppdateras
K = {
    "PRIS": {"bensin": 18.89, "diesel": 23.14},  # Preem listpris företagskort, kr/l inkl. moms
    "PRIS_DATUM": "3 oktober 2026",
    "LADD_PREEM": 4.99,        # Preems riktpris för laddning, kr/kWh inkl. moms (gäller från 13 nov 2025)
    "KOR_PRIVAT": 1155,        # Trafikanalys, Körsträckor 2025: privatägda personbilar, mil/år
    "KOR_ALLA": 1243,          # alla personbilar
    "KOR_LADDBAR": 1700,       # elbilar och laddhybrider, ungefär
    "MILERS": 25,              # Skatteverket: skattefri milersättning egen bil 2026, kr/mil
}
# Exempelvärden i formuläret (märkta som exempel på sidan, inga påståenden om typisk förbrukning)
D = {"STRACKA": 200, "FORBR": {"bensin": 0.7, "diesel": 0.7, "el": 2.0}}

SRC = {
    "preem": "https://www.preem.se/foretag/kund-hos-preem/listpriser/",
    "trafa": "https://www.trafa.se/globalassets/statistik/vagtrafik/korstrackor/2025/korstrackor-2025---2026-04-17.pdf",
    "skv": "https://www.skatteverket.se/privat/skatter/beloppochprocent/2026.4.1522bf3f19aea8075ba21.html",
}


def r(x, d=0):
    """Avrundning som i webbläsaren (halvt uppåt) – för att jämföra med JS."""
    q = Decimal(1).scaleb(-d)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def fmt(n, d=0):
    s = f"{r(n, d):,.{d}f}"
    return s.replace(",", "\u00a0").replace(".", ",")  # hårt mellanslag – talet bryts inte


def resa(stracka, enhet, tur, forbr, pris, pers=1):
    """Python-referens – samma logik som sidans JS."""
    mil = (stracka / 10 if enhet == "km" else stracka) * (2 if tur else 1)
    mangd = mil * forbr
    kost = mangd * pris
    return {"mil": mil, "mangd": mangd, "kost": kost, "permil": forbr * pris, "perpers": kost / pers}


def per_ar(forbr, pris, mil_ar):
    return forbr * pris * mil_ar


def forbrukning(liter, mil):
    return liter / mil


PB, PD = K["PRIS"]["bensin"], K["PRIS"]["diesel"]
EX = resa(D["STRACKA"], "km", False, D["FORBR"]["bensin"], PB)
AR = per_ar(D["FORBR"]["bensin"], PB, K["KOR_PRIVAT"])
p2 = lambda v: fmt(v, 2)  # noqa: E731
kr10 = lambda v: fmt(r(v / 10) * 10)  # noqa: E731

FAQ = [
    ("Hur räknar man ut bränslekostnad?",
     "Multiplicera sträckan i mil med bilens förbrukning i liter per mil och med literpriset. 30 mil med en bil som drar "
     f"0,6 liter per mil och bensin för {p2(PB)} kr/l blir 30 × 0,6 × {p2(PB)} = {fmt(30 * 0.6 * PB)} kr. Har du sträckan i "
     "kilometer delar du först med 10. Åker ni flera delar ni summan med antalet personer."),
    ("Vad kostar bensin per mil?",
     f"Förbrukningen gånger literpriset. Med {p2(PB)} kr/l (Preems listpris {K['PRIS_DATUM']}) kostar en bil som drar "
     f"0,5 l/mil {p2(0.5 * PB)} kr per mil, 0,7 l/mil {p2(0.7 * PB)} kr och 1,0 l/mil {p2(PB)} kr. Diesel kostar "
     f"{p2(PD)} kr/l, så 0,6 l/mil blir {p2(0.6 * PD)} kr per mil."),
    ("Hur mycket bensin drar en bil per mil?",
     "Det skiljer sig mellan bilar och beror också på hur du kör, så räkna med din egen bils värde. Anges förbrukningen i "
     "liter per 100 km delar du med 10: 7 l/100 km är 0,7 l/mil. Säkrast är att mäta själv mellan två fulltankningar."),
    ("Hur räknar man ut bränsleförbrukning?",
     "Tanka fullt och nollställ trippmätaren. Nästa gång du tankar fullt delar du antalet liter du tankade med antalet mil du "
     f"har kört. 42 liter efter 60 mil ger {p2(forbrukning(42, 60))} liter per mil, alltså 7 liter per 100 km."),
    ("Hur mycket kostar en full tank bensin?",
     f"Tankens storlek i liter gånger literpriset. En tank på 50 liter kostar {fmt(50 * PB)} kr med {p2(PB)} kr/l "
     f"(Preems listpris {K['PRIS_DATUM']}). Är tanken inte helt tom betalar du bara för det som ryms."),
    ("Vad kostar bensinen per år?",
     f"Privatägda personbilar körde i snitt {fmt(K['KOR_PRIVAT'])} mil 2025 enligt Trafikanalys. Med en förbrukning på "
     f"0,7 l/mil och {p2(PB)} kr/l blir det ca {kr10(AR)} kr om året, eller {kr10(AR / 12)} kr i månaden. Fyll i din egen "
     "sträcka per år i kalkylatorn för att se din kostnad."),
    ("Hur delar man på bensinkostnaden?",
     "Räkna ut vad bränslet kostar för hela resan och dela med antalet som åker med. Vill ni även dela på slitage och bilens "
     f"övriga kostnader kan den skattefria milersättningen för egen bil, {K['MILERS']} kr per mil 2026, vara ett riktmärke: "
     f"20 mil blir då {fmt(20 * K['MILERS'])} kr."),
    ("Vad kostar det att köra elbil per mil?",
     "Förbrukningen i kWh per mil gånger elpriset per kWh. Hemma är det ditt elpris med elnät, energiskatt och moms. "
     f"Vid publik laddning gäller operatörens pris – med Preems riktpris {p2(K['LADD_PREEM'])} kr/kWh kostar en elbil "
     f"som drar 2 kWh/mil {p2(2 * K['LADD_PREEM'])} kr per mil."),
]

CHEV = S.ICON_CHEV


def seg(vals, pressed, small=None):
    out = []
    for v, lab in vals:
        sm = f"<small>{small[v]}</small>" if small and v in small else ""
        out.append(f'<button type="button" data-v="{v}" aria-pressed="{"true" if v == pressed else "false"}">{lab}{sm}</button>')
    return "".join(out)


def page():
    title = "Räkna ut bränslekostnad för bilresan 2026 | GratisKalkyl"
    desc = (f"Räkna ut vad bilresan kostar i bensin, diesel eller el – totalt, per mil och per person. "
            f"Bensin 95 {p2(PB)} kr/l, diesel {p2(PD)} kr/l ({K['PRIS_DATUM']}).")
    crumbs = [("Hem", "/"), ("Bil & energi", "/bil-och-energi"), ("Drivmedelskalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Drivmedelskalkylator 2026 – räkna ut bränslekostnad",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-03"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Bil & energi", "item": S.SITE + "/bil-och-energi"},
            {"@type": "ListItem", "position": 3, "name": "Drivmedelskalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    rows = "".join(f"<tr><td>{fmt(f, 1)} l/mil</td><td>{p2(f * PB)} kr</td><td>{p2(f * PD)} kr</td></tr>"
                   for f in (0.5, 0.6, 0.7, 0.8, 1.0))
    ex_mil = fmt(EX["mil"])

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Drivmedelskalkylator 2026</div>
<h1>Vad kostar bilresan? – räkna ut bränslekostnaden</h1>
<p class="gk-lead">Fyll i sträckan, vad bilen drar och literpriset – så ser du vad resan kostar, per mil och per person.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Bränslepris den {K['PRIS_DATUM']} · Källa: <a href="{SRC['preem']}" target="_blank" rel="noopener">Preems listpriser</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="dmform" novalidate onsubmit="return false">
<fieldset class="gk-fieldset">
<legend class="gk-legend">Drivmedel</legend>
<div class="gk-seg" style="--n:3" id="typ" role="group" aria-label="Drivmedel">
{seg([("bensin", "Bensin"), ("diesel", "Diesel"), ("el", "El")], "bensin")}
</div>
</fieldset>

<div class="gk-field">
<label for="str">Sträcka</label>
<div class="gk-input"><input id="str" inputmode="decimal" autocomplete="off" value="{D['STRACKA']}"><span class="unit" id="strUnit">km</span></div>
<div class="gk-seg" style="--n:2" id="enh" role="group" aria-label="Enhet för sträckan">
{seg([("km", "Kilometer"), ("mil", "Mil")], "km")}
</div>
<label class="gk-check"><input type="checkbox" id="tur"> Tur och retur – räkna dubbla sträckan</label>
<span class="gk-hint">Förifyllt exempel – skriv in din sträcka.</span>
</div>

<div class="gk-field">
<label for="forbr">Bilens förbrukning</label>
<div class="gk-input"><input id="forbr" inputmode="decimal" autocomplete="off" value="0,7"><span class="unit" id="forbrUnit">l/mil</span></div>
<span class="gk-hint" id="forbrHint"></span>
</div>

<div class="gk-field">
<label for="pris" id="prisLabel">Pris per liter</label>
<div class="gk-input"><input id="pris" inputmode="decimal" autocomplete="off" value="{p2(PB)}"><span class="unit" id="prisUnit">kr/l</span></div>
<span class="gk-hint" id="prisHint"></span>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur många delar på kostnaden?</legend>
<div class="gk-seg" style="--n:5" id="pers" role="group" aria-label="Antal personer">
{seg([(n, str(n)) for n in range(1, 6)], 1)}
</div>
</fieldset>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:14px" aria-labelledby="fH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="fH" style="font-size:22px">Räkna ut förbrukningen</h2>
<p class="gk-hint">Tanka fullt och nollställ trippmätaren. Nästa gång du tankar fullt fyller du i hur mycket du tankade och hur långt du har kört.</p>
</div>
<div class="gk-field">
<label for="fl" id="flLabel">Tankade liter</label>
<div class="gk-input"><input id="fl" inputmode="decimal" autocomplete="off" placeholder="t.ex. 42"><span class="unit" id="flUnit">liter</span></div>
</div>
<div class="gk-field">
<label for="fm">Körda mil sedan förra tankningen</label>
<div class="gk-input"><input id="fm" inputmode="decimal" autocomplete="off" placeholder="t.ex. 60"><span class="unit">mil</span></div>
<span class="gk-hint">Visar mätaren km: dela med 10.</span>
</div>
<div id="fRes" aria-live="polite"></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Bränslekostnad för resan</div>
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
<a class="gk-linkcard" href="/kalkylatorer/bilkostnadsraknare"><span>Vad kostar bilen totalt?<small>Bilkostnadsräknare – med försäkring, skatt, service och värdeminskning</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/milersattningskalkylator"><span>Kör du i jobbet?<small>Milersättning – {K['MILERS']} kr/mil skattefritt 2026</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/elkostnadskalkylator"><span>Laddar du hemma?<small>Elkostnadskalkylator – vad kostar din el per kWh?</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknar du ut bränslekostnaden</h2>
<p><strong>Bränslekostnad = sträcka i mil × förbrukning i liter per mil × pris per liter.</strong> En mil är 10 km. Ska du köra {D['STRACKA']} km, alltså {ex_mil} mil, med en bil som drar 0,7 liter per mil och bensinen kostar {p2(PB)} kr/l blir det {ex_mil} × 0,7 × {p2(PB)} = <strong>{fmt(EX['kost'])} kr</strong>. Kör du tur och retur dubblar du sträckan.</p>

<h2>Vad kostar bensin och diesel per mil?</h2>
<p>Kostnaden per mil är förbrukningen gånger literpriset. Så här blir det med Preems listpriser den {K['PRIS_DATUM']}:</p>
<div class="gk-table-wrap"><table class="gk-table">
<thead><tr><th scope="col">Förbrukning</th><th scope="col">Bensin 95</th><th scope="col">Diesel</th></tr></thead>
<tbody>{rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor per mil. Bensin {p2(PB)} kr/l och diesel {p2(PD)} kr/l, inkl. moms. Priset på din mack kan skilja.</caption>
</table></div>

<h2>Hur mycket bensin drar bilen per mil?</h2>
<p>Det skiljer sig mellan bilar, så använd din egen bils värde. Anges förbrukningen i liter per 100 km delar du med 10: 6,5 l/100 km är 0,65 l/mil. Vill du veta exakt: tanka fullt två gånger och dela tankade liter med körda mil – räkna ut det i kortet <a href="#fH">Räkna ut förbrukningen</a>.</p>

<h2>Dela på bilresan</h2>
<p>Delar ni på bensinen delar ni bränslekostnaden med antalet som åker med. Vill ni också dela på slitage och bilens andra kostnader kan Skatteverkets skattefria milersättning för egen bil, <strong>{K['MILERS']} kr per mil</strong> 2026, vara ett riktmärke. Den ska täcka hela bilkostnaden, inte bara bränslet.</p>

<h2>Elbil: kostnad per mil</h2>
<p>Räkna kWh per mil × elpriset per kWh. Hemma är elpriset det du betalar för elen plus elnät, energiskatt och moms – <a href="/kalkylatorer/elkostnadskalkylator">räkna ut ditt elpris</a>. Vid publik laddning gäller operatörens pris, till exempel Preems riktpris {p2(K['LADD_PREEM'])} kr/kWh.</p>

<h2>Vanliga frågor om bränslekostnad</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['preem']}" target="_blank" rel="noopener">Preem – Drivmedelspriser för företagskunder</a> – listpris bensin 95 {p2(PB)} kr/l och diesel {p2(PD)} kr/l (bensin från 2 oktober, diesel från 1 oktober 2026), riktpris laddning {p2(K['LADD_PREEM'])} kr/kWh, alla inkl. moms. Hämtat {K['PRIS_DATUM']}.</li>
<li><a href="{SRC['trafa']}" target="_blank" rel="noopener">Trafikanalys – Körsträckor 2025</a> (17 april 2026) – privatägda personbilar {fmt(K['KOR_PRIVAT'])} mil, alla personbilar {fmt(K['KOR_ALLA'])} mil, elbilar och laddhybrider ungefär {fmt(K['KOR_LADDBAR'])} mil</li>
<li><a href="{SRC['skv']}" target="_blank" rel="noopener">Skatteverket – Belopp och procent 2026</a> – skattefri bilersättning för egen bil {K['MILERS']} kr per mil</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/leasingkalkylator"><span>Leasingkalkylator<small>Vad kostar bilen att leasa per månad?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/reseavdragskalkylator"><span>Reseavdrag<small>Kör du bil till jobbet? Se om du får avdrag</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/bil-och-energi"><span>Allt om bil och energi<small>Elpris, bilkostnad, förmånsbil och solceller</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-dm" type="application/json">{json.dumps({"K": K, "D": D})}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Vad kostar bilresan? Räkna ut bränslekostnaden", jsonld=ld)
            + S.header() + body + S.footer("Bränslepriset ändras ofta – fyll i priset på din mack."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var CFG = JSON.parse(document.getElementById('gk-dm').textContent), C = CFG.K, D = CFG.D;
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(v, 0) + ' kr'; };
  var kr10 = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var d2 = function (v) { return GK.fmt(v, 2); };
  var st = { typ: 'bensin', enh: 'km', pers: 1 };
  var NAMN = { bensin: 'bensin', diesel: 'diesel', el: 'el' };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc(); forb();
    });
  }
  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  /* Modell – samma som scripts/build_drivmedel.py */
  function resa(stracka, enhet, tur, forbr, pris, pers) {
    var mil = (enhet === 'km' ? stracka / 10 : stracka) * (tur ? 2 : 1), mangd = mil * forbr, kost = mangd * pris;
    return { mil: mil, mangd: mangd, kost: kost, permil: forbr * pris, perpers: kost / pers };
  }
  function perAr(forbr, pris, milAr) { return forbr * pris * milAr; }
  function forbrukning(liter, mil) { return liter / mil; }

  function setTyp(t) {
    var prev = st.typ, el = t === 'el', f = GK.parse($('forbr').value);
    st.typ = t;
    if ((prev === 'el') !== el || !isFinite(f) || f === D.FORBR[prev]) $('forbr').value = GK.fmt(D.FORBR[t], 1);
    $('pris').value = el ? '' : d2(C.PRIS[t]);
    $('forbrUnit').textContent = el ? 'kWh/mil' : 'l/mil';
    $('prisUnit').textContent = el ? 'kr/kWh' : 'kr/l';
    $('prisLabel').textContent = el ? 'Elpris per kWh' : 'Pris per liter';
    $('pris').placeholder = el ? 'ditt elpris' : '';
    $('forbrHint').textContent = el ? 'Exempel: 2,0 kWh/mil – fyll i din bils värde. Anges det i kWh/100 km: dela med 10.'
      : 'Exempel: 0,7 l/mil – fyll i din bils värde. Anges det i l/100 km: dela med 10.';
    $('prisHint').innerHTML = el ? 'Hemma: ditt elpris med elnät, skatt och moms (<a href="/kalkylatorer/elkostnadskalkylator">räkna ut det</a>). Publik laddning: priset i laddappen.'
      : 'Preems listpris för ' + (t === 'bensin' ? 'bensin 95' : 'diesel') + ' den ' + C.PRIS_DATUM + '. Priset på din mack kan skilja – ändra till ditt.';
    $('flLabel').textContent = el ? 'Laddade kWh' : 'Tankade liter';
    $('flUnit').textContent = el ? 'kWh' : 'liter';
  }
  seg('typ', setTyp);
  seg('enh', function (v) { st.enh = v; $('strUnit').textContent = v; });
  seg('pers', function (v) { st.pers = +v; });
  ['str', 'forbr', 'pris'].forEach(function (id) { $(id).addEventListener('input', calc); });
  $('tur').addEventListener('change', calc);
  ['fl', 'fm'].forEach(function (id) { $(id).addEventListener('input', forb); });
  $('pris').addEventListener('input', forb);
  GK.groupInput($('str'));

  function clear(msg) {
    $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'verdict', 'how'].forEach(function (id) { $(id).innerHTML = ''; });
  }

  function calc() {
    var s = val('str'), f = val('forbr'), p = val('pris'), el = st.typ === 'el', tur = $('tur').checked, n = st.pers;
    var eu = el ? 'kWh' : 'liter', fu = el ? 'kWh/mil' : 'l/mil', pu = el ? 'kr/kWh' : 'kr/l';
    if (!s) return clear('Fyll i hur långt du ska köra.');
    if (!f) return clear('Fyll i hur mycket bilen drar per mil.');
    if (!p) return clear(el ? 'Fyll i ditt elpris per kWh.' : 'Fyll i priset per liter.');
    var r = resa(s, st.enh, tur, f, p, n);
    $('resLabel').textContent = 'Bränslekostnad för resan' + (tur ? ' tur och retur' : '');
    $('resBig').textContent = GK.fmt(r.kost, 0);
    $('resSub').textContent = GK.fmt(r.mil, 1).replace(/,0$/, '') + ' mil ' + (tur ? 'tur och retur' : 'enkel resa') + ' · ' +
      GK.fmt(r.mangd, 1) + ' ' + eu + ' ' + (el ? 'el' : NAMN[st.typ]) + ' à ' + d2(p) + ' ' + pu + '.';
    var other = resa(s, st.enh, !tur, f, p, n);
    $('tiles').innerHTML = tile('Per mil', d2(r.permil) + ' kr', d2(f) + ' ' + fu + ' × ' + d2(p) + ' ' + pu) +
      tile('Per person', kr(r.perpers), n > 1 ? 'Delat på ' + n : 'Välj fler för att dela') +
      tile(el ? 'El som går åt' : 'Bränsle som går åt', GK.fmt(r.mangd, 1) + ' ' + eu) +
      tile(tur ? 'Enkel resa' : 'Tur och retur', kr(other.kost));

    var v = '', big = el ? f >= 8 : f >= 3;
    if (big) {
      v += verdict('warn', 'Har du fyllt i per 100 km?', 'Förbrukningen ska anges per mil. ' + GK.fmt(f, 1) + ' ' + (el ? 'kWh' : 'l') + '/100 km är ' + d2(f / 10) + ' ' + fu + ' – dela med 10.');
    }
    var milAr = el ? C.KOR_LADDBAR : C.KOR_PRIVAT, ar = perAr(f, p, milAr);
    v += verdict('info', 'Med snittkörning: ca ' + kr10(ar) + ' per år',
      (el ? 'Elbilar och laddhybrider körde i snitt ungefär ' : 'Privatägda personbilar körde i snitt ') + GK.fmt(milAr, 0) + ' mil 2025 (Trafikanalys). Med din förbrukning och ditt pris blir det ' + kr10(ar / 12) + ' i månaden.');
    if (n > 1) {
      var ms = r.mil * C.MILERS;
      v += verdict('info', 'Inklusive slitage: ' + kr(ms / n) + ' per person', 'Vill ni dela på hela bilkostnaden kan den skattefria milersättningen för egen bil, ' + C.MILERS + ' kr/mil 2026, vara ett riktmärke: ' + kr(ms) + ' för resan.');
    }
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p>Sträcka: ' + GK.fmt(s, 1).replace(/,0$/, '') + ' ' + st.enh + (st.enh === 'km' ? ' / 10' : '') + (tur ? ' × 2 (tur och retur)' : '') + ' = ' + GK.fmt(r.mil, 1).replace(/,0$/, '') + ' mil.</p>' +
      '<p>' + (el ? 'El' : 'Bränsle') + ': ' + GK.fmt(r.mil, 1).replace(/,0$/, '') + ' mil × ' + d2(f) + ' ' + fu + ' = ' + GK.fmt(r.mangd, 1) + ' ' + eu + '. Kostnad: ' + GK.fmt(r.mangd, 1) + ' × ' + d2(p) + ' ' + pu + ' = ' + kr(r.kost) + (n > 1 ? ', delat på ' + n + ' = ' + kr(r.perpers) + ' per person' : '') + '.</p>' +
      '<p>' + (el ? 'Elpriset är det du fyller i.' : 'Förvalt pris är Preems listpris den ' + C.PRIS_DATUM + ', inkl. moms.') + ' Vi räknar bara ' + (el ? 'el' : 'bränsle') + ' – inte slitage, försäkring, skatt eller värdeminskning.</p>';
  }

  function forb() {
    var l = val('fl'), m = val('fm'), el = st.typ === 'el', u = el ? 'kWh' : 'l';
    if (!l || !m) { $('fRes').innerHTML = ''; return; }
    var f = forbrukning(l, m), p = val('pris');
    $('fRes').innerHTML = '<div class="gk-tiles">' + tile('Förbrukning', d2(f) + ' ' + u + '/mil', 'Tankat delat med körda mil') +
      tile('Per 100 km', GK.fmt(f * 10, 1) + ' ' + u, p ? 'Kostar ' + d2(f * p) + ' kr per mil' : '') + '</div>' +
      '<button type="button" class="gk-btn" id="fUse" style="margin-top:12px">Använd ' + d2(f) + ' ' + u + '/mil i kalkylatorn</button>';
    $('fUse').addEventListener('click', function () {
      $('forbr').value = d2(f); calc();
      var res = document.querySelector('.gk-result'); if (res && res.scrollIntoView) res.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  setTyp('bensin');
  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "drivmedelskalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    cases = [
        (200, "km", False, 0.7, PB, 1),
        (47, "mil", True, 0.62, PD, 3),
        (380, "km", True, 1.85, 2.4, 2),
        (12.5, "mil", False, 0.55, 18.45, 4),
        (1155, "mil", False, 0.7, PB, 1),
    ]
    for c in cases:
        x = resa(*c)
        print(c, "->", "kost", fmt(x["kost"]), "per mil", fmt(x["permil"], 2), "per pers", fmt(x["perpers"]),
              "mängd", fmt(x["mangd"], 1), "år(privat)", kr10(per_ar(c[3], c[4], K["KOR_PRIVAT"])))
    print("förbrukning 42 l / 60 mil =", fmt(forbrukning(42, 60), 2), "; 51,3 / 74 =", fmt(forbrukning(51.3, 74), 2))
    print("Titel", len("Räkna ut bränslekostnad för bilresan 2026 | GratisKalkyl"))


if __name__ == "__main__":
    main()
