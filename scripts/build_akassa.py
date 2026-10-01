#!/usr/bin/env python3
"""Bygger kalkylatorer/akassa-kalkylator.html i den nya verktygsmallen.

Regler (lag 2024:506 om arbetslöshetsförsäkring och förordning 2024:1350, gäller från 1 oktober 2025):
  - Ersättningsgrundande inkomst = en tolftedel av arbetsinkomsten under de 12 månaderna före ansökan
    (5 kap. 2 §), högst 34 000 kr/mån (förordningen 7 §).
  - Inkomstvillkor: minst 120 000 kr under 12 månader och minst 11 000 kr i minst 4 av månaderna
    (förordningen 3–4 §§). Alternativ: 4 månader i följd med minst 11 000 kr → 66 dagar, och då räknas
    ersättningen på 11 000 kr.
  - Nivå: 80 % (medlem minst 12 mån), 60 % (medlem minst 6 mån), 50 % (annars, även icke-medlem via
    Alfa-kassan) – 5 kap. 4–6 §§. Efter 100 dagar −10 procentenheter, efter 200 dagar ytterligare −5 (5 kap. 10 §).
  - Dagar: 300 (11–12 månader med minst 11 000 kr), 200 (8–10), 100 (4–7), 66 (alternativet). En månad = 22
    ersättningsdagar (4 kap. 6 §). Karens 2 dagar (4 kap. 3 §). Från 20 års ålder (2 kap. 2 §).
  - Skatt: a-kassa ger inget jobbskatteavdrag. Netto räknas med assets/skatt2026.js / scripts/skatt2026.py.

    python3 scripts/build_akassa.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import skatt2026 as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/akassa-kalkylator"
UPDATED = "1 oktober 2026"

K = {"TAK": 34000, "MININK": 11000, "MINTOT": 120000, "DAGAR_MAN": 22, "KARENS": 2, "SNITT_KS": 32.38}
NIVA = {12: 80, 6: 60, 0: 50}

SRC = {
    "lag": "https://data.riksdagen.se/dokument/sfs-2024-506.html",
    "forordning": "https://lagen.nu/2024:1350",
    "alfa": "https://alfakassan.se/nya-regler-for-a-kassan-2025/",
    "skv": "https://www.skatteverket.se/jobbskatteavdrag",
    "akassor": "https://sverigesakassor.se/",
    "af": "https://arbetsformedlingen.se/",
}


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def akassa(lon, man, medl):
    """Python-referens – samma logik som sidans JS. lon = lön per månad de månader du jobbade,
    man = antal av de senaste 12 månaderna med minst 11 000 kr, medl = 12, 6 eller 0."""
    if lon < K["MININK"] or man < 4:
        return {"ok": False}
    tot = lon * man
    if tot >= K["MINTOT"]:
        alt, egi = False, min(K["TAK"], tot / 12)
        dagar = 300 if man >= 11 else 200 if man >= 8 else 100
    else:
        alt, egi, dagar = True, K["MININK"], 66
    p = NIVA[medl]
    perioder = []
    for i, (fr, ti, pp) in enumerate([(1, 100, p), (101, 200, p - 10), (201, 300, p - 15)]):
        if dagar < fr:
            break
        d = min(ti, dagar) - fr + 1
        perioder.append({"fran": fr, "till": fr + d - 1, "dagar": d, "procent": pp, "manad": egi * pp / 100})
    return {"ok": True, "alt": alt, "egi": egi, "dagar": dagar, "perioder": perioder,
            "total": sum(x["manad"] * x["dagar"] / K["DAGAR_MAN"] for x in perioder)}


def netto_akassa(manad, ks=K["SNITT_KS"]):
    return T.skatt_ar(manad * 12, kommunalskatt=ks, arbetsinkomst=0)["netto"] / 12


def netto_lon(manad, ks=K["SNITT_KS"]):
    return T.skatt_ar(manad * 12, kommunalskatt=ks)["netto"] / 12


MAX = akassa(45000, 12, 12)
MAXN = netto_akassa(MAX["perioder"][0]["manad"])
EX32 = akassa(32000, 12, 12)
EX32N = netto_akassa(EX32["perioder"][0]["manad"])

FAQ = [
    ("Hur mycket får man i a-kassa 2026?",
     "Har du varit medlem i en a-kassa i minst 12 månader får du 80 procent av din tidigare inkomst de första 100 dagarna, "
     "70 procent dag 101–200 och 65 procent dag 201–300. Inkomsten räknas som ett snitt av de 12 månaderna innan du blev "
     "arbetslös, och högst 34 000 kr i månaden räknas. Det ger som mest 27 200 kr i månaden före skatt de första 100 dagarna. "
     f"Med 32 000 kr i lön blir det {fmt(round(EX32['perioder'][0]['manad'], -1))} kr före skatt och ungefär "
     f"{fmt(round(EX32N, -1))} kr efter skatt med genomsnittlig kommunalskatt."),
    ("Hur mycket får man från Alfa-kassan?",
     "Alfa-kassan följer samma lag som alla andra a-kassor. Är du inte medlem får du 50 procent av din tidigare inkomst, "
     "upp till taket 34 000 kr. Har du varit medlem minst 6 månader får du 60 procent, och efter 12 månader 80 procent. "
     "Alfa-kassan är inte knuten till något fackförbund och alla kan gå med oavsett yrke."),
    ("Vad är taket i a-kassan?",
     "Taket är 34 000 kr i månaden. Tjänar du mer räknas ändå bara 34 000 kr. Det ger högst 27 200 kr i månaden dag 1–100, "
     "23 800 kr dag 101–200 och 22 100 kr dag 201–300, före skatt. Tjänar du mer än taket kan en inkomstförsäkring, ofta via "
     "ett fackförbund, täcka en del av mellanskillnaden."),
    ("Hur länge kan man få a-kassa?",
     "Det beror på hur många av de senaste 12 månaderna du har tjänat minst 11 000 kr. 11–12 månader ger 300 ersättningsdagar, "
     "8–10 månader 200 dagar och 4–7 månader 100 dagar. En månad räknas som 22 ersättningsdagar, så 300 dagar räcker i "
     "ungefär 13–14 månader."),
    ("Vad krävs för att få a-kassa?",
     "Du ska ha tjänat minst 120 000 kr de senaste 12 månaderna och minst 11 000 kr i minst 4 av månaderna. Har du inte tjänat "
     "120 000 kr men haft minst 11 000 kr fyra månader i följd kan du få 66 dagar, och då räknas ersättningen på 11 000 kr. "
     "Du ska också ha fyllt 20 år och vara inskriven som arbetssökande hos Arbetsförmedlingen."),
    ("Hur många karensdagar är det i a-kassan?",
     "Två. Ersättningen börjar betalas först när du har varit arbetslös i två dagar, och för de dagarna får du ingen ersättning."),
    ("Är a-kassan skattepliktig?",
     "Ja. A-kassan beskattas som inkomst av tjänst men ger inget jobbskatteavdrag, så skatten blir högre än på en lön av samma "
     f"storlek. Den högsta ersättningen, 27 200 kr i månaden, blir ungefär {fmt(round(MAXN, -1))} kr efter skatt med genomsnittlig "
     "kommunalskatt 2026."),
    ("Hur mycket är a-kassan per dag?",
     "Ersättningen betalas för 22 dagar i månaden, så dagbeloppet är månadsbeloppet delat med 22. Det högsta beloppet de första "
     f"100 dagarna är 27 200 kr i månaden, alltså ungefär {fmt(27200 / 22)} kr per dag före skatt."),
]

CHEV = S.ICON_CHEV


def page():
    with open(os.path.join(ROOT, "data", "kommunalskatt-2026.json"), encoding="utf-8") as f:
        kommuner = json.load(f)["kommuner"]
    opts = '<option value="32.38">Rikssnitt – 32,38 %</option>' + "".join(
        f'<option value="{v}">{S.e(n)} – {str(v).replace(".", ",")} %</option>' for n, v in kommuner)
    manopts = "".join(
        f'<option value="{m}"{" selected" if m == 12 else ""}>{m} månader{" – alla" if m == 12 else ""}</option>'
        for m in range(12, -1, -1))

    title = "A-kassa 2026 – räkna ut hur mycket du får | GratisKalkyl"
    desc = ("Räkna ut din a-kassa 2026 före och efter skatt: 80, 70 och 65 % av lönen upp till 34 000 kr, "
            "antal dagar och vad Alfa-kassan ger.")
    crumbs = [("Hem", "/"), ("Familj & trygghet", "/familj-och-trygghet"), ("A-kassekalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "A-kassekalkylator 2026",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Familj & trygghet", "item": S.SITE + "/familj-och-trygghet"},
            {"@type": "ListItem", "position": 3, "name": "A-kassekalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)

    ex = []
    for lon in (25000, 32000, 34000, 45000):
        r = akassa(lon, 12, 12)
        m1 = r["perioder"][0]["manad"]
        ex.append(f"<tr><td>{fmt(lon)} kr</td><td>{fmt(round(m1, -1))} kr</td><td>{fmt(round(netto_akassa(m1), -1))} kr</td>"
                  f"<td>{fmt(round(netto_lon(lon), -1))} kr</td></tr>")
    ex_rows = "".join(ex)

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">A-kassekalkylator 2026</div>
<h1>Hur mycket får du i a&#8209;kassa?</h1>
<p class="gk-lead">Räkna ut din ersättning före och efter skatt, hur länge du får den och hur mycket du tappar jämfört med lönen.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Regler från 1 oktober 2025 · Källa: <a href="{SRC['lag']}" target="_blank" rel="noopener">lagen om arbetslöshetsförsäkring</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="akform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="lon">Din lön per månad före skatt</label>
<div class="gk-input"><input id="lon" inputmode="numeric" autocomplete="off" value="32 000"><span class="unit">kr/mån</span></div>
<div class="gk-seg" style="--n:3" id="lonq" role="group" aria-label="Vanliga löner">
<button type="button" data-v="25000" aria-pressed="false">25 000</button>
<button type="button" data-v="34000" aria-pressed="false">34 000<small>taket</small></button>
<button type="button" data-v="45000" aria-pressed="false">45 000</button>
</div>
<span class="gk-hint">Snittet de månader du jobbade. Varierar lönen: ta ett snitt.</span>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Hur länge har du varit med i en a-kassa?</legend>
<div class="gk-seg" style="--n:3" id="medl" role="group" aria-label="Medlemstid i a-kassa">
<button type="button" data-v="12" aria-pressed="true">12 mån +<small>80 %</small></button>
<button type="button" data-v="6" aria-pressed="false">6–11 mån<small>60 %</small></button>
<button type="button" data-v="0" aria-pressed="false">Kortare / inte med<small>50 %</small></button>
</div>
</fieldset>

<div class="gk-field">
<label for="man">Månader med minst 11 000 kr i lön, senaste året</label>
<div class="gk-input"><select id="man">{manopts}</select></div>
<span class="gk-hint">Avgör hur många dagar du får. Månader utan lön sänker också snittet som ersättningen räknas på.</span>
</div>

<div class="gk-field">
<label for="kommun">Din kommun</label>
<div class="gk-input"><select id="kommun">{opts}</select></div>
</div>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:12px" aria-labelledby="perH">
<h2 id="perH" style="font-size:22px">Så förändras ersättningen</h2>
<figure style="margin:0">
<figcaption class="gk-hint" style="margin-bottom:8px" id="chartCap"></figcaption>
<div id="chart"></div>
</figure>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="perTable"></table></div>
</section>

<section class="gk-card gk-stack gk-o4" style="gap:14px" aria-labelledby="bufH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="bufH" style="font-size:22px">Hur länge räcker din buffert?</h2>
<p class="gk-hint">Se hur länge sparade pengar täcker skillnaden mellan lönen och a-kassan.</p>
</div>
<div class="gk-field">
<label for="buf">Sparade pengar du kan använda</label>
<div class="gk-input"><input id="buf" inputmode="numeric" autocomplete="off" placeholder="t.ex. 50 000"><span class="unit">kr</span></div>
</div>
<div id="bufRes" aria-live="polite"></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Din a-kassa de första 100 dagarna</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån före skatt</span></div>
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
<a class="gk-linkcard" href="{SRC['af']}" target="_blank" rel="noopener"><span>Skriv in dig hos Arbetsförmedlingen<small>Första dagen du är arbetslös – annars kan du inte få a-kassa</small></span>{CHEV}</a>
<a class="gk-linkcard" href="{SRC['akassor']}" target="_blank" rel="noopener"><span>Hitta din a-kassa<small>Sveriges a-kassor – alla 24 a-kassor och var du ansöker</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/hushallsbudget"><span>Gör en budget för perioden<small>Hushållsbudget – få ihop ekonomin med lägre inkomst</small></span>{CHEV}</a>
<!--GK-PARTNER:akassa:START--><!--GK-PARTNER:akassa:END-->
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknas a-kassan ut</h2>
<p>Sedan 1 oktober 2025 är a-kassan helt inkomstbaserad. Ersättningen räknas på <strong>en tolftedel av allt du har tjänat de 12 månaderna innan du blev arbetslös</strong> – månader utan lön räknas alltså som noll. Högst <strong>34 000 kr i månaden</strong> räknas. På det beloppet får du en procentsats som beror på hur länge du har varit med i en a-kassa:</p>
<ul>
<li><strong>80 %</strong> om du har varit medlem i minst 12 månader i följd.</li>
<li><strong>60 %</strong> om du har varit medlem minst de senaste 6 månaderna.</li>
<li><strong>50 %</strong> annars – även om du inte är medlem alls.</li>
</ul>
<p>Efter 100 dagar sänks procentsatsen med 10 procentenheter och efter 200 dagar med ytterligare 5. Med fullt medlemskap blir det 80, 70 och 65 %. Ersättningen betalas för 22 dagar i månaden.</p>
<div class="gk-table-wrap"><table class="gk-table">
<thead><tr><th scope="col">Lön</th><th scope="col">A-kassa dag 1–100</th><th scope="col">Efter skatt</th><th scope="col">Lönen efter skatt</th></tr></thead>
<tbody>{ex_rows}</tbody>
<caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Per månad, 12 månaders medlemskap och lön alla 12 månader. Skatt med genomsnittlig kommunalskatt 2026 (32,38 %).</caption>
</table></div>

<h2>Hur länge får man a-kassa?</h2>
<p>Antalet dagar beror på hur många av de senaste 12 månaderna du har tjänat minst 11 000 kr:</p>
<ul>
<li>11–12 månader: <strong>300 dagar</strong> (ungefär 13–14 månader)</li>
<li>8–10 månader: <strong>200 dagar</strong></li>
<li>4–7 månader: <strong>100 dagar</strong></li>
</ul>
<p>Har du inte tjänat 120 000 kr totalt men haft minst 11 000 kr fyra månader i följd kan du få 66 dagar, och då räknas ersättningen på 11 000 kr. När dagarna är slut kan du få aktivitetsstöd om du deltar i ett program hos Arbetsförmedlingen.</p>

<h2>Vad krävs för att få a-kassa?</h2>
<ul>
<li>Du har tjänat minst <strong>120 000 kr</strong> de senaste 12 månaderna, och minst <strong>11 000 kr</strong> i minst fyra av månaderna.</li>
<li>Du har fyllt 20 år.</li>
<li>Du är inskriven som arbetssökande hos Arbetsförmedlingen och söker jobb aktivt.</li>
</ul>
<p>Du får ingen ersättning för de två första dagarna du är arbetslös – det är karensdagarna.</p>

<h2>Alfa-kassan och om du inte är medlem</h2>
<p>Alla a-kassor följer samma lag, så nivåerna är desamma oavsett vilken du är med i. Är du inte med i någon a-kassa kan du ansöka hos <strong>Alfa-kassan</strong>, som är öppen för alla oavsett yrke, och få 50 % av din tidigare inkomst. Det gamla grundbeloppet för den som inte var medlem finns inte längre. Går du med i en a-kassa nu tar det 12 månader innan du når 80 %.</p>

<h2>Skatt på a-kassan</h2>
<p>A-kassan är skattepliktig men ger inget <a href="{SRC['skv']}" target="_blank" rel="noopener">jobbskatteavdrag</a>. Därför betalar du mer skatt på a-kassan än på en lön av samma storlek, och skillnaden mot din vanliga nettolön blir större än procentsatsen antyder. Kalkylatorn räknar skatten med samma regler som Skatteverkets skattetabeller 2026.</p>

<h2>Vanliga frågor om a-kassa</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['lag']}" target="_blank" rel="noopener">Lag (2024:506) om arbetslöshetsförsäkring</a> – inkomsten som en tolftedel av 12 månader (5 kap. 2 §), 80/60/50 % (5 kap. 4–6 §§), nedtrappning (5 kap. 10 §), 300/200/100/66 dagar och 22 dagar per månad (4 kap. 4–6 §§), två karensdagar (4 kap. 3 §), från 20 år (2 kap. 2 §)</li>
<li><a href="{SRC['forordning']}" target="_blank" rel="noopener">Förordning (2024:1350) om arbetslöshetsförsäkring</a> – tak 34 000 kr (7 §), 120 000 kr och 11 000 kr (3–4 §§)</li>
<li><a href="{SRC['alfa']}" target="_blank" rel="noopener">Alfa-kassan – Nya regler för a-kassan</a> – 50 % för den som inte är medlem</li>
<li><a href="{SRC['skv']}" target="_blank" rel="noopener">Skatteverket – Jobbskatteavdrag</a> – gäller arbetsinkomster, inte a-kassa</li>
<li>Kommunalskatt 2026: SCB</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/artiklar/a-kassa-2026-belopp-och-regler"><span>Guide: A-kassa 2026<small>Belopp, regler och räkneexempel</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/loneraknare"><span>Löneräknare<small>Vad blir kvar av lönen efter skatt?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/sjukpenningkalkylator"><span>Sjukpenning<small>Ersättning om du blir sjuk</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-ak" type="application/json">{json.dumps(K)}</script>
<script defer src="/assets/skatt2026.js?v=20261001"></script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Hur mycket får du i a-kassa? Kalkylator 2026", jsonld=ld)
            + S.header() + body + S.footer("A-kassan är en uppskattning – din a-kassa beslutar om ersättningen."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-ak').textContent);
  var T = window.GKSkatt2026;
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var NIVA = { 12: 80, 6: 60, 0: 50 };
  var st = { medl: 12 };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', +x.getAttribute('data-v') === v ? 'true' : 'false'); }); }
  seg('lonq', function (v) { $('lon').value = GK.fmt(+v, 0); });
  seg('medl', function (v) { st.medl = +v; });
  $('lon').addEventListener('input', function () { press('lonq', GK.parse($('lon').value)); calc(); });
  ['man', 'kommun'].forEach(function (id) { $(id).addEventListener('change', calc); });
  $('buf').addEventListener('input', calc);
  ['lon', 'buf'].forEach(function (id) { GK.groupInput($(id)); });

  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }

  /* Modell – samma som scripts/build_akassa.py */
  function akassa(lon, man, medl) {
    if (lon < C.MININK || man < 4) return { ok: false };
    var tot = lon * man, alt, egi, dagar;
    if (tot >= C.MINTOT) { alt = false; egi = Math.min(C.TAK, tot / 12); dagar = man >= 11 ? 300 : (man >= 8 ? 200 : 100); }
    else { alt = true; egi = C.MININK; dagar = 66; }
    var p = NIVA[medl], per = [], total = 0;
    [[1, 100, p], [101, 200, p - 10], [201, 300, p - 15]].forEach(function (x) {
      if (dagar < x[0]) return;
      var d = Math.min(x[1], dagar) - x[0] + 1, m = egi * x[2] / 100;
      per.push({ fran: x[0], till: x[0] + d - 1, dagar: d, procent: x[2], manad: m });
      total += m * d / C.DAGAR_MAN;
    });
    return { ok: true, alt: alt, egi: egi, dagar: dagar, perioder: per, total: total };
  }
  function nAk(m, ks) { return T.skattAr(m * 12, { arbetsinkomst: 0, kommunalskatt: ks }).netto / 12; }
  function nLon(m, ks) { return T.skattAr(m * 12, { kommunalskatt: ks }).netto / 12; }
  function clear(msg) {
    $('resLabel').textContent = 'Din a-kassa'; $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'how', 'chart', 'chartCap', 'perTable', 'bufRes'].forEach(function (id) { $(id).innerHTML = ''; });
  }

  function calc() {
    var lon = val('lon'), man = +$('man').value, ks = +$('kommun').value, medl = st.medl;
    if (!lon || lon < 1000) { $('verdict').innerHTML = ''; return clear('Fyll i din lön.'); }
    var r = akassa(lon, man, medl);
    if (!r.ok) {
      clear('Du uppfyller inte inkomstvillkoret.');
      $('verdict').innerHTML = verdict('info', 'Du får troligen ingen a-kassa', 'För att få a-kassa ska du ha tjänat minst 11 000 kr i månaden under minst 4 av de senaste 12 månaderna, och minst 120 000 kr totalt (eller 11 000 kr fyra månader i följd). Kontakta en a-kassa om du är osäker – de gör den exakta bedömningen.');
      return;
    }
    var p1 = r.perioder[0], netL = nLon(lon, ks), net1 = nAk(p1.manad, ks), fall = netL - net1;
    $('resLabel').textContent = r.alt ? 'Din a-kassa i 66 dagar' : 'Din a-kassa de första 100 dagarna';
    $('resBig').textContent = GK.fmt(Math.round(p1.manad / 10) * 10, 0);
    $('resSub').textContent = 'Ungefär ' + kr(net1) + ' efter skatt i månaden – ' + GK.fmt(net1 / netL * 100, 0) + ' % av din lön efter skatt (' + kr(netL) + '). ' + kr(p1.manad / C.DAGAR_MAN) + ' per dag före skatt.';
    var man_tot = r.dagar / C.DAGAR_MAN;
    $('tiles').innerHTML = tile('Efter skatt', kr(net1) + '/mån', 'Dag 1–' + p1.till) +
      tile('Du tappar', kr(fall) + '/mån', 'Jämfört med lönen efter skatt') +
      tile('Så länge', r.dagar + ' dagar', 'Ungefär ' + GK.fmt(man_tot, 1).replace(/,0$/, '') + ' månader') +
      tile('Totalt före skatt', kr(r.total), 'Om du är arbetslös alla dagarna');

    var v = '';
    if (r.alt) {
      v += verdict('info', 'Du får 66 dagar, räknat på 11 000 kr', 'Du har inte tjänat 120 000 kr de senaste 12 månaderna. Har du haft minst 11 000 kr fyra månader i följd kan du ändå få a-kassa i 66 dagar, och då räknas ersättningen på 11 000 kr i månaden.');
    } else if (lon * man / 12 > C.TAK) {
      v += verdict('warn', 'Du tjänar över taket', 'A-kassan räknar bara 34 000 kr av din inkomst. Därför får du ' + GK.fmt(net1 / netL * 100, 0) + ' % av din nettolön, inte ' + p1.procent + ' %. En inkomstförsäkring, ofta via ett fackförbund, kan täcka en del av mellanskillnaden.');
    } else if (man < 12) {
      v += verdict('info', 'Snittet blir lägre än din lön', 'Ersättningen räknas på en tolftedel av årets inkomst. Med lön ' + man + ' av 12 månader räknas ' + kr(lon * man / 12) + ' i månaden i stället för ' + kr(lon) + '.');
    }
    if (medl < 12) {
      var full = akassa(lon, man, 12), extra = full.perioder[0].manad - p1.manad;
      v += verdict('warn', 'Med 12 månaders medlemskap: ' + kr(extra) + ' mer i månaden', 'Du får ' + p1.procent + ' % i stället för 80 %. Går du med i en a-kassa nu tar det 12 månader innan du når 80 %. Är du inte med i någon a-kassa ansöker du hos Alfa-kassan, som är öppen för alla.');
    } else if (!r.alt && lon * man / 12 <= C.TAK && man === 12) {
      v += verdict('good', 'Du får full a-kassa', '80 % av din lön de första 100 dagarna, och du ligger under taket på 34 000 kr.');
    }
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p>Inkomsten som räknas: ' + kr(lon) + ' × ' + man + ' månader / 12 = ' + kr(lon * man / 12) + (r.alt ? ' – men eftersom du inte når 120 000 kr räknas 11 000 kr (66 dagar).' : (lon * man / 12 > C.TAK ? ', högst 34 000 kr räknas.' : '.')) + '</p>' +
      '<p>Nivå: ' + NIVA[medl] + ' % de första 100 dagarna (' + (medl === 12 ? 'medlem minst 12 månader' : medl === 6 ? 'medlem 6–11 månader' : 'kortare medlemskap eller inte medlem') + '), därefter 10 respektive 15 procentenheter lägre. En månad är 22 ersättningsdagar. De två första dagarna (karens) får du ingen ersättning – det motsvarar ' + kr(2 * p1.manad / C.DAGAR_MAN) + '.</p>' +
      '<p>Skatten räknas med samma regler som Skatteverkets skattetabeller 2026 och ' + GK.fmt(ks, 2) + ' % kommunalskatt. A-kassan ger inget jobbskatteavdrag, lönen gör det. Vi räknar som om inkomsten är densamma hela året.</p>';

    $('perTable').innerHTML = '<thead><tr><th scope="col">Dagar</th><th scope="col">Före skatt</th><th scope="col">Efter skatt</th></tr></thead><tbody>' +
      r.perioder.map(function (x) { return '<tr><td>' + x.fran + '–' + x.till + '<small class="gk-hint" style="display:block">' + x.procent + ' %</small></td><td>' + GK.fmt(Math.round(x.manad / 10) * 10, 0) + '</td><td>' + GK.fmt(Math.round(nAk(x.manad, ks) / 10) * 10, 0) + '</td></tr>'; }).join('') +
      '</tbody><caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor per månad. Din lön efter skatt: ' + kr(netL) + '.</caption>';

    chart(r, ks, netL);
    buffer(r, ks, netL);
  }

  function chart(r, ks, netL) {
    var W = Math.max(300, Math.min(760, $('chart').clientWidth || 600)), H = W < 500 ? 190 : 210, L = 44, R = 12, Tp = 14, B = 30;
    var totM = r.dagar / C.DAGAR_MAN, span = totM + 1.5;
    var step = [5000, 10000].filter(function (s) { return netL / s <= 5; })[0] || 10000, hi = Math.ceil(netL * 1.1 / step) * step;
    var x = function (m) { return L + m / span * (W - L - R); }, y = function (v) { return Tp + (hi - v) / hi * (H - Tp - B); };
    var g = '';
    for (var t = 0; t <= hi; t += step) g += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(t) + '" y2="' + y(t) + '" stroke="var(--gk-border)"/><text x="' + (L - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end" font-size="11" fill="var(--gk-muted)">' + (t ? Math.round(t / 1000) + ' tkr' : '0') + '</text>';
    var m0 = 0, bars = '';
    r.perioder.forEach(function (p) {
      var m1 = m0 + p.dagar / C.DAGAR_MAN, n = nAk(p.manad, ks);
      bars += '<rect x="' + (x(m0) + 1) + '" y="' + y(n) + '" width="' + Math.max(1, x(m1) - x(m0) - 2) + '" height="' + (y(0) - y(n)) + '" rx="3" fill="var(--gk-accent)"/>';
      bars += '<text x="' + ((x(m0) + x(m1)) / 2) + '" y="' + (y(n) - 5) + '" text-anchor="middle" font-size="11" font-weight="700" fill="var(--gk-ink)">' + p.procent + ' %</text>';
      m0 = m1;
    });
    for (var k = 0; k <= Math.floor(span); k += (span > 8 ? 3 : 1)) g += '<text x="' + x(k) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="11" fill="var(--gk-muted)">' + k + '</text>';
    var line = '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(netL) + '" y2="' + y(netL) + '" stroke="var(--gk-ink-2)" stroke-width="2" stroke-dasharray="6 4"/>';
    $('chartCap').textContent = 'A-kassa efter skatt per månad. Vågrätt: antal månader som arbetslös. Streckad linje: din lön efter skatt.';
    $('chart').innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="A-kassa efter skatt ' + r.perioder.map(function (p) { return kr(nAk(p.manad, ks)); }).join(', ') + ' per månad mot lönen ' + kr(netL) + '" style="display:block;font-family:inherit">' + g + bars + line + '</svg>';
  }

  function buffer(r, ks, netL) {
    var b = val('buf');
    if (!b || b < 100) { $('bufRes').innerHTML = ''; return; }
    var left = b, m = 0, d = 0;
    while (left > 0 && m < 60) {
      d += C.DAGAR_MAN;
      var p = null; r.perioder.forEach(function (x) { if (d - C.DAGAR_MAN + 1 >= x.fran && d - C.DAGAR_MAN + 1 <= x.till) p = x; });
      var gap = netL - (p ? nAk(p.manad, ks) : 0);
      if (gap <= 0) { m = 60; break; }
      if (left < gap) { m += left / gap; left = 0; break; }
      left -= gap; m += 1;
    }
    var txt = m >= 60 ? 'mer än 5 år' : 'ungefär ' + GK.fmt(m, 1).replace(/,0$/, '') + ' månader';
    var slut = m * C.DAGAR_MAN > r.dagar;
    $('bufRes').innerHTML = '<div class="gk-tiles">' + tile('Bufferten räcker', txt, 'Täcker skillnaden mot lönen efter skatt') +
      tile('Skillnad per månad', kr(netL - nAk(r.perioder[0].manad, ks)), 'Dag 1–' + r.perioder[0].till) + '</div>' +
      (slut ? verdict('info', 'A-kassan tar slut innan bufferten', 'Efter ' + r.dagar + ' dagar får du ingen a-kassa, och då behöver bufferten täcka hela lönen.') : '');
  }

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "akassa-kalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    for lon, man, medl in [(32000, 12, 12), (45000, 12, 12), (25000, 9, 6), (20000, 5, 0)]:
        r = akassa(lon, man, medl)
        print(lon, man, medl, r["dagar"], [round(p["manad"]) for p in r["perioder"]], round(r["total"]),
              "netto1", round(netto_akassa(r["perioder"][0]["manad"])), "nettolön", round(netto_lon(lon)))


if __name__ == "__main__":
    main()
