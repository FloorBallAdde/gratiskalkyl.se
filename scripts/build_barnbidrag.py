#!/usr/bin/env python3
"""Bygger kalkylatorer/barnbidragskalkylator.html i den nya verktygsmallen.

Regler och belopp 2026 (Försäkringskassan, kontrollerat 1 oktober 2026):
  - Barnbidrag 1 250 kr per barn och månad, delas mellan vårdnadshavarna. En av dem kan få hela
    om båda anmäler det.
  - Flerbarnstillägg (summa per familj och månad): 2 barn 150 kr, 3 barn 730 kr, 4 barn 1 740 kr.
    Från och med det femte barnet ytterligare 1 250 kr per barn (5 barn 2 990, 6 barn 4 240).
  - Delas barnbidraget lika delas även flerbarnstillägget lika (ett helt barnbidrag = 2 halvor).
  - Skattefritt. Betalas senast den 20:e varje månad.

Modell (samma i Python-referensen nedan och i sidans JS):
  barnbidrag = n × BB, tillägg = FB[n] (n ≤ 4) eller FB[4] + (n − 4) × FB_STEG, totalt = summan.
  Delas lika: totalt / 2 var. Per barn = totalt / n, avrundat till hela kronor.

    python3 scripts/build_barnbidrag.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/barnbidragskalkylator"
UPDATED = "1 oktober 2026"

# Byts vid årsskiftet. FB = flerbarnstillägg per familj och månad för 2–4 barn,
# FB_STEG = tillägget per barn från och med det femte barnet.
K = {"AR": 2026, "BB": 1250, "FB": {"2": 150, "3": 730, "4": 1740}, "FB_STEG": 1250, "MAX_N": 20}

SRC = {
    "belopp": "https://www.forsakringskassan.se/privatperson/e-tjanster-blanketter-och-informationsmaterial/aktuella-belopp",
    "fk": "https://www.forsakringskassan.se/privatperson/foralder/barnbidrag-och-flerbarnstillagg",
    "safunkar": "https://www.forsakringskassan.se/privatperson/familj-och-barn/barnbidrag-och-flerbarnstillagg/barnbidrag-och-flerbarnstillagg-sa-funkar-det",
    "andra": "https://www.forsakringskassan.se/privatperson/familj-och-barn/barnbidrag-och-flerbarnstillagg/andra-vem-som-ska-fa-barnbidraget-och-flerbarnstillagget",
    "16ar": "https://www.forsakringskassan.se/privatperson/familj-och-barn/barnbidrag-och-flerbarnstillagg/nar-barnet-fyller-16-ar-studiebidrag-eller-forlangt-barnbidrag",
}


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def r0(x):
    """Avrundning som Math.round i JS (halvor uppåt)."""
    return int(math.floor(x + 0.5))


def tillagg(n):
    if n < 2:
        return 0
    if n <= 4:
        return K["FB"][str(n)]
    return K["FB"]["4"] + (n - 4) * K["FB_STEG"]


def barnbidrag(n, delat=True):
    """Python-referens – samma logik som sidans JS. n = antal barn, delat = två vårdnadshavare delar lika."""
    bb = n * K["BB"]
    fb = tillagg(n)
    tot = bb + fb
    return {"n": n, "bb": bb, "fb": fb, "tot": tot, "ar": tot * 12, "per_barn": r0(tot / n),
            "var": tot / 2 if delat else tot, "delat": delat}


def kr(v):
    return fmt(v) + " kr"


T = {n: barnbidrag(n) for n in range(1, 11)}

FAQ = [
    ("Hur mycket är barnbidraget 2026?",
     f"{kr(K['BB'])} per barn och månad. Med två barn eller fler tillkommer flerbarnstillägg, så två barn ger "
     f"{kr(T[2]['tot'])} och tre barn {kr(T[3]['tot'])} i månaden till familjen."),
    ("Hur mycket blir barnbidraget för 3 barn 2026?",
     f"{kr(T[3]['tot'])} i månaden: 3 × 1 250 kr i barnbidrag plus {kr(T[3]['fb'])} i flerbarnstillägg. "
     f"Det blir {kr(T[3]['ar'])} om året. Delar två vårdnadshavare får ni {kr(T[3]['var'])} var."),
    ("Hur mycket får man i barnbidrag för 4, 5 eller 6 barn?",
     f"4 barn ger {kr(T[4]['tot'])}, 5 barn {kr(T[5]['tot'])} och 6 barn {kr(T[6]['tot'])} i månaden, "
     "flerbarnstillägget inräknat. Från det femte barnet ökar tillägget med 1 250 kr för varje barn."),
    ("Hur mycket får man i barnbidrag för 8 eller 10 barn?",
     f"8 barn ger {kr(T[8]['tot'])} i månaden och 10 barn {kr(T[10]['tot'])}. Av det är "
     f"{kr(T[10]['fb'])} flerbarnstillägg för 10 barn. Varje barn utöver fyra ger 2 500 kr mer i månaden: "
     "1 250 kr i barnbidrag och 1 250 kr i tillägg."),
    ("Varför står det 625 kr på Försäkringskassans sida?",
     "Försäkringskassan visar beloppet per förälder när två vårdnadshavare delar. Barnbidraget är 1 250 kr per barn, "
     "och hälften – 625 kr – betalas till var och en av er."),
    ("Är barnbidraget skattepliktigt?",
     "Nej. Det är ingen skatt på barnbidraget eller flerbarnstillägget, så beloppet du ser är det som kommer in på kontot."),
    ("När kommer barnbidraget?",
     "Pengarna kommer senast den 20:e varje månad. Första gången kommer de månaden efter att barnet har fötts. "
     "Du behöver inte ansöka – barnbidraget betalas ut automatiskt."),
    ("Kan en förälder få hela barnbidraget?",
     "Ja, om ni båda anmäler det till Försäkringskassan. Ändringen gäller tidigast från månaden efter att ni båda har "
     "signerat anmälan. Då får den föräldern även hela flerbarnstillägget."),
]

CHEV = S.ICON_CHEV


def table_rows():
    out = []
    for n in range(1, 11):
        r = T[n]
        out.append(f'<tr data-n="{n}"><td>{n} barn</td><td>{fmt(r["fb"]) if r["fb"] else "–"}</td>'
                   f'<td><strong>{fmt(r["tot"])}</strong></td><td>{fmt(r["var"])}</td></tr>')
    return "".join(out)


def page():
    title = "Barnbidrag 2026: 1 250 kr per barn – räkna ut | GratisKalkyl"
    desc = (f"Barnbidraget 2026 är 1 250 kr per barn och månad. Med flerbarnstillägg: 2 barn {kr(T[2]['tot'])}, "
            f"3 barn {kr(T[3]['tot'])}, 4 barn {kr(T[4]['tot'])}. Räkna ut för 1–10 barn.")
    crumbs = [("Hem", "/"), ("Familj & trygghet", "/familj-och-trygghet"), ("Barnbidragskalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Barnbidragskalkylator 2026",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Familj & trygghet", "item": S.SITE + "/familj-och-trygghet"},
            {"@type": "ListItem", "position": 3, "name": "Barnbidragskalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    nbtns = "".join(f'<button type="button" data-v="{n}" aria-pressed="{"true" if n == 2 else "false"}">{n}</button>'
                    for n in range(1, 11))

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Barnbidragskalkylator 2026</div>
<h1>Hur mycket är barnbidraget 2026?</h1>
<p class="gk-lead"><strong>1 250 kr per barn och månad</strong>, skattefritt – från två barn tillkommer flerbarnstillägg, som kalkylatorn räknar in.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Belopp för 2026 · Källa: <a href="{SRC['belopp']}" target="_blank" rel="noopener">Försäkringskassan</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="bbform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="antal">Antal barn</label>
<div class="gk-input"><input id="antal" inputmode="numeric" autocomplete="off" value="2"><span class="unit">barn</span></div>
<div class="gk-seg" style="--n:5" id="antalq" role="group" aria-label="Välj antal barn">
{nbtns}
</div>
<span class="gk-hint">Barn under 16 år. Barn på gymnasiet med studiebidrag räknas också med i flerbarnstillägget.</span>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur betalas barnbidraget ut?</legend>
<div class="gk-seg" style="--n:2" id="delning" role="group" aria-label="Hur barnbidraget betalas ut">
<button type="button" data-v="2" aria-pressed="true">Delas lika<small>två vårdnadshavare</small></button>
<button type="button" data-v="1" aria-pressed="false">Allt till en<small>en vårdnadshavare</small></button>
</div>
<span class="gk-hint">Har barnet två vårdnadshavare delas bidraget mellan er. Anmäler ni båda det kan en av er få allt.</span>
</fieldset>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:12px" aria-labelledby="tabH">
<h2 id="tabH" style="font-size:22px">Barnbidrag 2026 för 1–10 barn</h2>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="bbTable">
<thead><tr><th scope="col">Antal</th><th scope="col">Tillägg</th><th scope="col">Totalt</th><th scope="col">Hälften var</th></tr></thead>
<tbody>{table_rows()}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px;font-weight:500">Kronor per månad till familjen. Totalt = 1 250 kr per barn + flerbarnstillägg. Hälften var = om två vårdnadshavare delar på alla barnen.</caption>
</table></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Barnbidrag + flerbarnstillägg för 2 barn</div>
<div class="gk-big"><strong id="resBig">{fmt(T[2]['tot'])}</strong><span>kr/mån</span></div>
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
<a class="gk-linkcard" href="/artiklar/barnbidrag-2026"><span>Guide: Barnbidrag 2026<small>Utbetalningsdagar, regler och exempel</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/sparkalkylator"><span>Spara barnbidraget<small>Sparkalkylator – se vad ett månadssparande kan bli</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Gör en budget för familjen<small>Hushållsbudget – få med barnbidraget i kalkylen</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Barnbidrag och flerbarnstillägg 2026</h2>
<p>Barnbidraget är <strong>1 250 kr i månaden per barn</strong>. Har du två barn eller fler får familjen också flerbarnstillägg, ett belopp för hela familjen:</p>
<ul>
<li>2 barn: <strong>150 kr</strong></li>
<li>3 barn: <strong>730 kr</strong></li>
<li>4 barn: <strong>1 740 kr</strong></li>
<li>Från det femte barnet: <strong>1 250 kr mer</strong> för varje barn</li>
</ul>
<p>Det är ingen skatt på barnbidraget eller tillägget. Pengarna kommer senast den 20:e varje månad, och du behöver inte ansöka.</p>

<h2>Delas barnbidraget mellan föräldrarna?</h2>
<p>Ja. Har barnet två vårdnadshavare delas barnbidraget mellan er, alltså <strong>625 kr var per barn</strong>. Flerbarnstillägget fördelas efter hur många halva barnbidrag var och en får, så delar ni på alla barnen får ni hälften var. Vill ni att en av er ska få allt anmäler ni det båda till Försäkringskassan.</p>

<h2>Hur länge får man barnbidrag?</h2>
<p>Barnbidraget betalas för barn under 16 år. Den sista utbetalningen beror på när barnet fyller 16:</p>
<ul>
<li>Januari–mars: förlängt barnbidrag till och med juni</li>
<li>April–juni: sista barnbidraget i juni</li>
<li>Juli–september: sista i september</li>
<li>Oktober–december: sista i december</li>
</ul>
<p>Går barnet kvar i grundskolan eller anpassad skola förlängs barnbidraget – det är skolan som anmäler. På gymnasiet får barnet i stället studiebidrag från CSN, lika stort som barnbidraget. Barnet räknas då fortfarande med i flerbarnstillägget, som längst till och med juni det år det fyller 20.</p>

<h2>Vanliga frågor om barnbidrag</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['belopp']}" target="_blank" rel="noopener">Försäkringskassan – Aktuella belopp</a> – barnbidrag och flerbarnstillägg 2026 för 1–4 barn, 1 250 kr mer i tillägg från det femte barnet (uppdaterad 3 juli 2026)</li>
<li><a href="{SRC['fk']}" target="_blank" rel="noopener">Försäkringskassan – Barnbidrag och flerbarnstillägg</a> – delas mellan vårdnadshavarna, belopp per förälder för 1–6 barn, skattefritt, utbetalning senast den 20:e, automatiskt (uppdaterad 12 augusti 2026)</li>
<li><a href="{SRC['safunkar']}" target="_blank" rel="noopener">Försäkringskassan – Så funkar det</a> – flerbarnstillägget fördelas i halva barnbidrag</li>
<li><a href="{SRC['andra']}" target="_blank" rel="noopener">Försäkringskassan – Ändra vem som ska få barnbidraget</a> – en förälder kan få hela bidraget (uppdaterad 22 juni 2026)</li>
<li><a href="{SRC['16ar']}" target="_blank" rel="noopener">Försäkringskassan – När barnet fyller 16 år</a> – sista utbetalningen, förlängt barnbidrag, studiebidrag och flerbarnstillägg till 20 år (uppdaterad 20 juli 2026)</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/foraldrapenning"><span>Föräldrapenning<small>Hur mycket får du när du är föräldraledig?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/underhallsstod-kalkylator"><span>Underhållsstöd<small>Om ni inte bor tillsammans</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/ranta-pa-ranta"><span>Ränta på ränta<small>Så kan ett sparande växa över tid</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-bb" type="application/json">{json.dumps(K)}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Hur mycket är barnbidraget 2026? 1 250 kr per barn", jsonld=ld)
            + S.header() + body + S.footer("Beloppen gäller 2026 – Försäkringskassan beslutar om utbetalningen."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-bb').textContent);
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v), 0) + ' kr'; };
  var st = { delat: true };

  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', +x.getAttribute('data-v') === v ? 'true' : 'false'); }); }
  $('antalq').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    $('antal').value = b.getAttribute('data-v'); press('antalq', +b.getAttribute('data-v')); calc();
  });
  $('delning').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    st.delat = b.getAttribute('data-v') === '2'; press('delning', +b.getAttribute('data-v')); calc();
  });
  $('antal').addEventListener('input', function () { press('antalq', GK.parse($('antal').value)); calc(); });

  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  /* Modell – samma som scripts/build_barnbidrag.py */
  function tillagg(n) {
    if (n < 2) return 0;
    if (n <= 4) return C.FB[String(n)];
    return C.FB['4'] + (n - 4) * C.FB_STEG;
  }
  function barnbidrag(n, delat) {
    var bb = n * C.BB, fb = tillagg(n), tot = bb + fb;
    return { n: n, bb: bb, fb: fb, tot: tot, ar: tot * 12, per_barn: Math.round(tot / n), 'var': delat ? tot / 2 : tot, delat: delat };
  }

  function clear(msg) {
    $('resLabel').textContent = 'Barnbidrag per månad'; $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'how', 'verdict'].forEach(function (id) { $(id).innerHTML = ''; });
    $('bbTable').querySelectorAll('tbody tr').forEach(function (tr) { tr.classList.remove('is-you'); });
  }

  function calc() {
    var n = GK.parse($('antal').value);
    if (!isFinite(n) || n < 1 || n !== Math.round(n)) return clear('Fyll i antal barn.');
    if (n > C.MAX_N) return clear('Kalkylatorn räknar upp till ' + C.MAX_N + ' barn.');
    var r = barnbidrag(n, st.delat);
    $('resLabel').textContent = n === 1 ? 'Barnbidrag för 1 barn' : 'Barnbidrag + flerbarnstillägg för ' + n + ' barn';
    $('resBig').textContent = GK.fmt(r.tot, 0);
    $('resSub').textContent = (st.delat ? 'Till familjen i månaden – ' + kr(r['var']) + ' var till två vårdnadshavare.' : 'I månaden, allt till en förälder.') + ' Skattefritt.';
    $('tiles').innerHTML =
      tile(st.delat ? 'Varje förälder får' : 'En förälder får', kr(r['var']) + '/mån', st.delat ? 'Hälften av allt' : 'Hela beloppet') +
      tile('Per år', kr(r.ar), st.delat ? kr(r.ar / 2) + ' var' : '12 utbetalningar') +
      tile('Per barn', kr(r.per_barn) + '/mån', n > 1 ? 'Snitt med tillägget' : 'Barnbidraget') +
      tile('Flerbarnstillägg', kr(r.fb) + '/mån', n > 1 ? 'Ingår i summan' : 'Från 2 barn');

    var nx = barnbidrag(n + 1, st.delat);
    $('verdict').innerHTML = n === 1
      ? verdict('info', 'Flerbarnstillägg från två barn', 'Med två barn blir det ' + kr(nx.tot) + ' i månaden: 2 × ' + kr(C.BB) + ' i barnbidrag plus ' + kr(nx.fb) + ' i flerbarnstillägg.')
      : verdict('good', 'Flerbarnstillägget ger ' + kr(r.fb) + ' extra i månaden', 'Utan tillägget hade det varit ' + kr(r.bb) + '. Ett barn till ger ' + kr(nx.tot - r.tot) + ' mer i månaden.');

    $('how').innerHTML =
      '<p>Barnbidrag: ' + n + ' × ' + kr(C.BB) + ' = ' + kr(r.bb) + ' i månaden.</p>' +
      '<p>Flerbarnstillägg för ' + n + ' barn: ' + kr(r.fb) + '. Försäkringskassans belopp ' + C.AR + ' är 150 kr för 2 barn, 730 kr för 3 och 1 740 kr för 4 barn, och från det femte barnet 1 250 kr mer för varje barn.</p>' +
      '<p>Totalt: ' + kr(r.bb) + ' + ' + kr(r.fb) + ' = ' + kr(r.tot) + ' i månaden och ' + kr(r.ar) + ' om året. ' +
      (st.delat ? 'Delar två vårdnadshavare på alla barnen får ni hälften var, ' + kr(r['var']) + '. Har ni olika många barn var fördelas flerbarnstillägget i stället efter hur många halva barnbidrag var och en får. ' : '') +
      'Barnbidraget är skattefritt, så det dras ingen skatt.</p>';

    $('bbTable').querySelectorAll('tbody tr').forEach(function (tr) { tr.classList.toggle('is-you', +tr.getAttribute('data-n') === n); });
  }

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "barnbidragskalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    for n, delat in [(1, True), (2, True), (3, False), (5, True), (8, True), (10, False), (13, True)]:
        r = barnbidrag(n, delat)
        print(f"{n:>2} barn delat={delat!s:5}  bb {fmt(r['bb']):>7}  tillägg {fmt(r['fb']):>6}  totalt {fmt(r['tot']):>7}"
              f"  var {fmt(r['var']):>7}  per år {fmt(r['ar']):>8}  per barn {fmt(r['per_barn']):>6}")


if __name__ == "__main__":
    main()
