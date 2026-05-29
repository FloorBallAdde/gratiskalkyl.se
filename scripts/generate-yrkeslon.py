#!/usr/bin/env python3
"""
Programmatic SEO-generator för yrkeslön-sidor på GratisKalkyl.se.

Kör: python3 scripts/generate-yrkeslon.py
Output: kalkylatorer/yrkeslon/{slug}.html × N
        sitemap-yrkeslon-fragment.xml (klistra in i sitemap.xml manuellt)
        search-index-fragment.js     (klistra in i search-index.js manuellt)

Lägg till nya yrken i YRKEN-listan nedan och kör om — säkert att köra
flera gånger, skriver över befintliga filer.
"""

import json
import os
from pathlib import Path
from textwrap import dedent

# SCB Lönestrukturstatistik 2024 — approximativa medianer (uppdatera vid behov).
YRKEN = [
    # slug, namn, ackusativ, medianlön kr/mån, intervall, sektor, kommentar
    {"slug": "sjukskoterska", "namn": "Sjuksköterska", "median": 38000, "low": 33000, "high": 46000, "sektor": "Vård & omsorg",
     "fakta": "En sjuksköterska tjänar i snitt 38 000 kr/mån enligt SCB 2024. Specialistsjuksköterskor i operationssal eller IVA tjänar oftast 45 000–55 000 kr. Tillägg för OB-arbete (kväll, natt, helg) kan ge 5 000–10 000 kr extra/mån."},

    {"slug": "larare", "namn": "Lärare (grundskola)", "median": 38500, "low": 33000, "high": 46000, "sektor": "Utbildning",
     "fakta": "En grundskollärare tjänar i snitt 38 500 kr/mån. Förstelärare med särskilt uppdrag har normalt 45 000–50 000 kr. Lärartiteln 'förstelärare' ger ofta 5 000 kr/mån i tillägg enligt karriärtjänstreformen."},

    {"slug": "polis", "namn": "Polis", "median": 41000, "low": 33000, "high": 53000, "sektor": "Rättsväsende",
     "fakta": "En polisman tjänar 33 000 kr/mån som nybörjare och upp till 53 000 kr som erfaren utredare eller gruppchef. OB-tillägg vid kvälls- och helgarbete ger normalt 5 000–10 000 kr/mån extra. Polisförhandlingen 2023 lyfte ingångslönen kraftigt."},

    {"slug": "underskoterska", "namn": "Undersköterska", "median": 30500, "low": 27000, "high": 35500, "sektor": "Vård & omsorg",
     "fakta": "En undersköterska tjänar i snitt 30 500 kr/mån. Specialistundersköterskor (demens, palliativ vård) tjänar 33 000–37 000 kr. OB-tillägg kan ge 4 000–8 000 kr extra/mån vid skift- och helgarbete."},

    {"slug": "it-tekniker", "namn": "IT-tekniker", "median": 41000, "low": 32000, "high": 56000, "sektor": "IT & teknik",
     "fakta": "En IT-tekniker (helpdesk/support) tjänar runt 35 000 kr. Systemadministratörer och nätverkstekniker tjänar normalt 45 000–55 000 kr. DevOps-ingenjörer kan ligga på 55 000–75 000 kr beroende på erfarenhet och ort."},

    {"slug": "snickare", "namn": "Snickare", "median": 33000, "low": 28000, "high": 41000, "sektor": "Bygg & hantverk",
     "fakta": "En snickare i Sverige tjänar i snitt 33 000 kr/mån (timlön ca 200–230 kr). Egenföretagande snickare med F-skatt fakturerar normalt 600–900 kr/tim exklusive moms. Byggavtalet styr lönenivåer för anställda."},

    {"slug": "civilingenjor", "namn": "Civilingenjör", "median": 51000, "low": 40000, "high": 70000, "sektor": "Ingenjör & teknik",
     "fakta": "En civilingenjör tjänar i snitt 51 000 kr/mån. Ingångslönen för en nyexaminerad ligger på 38 000–43 000 kr. Erfarna projektledare och tekniska experter når 65 000–80 000 kr, särskilt inom IT och konsultverksamhet."},

    {"slug": "lakare", "namn": "Läkare (allmänläkare)", "median": 70000, "low": 55000, "high": 95000, "sektor": "Vård & omsorg",
     "fakta": "En allmänläkare (specialist) tjänar i snitt 70 000 kr/mån. Underläkare har 45 000–55 000 kr under ST-tiden. Privatpraktiserande läkare och stafettläkare når 90 000–130 000 kr/mån, ibland mer."},

    {"slug": "ekonom", "namn": "Ekonom", "median": 47000, "low": 35000, "high": 65000, "sektor": "Ekonomi & finans",
     "fakta": "En ekonom (controller, redovisning, analys) tjänar i snitt 47 000 kr/mån. Auktoriserade revisorer ligger på 55 000–75 000 kr. CFO på medelstora bolag tjänar 75 000–110 000 kr beroende på bolagsstorlek."},

    {"slug": "jurist", "namn": "Jurist", "median": 56000, "low": 42000, "high": 85000, "sektor": "Juridik",
     "fakta": "En jurist tjänar i snitt 56 000 kr/mån. Nyexaminerade börjar på 38 000–45 000 kr. Affärsjurister och delägare på advokatbyrå når 80 000–150 000 kr/mån. Domare har relativt fasta lönenivåer på 65 000–90 000 kr."},

    {"slug": "tandlakare", "namn": "Tandläkare", "median": 64000, "low": 50000, "high": 90000, "sektor": "Vård & omsorg",
     "fakta": "En tandläkare i offentlig sektor tjänar i snitt 64 000 kr/mån. Specialister (ortodonti, oral kirurgi) når 80 000–100 000 kr. Privatpraktiserande tandläkare kan ha betydligt högre inkomst beroende på praktikens storlek."},

    {"slug": "forskollarare", "namn": "Förskollärare", "median": 33000, "low": 29000, "high": 38500, "sektor": "Utbildning",
     "fakta": "En förskollärare tjänar i snitt 33 000 kr/mån. Förskollärare med specialpedagogisk kompetens eller förstelärar-uppdrag ligger på 36 000–41 000 kr. Barnskötare (utan högskoleexamen) tjänar normalt 27 000–30 000 kr."},

    {"slug": "elektriker", "namn": "Elektriker", "median": 35500, "low": 30000, "high": 44000, "sektor": "Bygg & hantverk",
     "fakta": "En installationsledektriker tjänar i snitt 35 500 kr/mån. Behörighetsutbildade elektriker (auktoriserade) ligger på 40 000–48 000 kr. Egenföretagande elektriker fakturerar typiskt 650–900 kr/tim exklusive moms."},

    {"slug": "byggnadsarbetare", "namn": "Byggnadsarbetare", "median": 33500, "low": 28000, "high": 42000, "sektor": "Bygg & hantverk",
     "fakta": "En byggnadsarbetare tjänar i snitt 33 500 kr/mån (timlön ca 200–230 kr enligt Byggavtalet 2024). Arbetsledare och förmän tjänar 42 000–55 000 kr. Ackordsarbete kan ge betydligt högre månadsinkomst."},

    {"slug": "frisor", "namn": "Frisör", "median": 27500, "low": 23000, "high": 35000, "sektor": "Service",
     "fakta": "En anställd frisör tjänar i snitt 27 500 kr/mån enligt Handels avtal. Egenanställda frisörer och salongsägare kan ha betydligt högre inkomst (40 000–70 000 kr) men bär även hyra, material och företagskostnader."},

    {"slug": "saljare", "namn": "Säljare", "median": 36000, "low": 28000, "high": 60000, "sektor": "Försäljning",
     "fakta": "En anställd säljare har en grundlön på i snitt 36 000 kr/mån, men provisionsdelen kan dubblera totalen. B2B-säljare i SaaS och tech-bolag kan nå 70 000–120 000 kr inkl. bonus. Telemarketing-säljare ligger i den lägre delen av spannet."},

    {"slug": "sakerhetsvakt", "namn": "Säkerhetsvakt", "median": 28000, "low": 24500, "high": 35000, "sektor": "Säkerhet",
     "fakta": "En väktare/säkerhetsvakt tjänar i snitt 28 000 kr/mån enligt Bevakningsavtalet. OB-tillägg vid kvälls- och nattskift kan ge 4 000–8 000 kr/mån extra. Personskyddsväktare och utbildade ordningsvakter ligger högre."},

    {"slug": "brandman", "namn": "Brandman", "median": 33000, "low": 28000, "high": 42000, "sektor": "Rättsväsende",
     "fakta": "En heltidsanställd brandman tjänar i snitt 33 000 kr/mån. Brandförman och arbetsledare ligger på 38 000–45 000 kr. Räddningstjänstpersonal i beredskap (RIB, deltidsbrandmän) har en grundersättning + utryckningsersättning."},

    {"slug": "socionom", "namn": "Socionom", "median": 36500, "low": 31000, "high": 44000, "sektor": "Vård & omsorg",
     "fakta": "En socionom tjänar i snitt 36 500 kr/mån. Socialsekreterare med utredningsansvar för barn/unga (IFO) ligger normalt på 38 000–43 000 kr. Enhetschefer inom socialtjänsten når 50 000–60 000 kr."},

    {"slug": "personlig-assistent", "namn": "Personlig assistent", "median": 26500, "low": 24000, "high": 31000, "sektor": "Vård & omsorg",
     "fakta": "En personlig assistent tjänar i snitt 26 500 kr/mån enligt Kommunals avtal. OB-tillägg vid kvälls-, natt- och helgarbete kan ge 3 000–7 000 kr/mån extra. Vissa arbetsgivare betalar tillägg för dubbla assistansbehov."},
]


def format_kr(amount):
    """Format number as Swedish currency with non-breaking space."""
    return f"{amount:,}".replace(",", " ") + " kr"


def calc_netto(brutto_year):
    """Rough net income approximation (Skatteverket schablon ~30 % municipal)."""
    if brutto_year < 24000 * 12:
        skatt_pct = 0.20
    elif brutto_year < 49500 * 12:
        skatt_pct = 0.32
    else:
        # Statlig skatt på lönedel över 49 500/mån (skiktgräns 2026 approx 614 000/år).
        skatt_pct = 0.42
    return int(brutto_year * (1 - skatt_pct))


TEMPLATE = '''<!DOCTYPE html>
<html lang="sv">
<head>
  <!-- Google Analytics 4 -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XGTX1PYYFJ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-XGTX1PYYFJ');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script>(function(){{var s=null;try{{s=localStorage.getItem('gk-theme');}}catch(e){{}}var d=s==='dark'||(s===null&&window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)').matches);document.documentElement.setAttribute('data-theme',d?'dark':'light');}})();</script>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/favicon.svg">

  <title>Lön {namn_lower} 2026 — Snittlön {median_str}/mån + nettolön</title>
  <meta name="description" content="Lön för {namn_lower} 2026: snittlön {median_str}/mån enligt SCB ({low_str}–{high_str}). Räkna ut nettolön på 30 sek. Inkl. OB-tillägg, sektor och exempel.">
  <link rel="canonical" href="https://gratiskalkyl.se/kalkylatorer/yrkeslon/{slug}">
  <meta property="og:title" content="Lön {namn_lower} 2026 — Snittlön {median_str}/mån + nettolön">
  <meta property="og:description" content="Snittlön {median_str}/mån för {namn_lower} 2026 enligt SCB. Räkna ut din nettolön direkt — inkl. skatt, OB och pension.">
  <meta property="og:url" content="https://gratiskalkyl.se/kalkylatorer/yrkeslon/{slug}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="https://gratiskalkyl.se/favicon.svg">
  <meta property="og:locale" content="sv_SE">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{"@type":"Question","name":"Vad tjänar en {namn_lower_q} 2026?","acceptedAnswer":{{"@type":"Answer","text":"En {namn_lower_q} tjänar i snitt {median_str}/månad 2026 enligt SCB:s lönestrukturstatistik. Lönespannet är {low_str}–{high_str}/månad beroende på erfarenhet, sektor och region."}}}},
      {{"@type":"Question","name":"Vad blir nettolönen för en {namn_lower_q}?","acceptedAnswer":{{"@type":"Answer","text":"Med en snittlön på {median_str}/mån brutto blir nettolönen ca {netto_str}/mån efter kommunalskatt (cirka 32 %). Räkna ut din exakta nettolön på loneraknare.se baserat på din kommun."}}}},
      {{"@type":"Question","name":"Hur skiljer sig lönen mellan offentlig och privat sektor?","acceptedAnswer":{{"@type":"Answer","text":"Inom {sektor} kan löneskillnaden mellan offentlig och privat sektor variera 5–20 %. Offentlig sektor erbjuder normalt mer förmåner (pension, försäkringar, semester) medan privat sektor oftare har bonus- och resultatbaserad ersättning."}}}},
      {{"@type":"Question","name":"När höjs lönen?","acceptedAnswer":{{"@type":"Answer","text":"Lönerevision sker normalt en gång per år, oftast under våren efter att aktuellt löneavtal förhandlats fram. Centrala avtal sätter ett 'minimi-mervärde' (i procent) som hela sektorn ska över, men individuell lönesättning används i många avtal idag."}}}}
    ]
  }}
  </script>

  <style>
    :root {{ --primary: #16a34a; --primary-light: #dcfce7; --primary-dark: #15803d; --text: #111827; --muted: #6b7280; --bg: #f8fafc; --card: #ffffff; --border: #e5e7eb; --radius: 12px; --sh: 0 1px 3px rgba(0,0,0,.06); }}
    @media (prefers-color-scheme: dark) {{ :root {{ --text: #f3f4f6; --muted: #9ca3af; --bg: #0f172a; --card: #1e293b; --border: #334155; --primary-light: rgba(52,211,153,.15); --primary: #34d399; }} }}
    html[data-theme="dark"] {{ --text: #f3f4f6; --muted: #9ca3af; --bg: #0f172a; --card: #1e293b; --border: #334155; --primary-light: rgba(52,211,153,.15); --primary: #34d399; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; font-size: 17px; }}
    .nav {{ background: var(--card); border-bottom: 1px solid var(--border); padding: 14px 20px; position: sticky; top: 0; z-index: 10; display: flex; justify-content: space-between; align-items: center; }}
    .nav a.logo {{ font-weight: 700; color: var(--primary); text-decoration: none; font-size: 1.1rem; }}
    .nav a.logo span {{ color: var(--text); font-weight: 500; }}
    .nav-links {{ display: flex; gap: 16px; }}
    .nav-links a {{ color: var(--muted); text-decoration: none; font-size: 0.9rem; }}
    .nav-links a:hover {{ color: var(--primary); }}
    .container {{ max-width: 760px; margin: 0 auto; padding: 24px 20px 48px; }}
    .breadcrumb {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 16px; }}
    .breadcrumb a {{ color: var(--primary); text-decoration: none; }}
    .tag {{ display: inline-block; background: var(--primary-light); color: var(--primary-dark); padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }}
    h1 {{ font-size: clamp(1.6rem, 4vw, 2.2rem); font-weight: 800; line-height: 1.2; margin-bottom: 8px; letter-spacing: -0.01em; }}
    .lead {{ font-size: 1.1rem; color: var(--muted); margin-bottom: 24px; }}
    .lead strong {{ color: var(--text); }}
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 24px 0; }}
    .stat {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; }}
    .stat .num {{ font-size: 1.6rem; font-weight: 800; color: var(--primary); line-height: 1.1; }}
    .stat .lbl {{ font-size: 0.78rem; color: var(--muted); margin-top: 4px; }}
    h2 {{ font-size: 1.3rem; font-weight: 700; margin: 32px 0 14px; }}
    h3 {{ font-size: 1.05rem; font-weight: 600; margin: 22px 0 10px; }}
    p {{ margin-bottom: 14px; }}
    .info-box {{ background: var(--primary-light); border-left: 4px solid var(--primary); border-radius: 0 var(--radius) var(--radius) 0; padding: 16px 20px; margin: 18px 0; }}
    .info-box strong {{ color: var(--primary-dark); }}
    ul, ol {{ padding-left: 22px; margin-bottom: 14px; }}
    li {{ margin-bottom: 6px; }}
    .table {{ width: 100%; border-collapse: collapse; margin: 18px 0; background: var(--card); border-radius: var(--radius); overflow: hidden; box-shadow: var(--sh); font-size: 0.95rem; }}
    .table th, .table td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
    .table th {{ background: var(--primary-light); color: var(--primary-dark); font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.03em; }}
    .table tr:last-child td {{ border-bottom: none; }}
    .table .num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
    .cta {{ background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; padding: 24px 28px; border-radius: var(--radius); margin: 28px 0; text-align: center; }}
    .cta h3 {{ color: white; margin-bottom: 6px; }}
    .cta a {{ display: inline-block; background: white; color: var(--primary); padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; margin-top: 8px; }}
    .related {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 18px 0; }}
    .related a {{ display: block; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; text-decoration: none; color: var(--text); transition: border-color .2s; }}
    .related a:hover {{ border-color: var(--primary); }}
    .related .em {{ font-size: 1.4rem; }}
    .related .name {{ font-weight: 600; font-size: 0.92rem; margin-top: 4px; }}
    footer {{ background: var(--card); border-top: 1px solid var(--border); padding: 24px 20px; text-align: center; color: var(--muted); font-size: 0.85rem; margin-top: 32px; }}
    footer a {{ color: var(--primary); text-decoration: none; }}
  </style>
</head>
<body>
  <nav class="nav">
    <a class="logo" href="/">GratisKalkyl<span>.se</span></a>
    <div class="nav-links">
      <a href="/">Kalkylatorer</a>
      <a href="/artiklar/">Guider</a>
    </div>
  </nav>

  <main class="container">
    <nav class="breadcrumb">
      <a href="/">Hem</a> &rsaquo; <a href="/kalkylatorer/loneraknare">Löneräknare</a> &rsaquo; <span>Lön {namn_lower}</span>
    </nav>

    <span class="tag">{sektor}</span>
    <h1>Lön {namn_lower} 2026</h1>
    <p class="lead">En <strong>{namn_lower}</strong> tjänar i snitt <strong>{median_str}/månad</strong> 2026 enligt SCB:s lönestrukturstatistik. Lönespannet är {low_str}–{high_str}/mån beroende på erfarenhet, sektor och region. Här går vi igenom vad du faktiskt tjänar netto, hur lönen utvecklas över karriären och hur du räknar ut din egen.</p>

    <div class="stats">
      <div class="stat"><div class="num">{median_str_short}</div><div class="lbl">Snittlön/mån</div></div>
      <div class="stat"><div class="num">{netto_str_short}</div><div class="lbl">Netto/mån</div></div>
      <div class="stat"><div class="num">{aretsbrutto_short}</div><div class="lbl">Bruttolön/år</div></div>
    </div>

    <div class="cta">
      <h3>Räkna ut din exakta nettolön</h3>
      <p style="color:rgba(255,255,255,0.92);font-size:0.95rem;">Skriv in din kommun, månadslön och eventuella avdrag — se nettolönen på 10 sekunder.</p>
      <a href="/kalkylatorer/loneraknare">Öppna löneräknaren &rarr;</a>
    </div>

    <h2>Lönenivåer för {namn_lower} 2026</h2>
    <p>{fakta}</p>

    <table class="table">
      <thead><tr><th>Lönenivå</th><th class="num">Bruttolön/mån</th><th class="num">Nettolön/mån</th><th class="num">Bruttolön/år</th></tr></thead>
      <tbody>
        <tr><td>Ingångslön</td><td class="num">{low_str}</td><td class="num">{low_netto_str}</td><td class="num">{low_year_str}</td></tr>
        <tr><td>Snittlön</td><td class="num">{median_str}</td><td class="num">{netto_str}</td><td class="num">{median_year_str}</td></tr>
        <tr><td>Topp 10 %</td><td class="num">{high_str}</td><td class="num">{high_netto_str}</td><td class="num">{high_year_str}</td></tr>
      </tbody>
    </table>

    <div class="info-box">
      <strong>Tips:</strong> Nettolönen ovan är beräknad med kommunalskatt ~32 % (Sveriges medel 2026). I kommuner med högre skatt (t.ex. Dorotea, Munkfors) blir nettot ca 600–900 kr lägre per månad. I lågskattekommuner (t.ex. Solna, Vellinge) blir nettot motsvarande högre.
    </div>

    <h2>Hur skiljer sig lönen i olika delar av Sverige?</h2>
    <p>För {namn_lower_q} finns det skillnader mellan storstadsregioner och övriga landet. Stockholm ligger normalt 5–12 % över rikssnittet, Göteborg 3–7 % över, medan glesbygd och mindre orter kan ligga 5–10 % under. Privat sektor betalar oftast mer än offentlig — men kollektivavtalad pension och förmåner gör att den totala "lönen" i offentlig sektor inte är så långt efter.</p>

    <h2>Hur räknar du själv ut din nettolön?</h2>
    <p>Använd <a href="/kalkylatorer/loneraknare">löneräknaren på GratisKalkyl.se</a> — den tar hänsyn till:</p>
    <ul>
      <li>Din kommunalskatt (varierar mellan ca 29 och 35 %)</li>
      <li>Statlig skatt om du tjänar över 49 500 kr/månad (skiktgränsen 2026)</li>
      <li>Jobbskatteavdrag (gör att du betalar mindre skatt på arbetsinkomst)</li>
      <li>Grundavdrag och eventuella avgifter (begravningsavgift, kyrkoavgift)</li>
    </ul>

    <h2>Vad är skillnaden mellan brutto och netto?</h2>
    <p><strong>Bruttolön</strong> är din lön före skatt. <strong>Nettolön</strong> är det som faktiskt landar på ditt konto efter att Skatteverket dragit kommunalskatt, eventuell statlig skatt och eventuella avgifter. För {namn_lower_q} med snittlön innebär det att ungefär <strong>{netto_pct} % av bruttot kommer ut som netto</strong>.</p>

    <h2>Vanliga frågor</h2>
    <h3>Vad tjänar en {namn_lower_q} 2026?</h3>
    <p>En {namn_lower_q} tjänar i snitt {median_str}/månad 2026 enligt SCB:s lönestrukturstatistik. Lönespannet är {low_str}–{high_str}/månad beroende på erfarenhet, sektor och region.</p>

    <h3>Vad blir nettolönen?</h3>
    <p>Med en snittlön på {median_str}/mån brutto blir nettolönen ca {netto_str}/mån efter kommunalskatt (cirka 32 %). Räkna ut din exakta nettolön i <a href="/kalkylatorer/loneraknare">löneräknaren</a> baserat på din kommun.</p>

    <h3>När höjs lönen?</h3>
    <p>Lönerevision sker normalt en gång per år, oftast under våren efter att aktuellt löneavtal förhandlats fram. Centrala avtal sätter ett "minimi-mervärde" (i procent) som hela sektorn ska över, men individuell lönesättning används i många avtal idag.</p>

    <h2>Relaterade kalkylatorer och guider</h2>
    <div class="related">
      <a href="/kalkylatorer/loneraknare"><span class="em">💰</span><div class="name">Löneräknare 2026</div></a>
      <a href="/kalkylatorer/marginalskattekalkylator"><span class="em">📊</span><div class="name">Marginalskatt</div></a>
      <a href="/kalkylatorer/pensionskalkylator"><span class="em">🏖️</span><div class="name">Pensionskalkylator</div></a>
      <a href="/artiklar/rakna-ut-nettolon-2026"><span class="em">📖</span><div class="name">Räkna ut nettolön 2026</div></a>
    </div>
  </main>

  <footer>
    <p>&copy; 2026 GratisKalkyl.se — Lönedata från SCB:s lönestrukturstatistik (Sveriges officiella statistik).<br>
    Beräkningarna är ungefärliga. Använd <a href="/kalkylatorer/loneraknare">löneräknaren</a> för exakt nettolön baserat på din kommun.</p>
  </footer>
</body>
</html>
'''


def main():
    out_dir = Path(__file__).parent.parent / "kalkylatorer" / "yrkeslon"
    out_dir.mkdir(parents=True, exist_ok=True)

    sitemap_fragment = []
    search_fragment = []

    for y in YRKEN:
        median_year = y["median"] * 12
        low_year = y["low"] * 12
        high_year = y["high"] * 12

        netto = calc_netto(median_year) // 12
        low_netto = calc_netto(low_year) // 12
        high_netto = calc_netto(high_year) // 12
        netto_pct = round(netto / y["median"] * 100)

        ctx = {
            "slug": y["slug"],
            "namn": y["namn"],
            "namn_lower": y["namn"].lower(),
            "namn_lower_q": y["namn"].lower(),
            "sektor": y["sektor"],
            "fakta": y["fakta"],
            "median": y["median"],
            "median_str": format_kr(y["median"]),
            "median_str_short": format_kr(y["median"]),
            "median_year_str": format_kr(median_year),
            "low_str": format_kr(y["low"]),
            "high_str": format_kr(y["high"]),
            "low_year_str": format_kr(low_year),
            "high_year_str": format_kr(high_year),
            "netto_str": format_kr(netto),
            "netto_str_short": format_kr(netto),
            "low_netto_str": format_kr(low_netto),
            "high_netto_str": format_kr(high_netto),
            "aretsbrutto_short": format_kr(median_year),
            "netto_pct": netto_pct,
        }

        html = TEMPLATE.format(**ctx)
        out_path = out_dir / f"{y['slug']}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"  Wrote {out_path.relative_to(out_dir.parent.parent)}")

        sitemap_fragment.append(
            f'  <url>\n'
            f'    <loc>https://gratiskalkyl.se/kalkylatorer/yrkeslon/{y["slug"]}</loc>\n'
            f'    <lastmod>2026-05-26</lastmod>\n'
            f'    <changefreq>monthly</changefreq>\n'
            f'    <priority>0.7</priority>\n'
            f'  </url>'
        )

        search_fragment.append(
            '  {\n'
            f'    "type": "yrkeslon",\n'
            f'    "url": "/kalkylatorer/yrkeslon/{y["slug"]}",\n'
            f'    "title": "Lön {y["namn"].lower()} 2026",\n'
            '    "icon": "💼",\n'
            '    "category": "Yrkeslön",\n'
            f'    "desc": "Snittlön {format_kr(y["median"])}/mån + nettolön och lönespann för {y["namn"].lower()}.",\n'
            f'    "kw": "lön {y["namn"].lower()} 2026 vad tjänar en {y["namn"].lower()} snittlön nettolön bruttolön {y["sektor"].lower()}"\n'
            '  }'
        )

    fragments_dir = Path(__file__).parent
    (fragments_dir / "sitemap-yrkeslon-fragment.xml").write_text(
        "\n".join(sitemap_fragment) + "\n", encoding="utf-8")
    (fragments_dir / "search-index-yrkeslon-fragment.js").write_text(
        ",\n".join(search_fragment) + "\n", encoding="utf-8")

    print(f"\n✅ Genererade {len(YRKEN)} yrkeslön-sidor i kalkylatorer/yrkeslon/")
    print(f"📄 Sitemap-fragment: scripts/sitemap-yrkeslon-fragment.xml")
    print(f"🔎 Search-index-fragment: scripts/search-index-yrkeslon-fragment.js")


if __name__ == "__main__":
    main()
