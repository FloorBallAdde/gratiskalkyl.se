#!/usr/bin/env python3
"""Bygger startsidan (index.html) i den nya designen.

    python3 scripts/build_start.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402
import build_amnen as A  # noqa: E402

ROOT = A.ROOT

QUICK = [("Nettolön", "/kalkylatorer/loneraknare"), ("Elavtal", "/kalkylatorer/elkostnadskalkylator"),
         ("Löneförhandling", "/kalkylatorer/loneforhandling"), ("Bolån", "/kalkylatorer/bolanekalkylator"),
         ("CSN", "/kalkylatorer/csn-kalkylator")]

# Mest besökta enligt Google Search Console (sep 2026; samma topp 5 i klick 4 jul–2 okt)
POPULAR = [("CSN – återbetalning", "/kalkylatorer/csn-kalkylator"), ("Elkostnad", "/kalkylatorer/elkostnadskalkylator"),
           ("Sjukpenning", "/kalkylatorer/sjukpenningkalkylator"), ("Leasing", "/kalkylatorer/leasingkalkylator"),
           ("A-kassa", "/kalkylatorer/akassa-kalkylator")]

TOOLS = [
    ("kr", "Vad borde jag tjäna?", "Din lön mot yrket i SCB:s statistik", "/kalkylatorer/loneforhandling"),
    ("el", "Vad borde elen kosta?", "Ditt elpris mot snittet i ditt elområde", "/kalkylatorer/elkostnadskalkylator"),
    ("%", "Vilken bolåneränta borde jag ha?", "Din ränta mot bankernas snitträntor", None),
    ("bil", "Vad kostar bilen att leasa?", "Och vilka bilar som kostar lika mycket", None),
    ("rot", "Vad kostar renoveringen?", "Badrum, tak och målning – med ROT", None),
    ("hem", "Vad kostar det att bo här?", "Skatt och avgifter i din kommun", None),
]

# Rensning 3 okt 2026 (GSC 4 jul–2 okt): nettolönsguiden (31 visningar på 3 mån) ersatt av CSN-guiden
# (42 947 visningar, sajtens mest visade sida). Deklarationsguiderna är från 30 sep – för nya för att bedömas.
FEATURED_GUIDES = ["/artiklar/deklaration-2027", "/artiklar/skatteaterbaring-2027", "/artiklar/csn-2026-belopp-och-regler",
                   "/artiklar/elkostnad-2026-sa-raknar-du", "/artiklar/hur-mycket-far-jag-lana-2026", "/artiklar/vad-ar-ranta-pa-ranta"]

MIN_EMPTY = [
    ("lon", "Min lön", "Lägg till", "Se vad du borde tjäna i ditt yrke", "/kalkylatorer/loneforhandling", "Kom igång"),
    ("el", "Min el", "Lägg till", "Se om ditt elavtal är rimligt", "/kalkylatorer/elkostnadskalkylator", "Kom igång"),
    ("csn", "Mitt CSN-lån", "Lägg till", "Se vad du betalar per månad och när du är klar", "/kalkylatorer/csn-kalkylator", "Kom igång"),
    ("bolan", "Mitt bolån", "Snart", "Jämför din ränta med bankernas snitt", "/kalkylatorer/bolanekalkylator", "Räkna på bolånet"),
]


def page():
    idx = A.load_index()
    all_calcs = []
    seen = set()
    for _, _, _, links in S.TOPICS:
        for t, u in links:
            if "yrkeslon" in u or u in seen:
                continue
            seen.add(u)
            x = idx.get(u)
            all_calcs.append(((x["title"] if x else t), u))
    all_calcs.sort(key=lambda x: x[0].lower().replace("å", "{").replace("ä", "|").replace("ö", "}"))
    n = len(all_calcs)
    n_guides = len([1 for x in idx.values() if x.get("type") == "guide"])

    title = f"GratisKalkyl.se – vad borde det kosta? {n} gratis kalkylatorer"
    desc = (f"Räkna, jämför och se om du betalar rätt – lön, el, bolån, skatt och sparande. {n} gratis kalkylatorer "
            "med officiella siffror från SCB, Skatteverket och Försäkringskassan. Ingen inloggning.")
    ld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": "GratisKalkyl.se", "url": S.SITE,
         "description": "Gratis kalkylatorer för privatekonomi – neutrala, snabba och med officiella siffror.",
         "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": S.SITE + "/?q={search_term_string}"},
                             "query-input": "required name=search_term_string"}},
        {"@context": "https://schema.org", "@type": "ItemList", "name": "Gratis kalkylatorer för privatekonomi 2026", "url": S.SITE,
         "numberOfItems": n, "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t, "url": S.SITE + u}
                                                  for i, (t, u) in enumerate(all_calcs)]},
    ]

    chips = "".join(f'<a class="gk-chip" href="{u}">{S.e(t)}</a>' for t, u in QUICK)
    min_cards = "".join(
        f'<a class="gk-mcard empty" id="min-{k}" href="{u}"><span class="l">{S.e(l)}</span><span class="v">{S.e(v)}</span>'
        f'<span class="s">{S.e(s)}</span><span class="d"></span><span class="a">{S.e(a)} →</span></a>'
        for k, l, v, s, u, a in MIN_EMPTY)
    tools = "".join(A.tcard(*t) for t in TOOLS)
    popular = "".join(
        f'<li><a href="{u}"><span>{i + 1}</span><span>{S.e(t)}</span>{S.ICON_CHEV}</a></li>' for i, (t, u) in enumerate(POPULAR))
    hubs = []
    for name, sub, hub, links in S.TOPICS:
        if not hub:
            continue
        ex = ", ".join(t.split(" – ")[0] for t, _ in links[:4])
        hubs.append(f'<a class="gk-hubcard" href="{hub}"><span class="t">{S.e(name)}{S.ICON_CHEV}</span>'
                    f'<span class="x">{S.e(ex)}</span><span class="n">{len(links)} verktyg</span></a>')
    az = "".join(f'<li><a href="{u}">{S.e(t)}</a></li>' for t, u in all_calcs)
    guides = A.guidecards(idx, FEATURED_GUIDES)

    body = f"""
<main id="innehall">
<section class="gk-hero">
<div class="gk-wrap gk-hero-in">
<div class="gk-hero-main">
<div class="gk-eyebrow">Lön · boende · bil · el · skatt</div>
<h1>Vad borde det kosta?</h1>
<p class="gk-lead">Räkna, jämför och fatta rätt beslut – med officiella siffror. Gratis, utan inloggning.</p>
<label class="gk-search"><span class="gk-sr">Vad vill du räkna på?</span>{S.ICON_SEARCH}<input type="search" id="search" data-search-dropdown="auto" placeholder="t.ex. elavtal, lön sjuksköterska, bolån" autocomplete="off" spellcheck="false"></label>
<div class="gk-chips">{chips}</div>
<div class="gk-src">{S.ICON_CHECK}<span>Källor: SCB, Skatteverket, Försäkringskassan och Energimyndigheten</span></div>
</div>
<div class="gk-stack" style="gap:10px">
<h2 style="font-family:var(--gk-font);font-size:16px;font-weight:700;color:var(--gk-muted)">Mest använda</h2>
<ul class="gk-rank">{popular}</ul>
</div>
</div>
</section>

<div class="gk-wrap">
<section class="gk-sec" id="min-ekonomi" aria-labelledby="h-min">
<div class="gk-sec-head"><div><h2 id="h-min">Min ekonomi</h2></div><button class="gk-textbtn" type="button" id="minClear" hidden>Radera mina siffror</button></div>
<p class="gk-hint" id="minSub">Spara dina siffror från elkollen, löneförhandlingen och CSN-kalkylatorn – så ser du här om du fortfarande ligger rätt. Sparas bara i din webbläsare, vi ser dem aldrig.</p>
<div class="gk-grid2 gk-grid4">{min_cards}</div>
</section>

<section class="gk-sec" aria-labelledby="h-jamfor">
<div class="gk-sec-head"><div><span class="gk-kicker">Jämför</span><h2 id="h-jamfor">Betalar du rätt?</h2></div></div>
<div class="gk-guides">{tools}</div>
</section>

<section class="gk-sec" aria-labelledby="h-amnen">
<div class="gk-sec-head"><div><span class="gk-kicker">Räkna</span><h2 id="h-amnen">Alla kalkylatorer efter ämne</h2></div></div>
<p class="gk-hint">Varje ämne samlar kalkylatorer, jämförelser och guider på ett ställe.</p>
<div class="gk-guides">{''.join(hubs)}</div>
</section>

<section class="gk-band">
<div style="display:flex;flex-direction:column;gap:8px"><span class="k">Inför deklarationen 2027</span><span class="h">När kommer skatteåterbäringen – och hur mycket blir den?</span></div>
<a class="gk-btn" href="/kalkylatorer/skatteaterbarings-kalkylator">Räkna ut återbäringen</a>
</section>

<section class="gk-sec" id="kalkylatorer" aria-labelledby="h-az">
<div class="gk-sec-head"><div><h2 id="h-az">Alla {n} kalkylatorer A–Ö</h2></div></div>
<details class="gk-azd" id="azd"><summary>Visa alla {n} kalkylatorer</summary><ul class="gk-az">{az}</ul></details>
</section>

<section class="gk-sec" aria-labelledby="h-guider">
<div class="gk-sec-head"><div><span class="gk-kicker">Lär dig</span><h2 id="h-guider">Guider</h2></div><a href="/artiklar/" style="font-weight:700;font-size:15px">Alla {n_guides} guider →</a></div>
<div class="gk-guides">{guides}</div>
</section>

<section class="gk-sec" aria-labelledby="h-lofte">
<div class="gk-sec-head"><div><h2 id="h-lofte">Vårt löfte</h2></div></div>
<div class="gk-promise">
<div><strong>Oberoende</strong><span>Vi säljer inga finansiella produkter. Annonser och märkta samarbetslänkar påverkar aldrig uträkningarna.</span></div>
<div><strong>Dina siffror stannar hos dig</strong><span>Allt räknas i din webbläsare och vi sparar aldrig det du fyller i. Ingen inloggning. Vi använder Google Analytics för anonym besöksstatistik.</span></div>
<div><strong>Officiella källor</strong><span>Regler och siffror från SCB, Skatteverket, Försäkringskassan och Energimyndigheten – med källa och datum.</span></div>
</div>
</section>
</div>
</main>
<script>
{JS}
</script>
"""
    return S.head(title, desc, "/", og_title="GratisKalkyl.se – vad borde det kosta?", jsonld=ld) + S.header() + body + S.footer()


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var MN = ['jan','feb','mar','apr','maj','jun','jul','aug','sep','okt','nov','dec'];
  function d(iso) { if (!iso) return ''; var p = iso.split('-'); return +p[2] + ' ' + MN[+p[1] - 1]; }
  function mtext(ym) { if (!ym) return ''; var p = ym.split('-'); return MN[+p[1] - 1] + ' ' + p[0]; }
  function kr(v) { return GK.fmt(Math.round(Math.abs(v) / 10) * 10, 0) + ' kr'; }
  function card(id, o) {
    var el = document.getElementById(id); if (!el) return;
    el.classList.remove('empty'); el.href = o.href;
    el.innerHTML = '<span class="l">' + o.l + '</span><span class="v">' + o.v + '</span><span class="s ' + (o.cls || '') + '">' + o.s + '</span>' +
      '<span class="d">' + (o.d || '') + '</span><span class="a">' + o.a + ' →</span>';
  }
  var all = GK.ekonomi.all(), n = 0;
  var el = all.el;
  if (el && el.kwh) {
    n++;
    var o = { l: 'Min el', href: '/kalkylatorer/elkostnadskalkylator', d: 'Sparat ' + d(el.sparad) + (el.manad ? ' · jämfört med ' + mtext(el.manad) : '') };
    if (el.avtal === 'anvisat') { o.v = 'Anvisat avtal'; o.s = 'Oftast dyrare än ett avtal du väljer själv'; o.cls = 'warn'; o.a = 'Se vad du kan spara'; }
    else if (el.prisOre != null) {
      o.v = GK.fmt(el.prisOre, 1) + ' öre/kWh';
      if (el.diffKrAr >= 50) { o.s = 'Ca ' + kr(el.diffKrAr) + '/år dyrare än snittet'; o.cls = 'warn'; o.a = 'Jämför avtal'; }
      else if (el.diffKrAr <= -50) { o.s = 'Ca ' + kr(el.diffKrAr) + '/år billigare än snittet'; o.cls = 'good'; o.a = 'Uppdatera'; }
      else { o.s = 'I nivå med snittet'; o.cls = 'good'; o.a = 'Uppdatera'; }
    } else { o.v = GK.fmt(el.kwh, 0) + ' kWh/år'; o.s = 'Ca ' + kr(el.kostnadKrAr) + '/år för elen i snitt'; o.a = 'Jämför ditt pris'; }
    card('min-el', o);
  }
  var lon = all.lon;
  if (lon && lon.lon) {
    n++;
    var p = lon.percentil;
    card('min-lon', { l: 'Min lön', v: GK.fmt(lon.lon, 0) + ' kr',
      s: lon.under ? 'Under ' + (lon.refTyp === 'alder' ? 'snittet för din ålder' : 'medianen') + ' i yrket' : 'På eller över nivån i yrket' + (p ? ' (' + p + ':e percentilen)' : ''),
      cls: lon.under ? 'warn' : 'good', d: (lon.yrkesNamn || '') + ' · sparat ' + d(lon.sparad),
      a: 'Förhandla', href: '/kalkylatorer/loneforhandling' + (lon.yrke ? '?yrke=' + encodeURIComponent(lon.yrke) : '') });
  }
  var csn = all.csn;
  if (csn && csn.skuld) {
    n++;
    var yNu = new Date().getFullYear();
    card('min-csn', { l: 'Mitt CSN-lån', v: GK.fmt(Math.round(csn.manadKr / 10) * 10, 0) + ' kr/mån',
      s: 'Klar ' + csn.klarAr + (csn.klarAr - yNu >= 0 ? ' – om ' + (csn.klarAr - yNu) + ' år' : ''), cls: 'good',
      d: GK.fmt(csn.skuld, 0) + ' kr i skuld · sparat ' + d(csn.sparad), a: 'Uppdatera', href: '/kalkylatorer/csn-kalkylator' });
  }
  if (n) {
    document.getElementById('minSub').textContent = 'Dina sparade siffror – sparas bara i den här webbläsaren. Uppdatera när något ändras.';
    var c = document.getElementById('minClear'); c.hidden = false;
    c.addEventListener('click', function () { GK.ekonomi.clear(); location.reload(); });
    if (typeof gtag === 'function') gtag('event', 'min_ekonomi_visa', { antal: n });
  }
  var azd = document.getElementById('azd');
  function az() { if (window.innerWidth >= 900 || location.hash === '#kalkylatorer') azd.open = true; }
  az(); window.addEventListener('hashchange', az);
  var q = new URLSearchParams(location.search).get('q');
  if (q) { var s = document.getElementById('search'); s.value = q; s.focus(); s.dispatchEvent(new Event('input')); }
});
"""


def main():
    html_text = page()
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")


if __name__ == "__main__":
    main()
