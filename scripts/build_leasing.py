#!/usr/bin/env python3
"""Bygger kalkylatorer/leasingkalkylator.html i den nya verktygsmallen.

Modell (samma i Python-referensen nedan och i sidans JS):
  Finansierat belopp F = pris − handpenning, restvärde RV = pris × restvärde %.
  Leasingavgift/mån = (F − RV) / mån  +  (F + RV) / 2 × ränta / 12.
  Köp med lån: annuitetslån på F över lånetiden, bilen säljs efter avtalstiden för RV och
  restskulden löses. Nettokostnad köp = handpenning + betalningar + restskuld + det som ingår i
  leasingen (service m.m.) − RV.
Enda statistiken på sidan är snittkörsträckan från Trafikanalys (Körsträckor 2025).

    python3 scripts/build_leasing.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/leasingkalkylator"
UPDATED = "1 oktober 2026"

# Standardvärden i formuläret (exempel, inga marknadssiffror)
D = {"PRIS": 350000, "HP": 0, "MAN": 36, "RV": 50, "RL": 6.5, "RK": 7.5, "LT": 60}
# Trafikanalys, Körsträckor 2025 (publicerad 17 april 2026)
TRAFA = {"PRIVAT": 1155, "ALLA": 1243, "EL": 1700}

SRC = {
    "trafa": "https://www.trafa.se/globalassets/statistik/vagtrafik/korstrackor/2025/korstrackor-2025---2026-04-17.pdf",
}


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def leasing(pris, hp, man, rv_pct, rl):
    F, RV = pris - hp, pris * rv_pct / 100
    dep = (F - RV) / man
    ranta = (F + RV) / 2 * rl / 100 / 12
    return {"F": F, "RV": RV, "dep": dep, "ranta": ranta, "man": dep + ranta, "tot": hp + (dep + ranta) * man}


def lan(L, rk, lt):
    i = rk / 100 / 12
    return L / lt if i == 0 else L * i / (1 - (1 + i) ** -lt)


def restskuld(L, rk, lt, n):
    if n >= lt:
        return 0.0
    i = rk / 100 / 12
    m = lan(L, rk, lt)
    if i == 0:
        return L - m * n
    return L * (1 + i) ** n - m * ((1 + i) ** n - 1) / i


def kop(pris, hp, man, rv_pct, rk, lt, ovrigt=0):
    L = pris - hp
    m = lan(L, rk, lt)
    k = min(man, lt)
    B = restskuld(L, rk, lt, man)
    brutto = hp + m * k + B + ovrigt * man
    return {"man": m, "betalt": hp + m * k, "rest": B, "brutto": brutto, "netto": brutto - pris * rv_pct / 100}


EX = leasing(D["PRIS"], D["HP"], D["MAN"], D["RV"], D["RL"])
EXK = kop(D["PRIS"], D["HP"], D["MAN"], D["RV"], D["RK"], D["LT"])

FAQ = [
    ("Hur räknar man ut leasingkostnaden per månad?",
     "Leasingavgiften består av två delar. Den första är bilens värdeminskning: det finansierade beloppet (priset minus handpenning) "
     "minus restvärdet, delat med antalet månader. Den andra är ränta på det genomsnittliga kapitalet under avtalet, alltså "
     "(finansierat belopp + restvärde) / 2 × årsräntan / 12. "
     f"En bil för {fmt(D['PRIS'])} kr med {D['RV']} % restvärde efter {D['MAN']} månader och {str(D['RL']).replace('.', ',')} % ränta kostar då ungefär "
     f"{fmt(round(EX['man'], -1))} kr i månaden: {fmt(round(EX['dep'], -1))} kr värdeminskning och {fmt(round(EX['ranta'], -1))} kr ränta. "
     "Leasingbolagets pris kan skilja, till exempel om service ingår eller om restvärdet är ett annat."),
    ("Hur beräknar man restvärdet vid leasing?",
     "Restvärdet i kronor är bilens pris gånger restvärdet i procent – 50 % av 350 000 kr är 175 000 kr. Procentsatsen sätts av "
     "leasingbolaget utifrån vad de tror att bilen är värd när avtalet är slut, och den står ofta i offerten. Vill du bedöma om "
     "den är rimlig: jämför med vad likadana bilar som är lika gamla säljs för begagnade."),
    ("Vad är restvärde vid leasing?",
     "Restvärdet är det värde leasingbolaget räknar med att bilen har när avtalet är slut, i procent av priset. Det är den del av "
     "bilens pris som du inte betalar av under avtalet. Ju högre restvärde, desto lägre månadsavgift. Restvärdet skiljer sig mellan "
     "modeller, så fråga efter det och jämför med vad liknande begagnade bilar säljs för."),
    ("Är det billigare att leasa eller köpa bil?",
     "Jämför vad bilen kostar netto, inte månadsbeloppet. Vid köp äger du bilen och får tillbaka det den är värd när du säljer. "
     "Kalkylatorn räknar köpets nettokostnad som handpenning + lånebetalningar + restskuld − bilens värde vid försäljningen. "
     "Med samma ränta blir köp ofta billigare om bilen går att sälja för restvärdet, men du bär själv risken att den är värd mindre. "
     "Kalkylatorn visar också vad bilen minst måste säljas för för att köpet ska löna sig."),
    ("Vad händer om jag kör fler mil än leasingavtalet?",
     "Då betalar du en avgift för varje mil över gränsen, oftast när bilen lämnas tillbaka. Priset per mil står i avtalet. "
     "Milgränsen går ofta inte att ändra under avtalstiden, så välj en gräns som räcker från början. Enligt Trafikanalys körde "
     f"privatägda personbilar i snitt {fmt(TRAFA['PRIVAT'])} mil under 2025."),
    ("Hur många mil kör en vanlig bil per år?",
     f"Enligt Trafikanalys körde personbilar i snitt {fmt(TRAFA['ALLA'])} mil under 2025, och privatägda bilar {fmt(TRAFA['PRIVAT'])} mil. "
     f"Elbilar och laddhybrider körde längre, ungefär {fmt(TRAFA['EL'])} mil. Det är snitt – räkna på hur mycket just du kör."),
    ("Kan man avsluta ett privatleasingavtal i förtid?",
     "Oftast inte utan kostnad. Ett leasingavtal löper normalt hela avtalstiden, och går leasingbolaget med på att avsluta det "
     "i förtid får du ofta betala en lösensumma. Läs vad avtalet säger om förtida avslut, skador vid återlämning och vad som räknas som normalt slitage."),
    ("Vad är handpenning vid leasing?",
     "Handpenning, ibland kallad förhöjd första hyra, är ett belopp du betalar när avtalet börjar. Den sänker månadsavgiften men "
     "du får inte tillbaka den – du äger ingen del av bilen. Jämför därför alltid totalkostnaden, handpenningen inräknad."),
]

CHEV = S.ICON_CHEV


def seg_btns(vals, pressed, fmt_fn, small=None):
    out = []
    for v in vals:
        sm = f"<small>{small[v]}</small>" if small and v in small else ""
        out.append(f'<button type="button" data-v="{v}" aria-pressed="{"true" if v == pressed else "false"}">{fmt_fn(v)}{sm}</button>')
    return "".join(out)


def page():
    title = "Leasingkalkylator 2026 – beräkna leasingkostnad per månad | GratisKalkyl"
    desc = ("Beräkna leasingkostnaden per månad för bilen: värdeminskning, ränta och restvärde. Jämför med att köpa "
            "med lån och se om leasingerbjudandet du fått är rimligt.")
    crumbs = [("Hem", "/"), ("Bil & energi", "/bil-och-energi"), ("Leasingkalkylator", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Leasingkalkylator 2026 – månadskostnad för billeasing",
         "url": S.SITE + PATH, "applicationCategory": "FinanceApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Bil & energi", "item": S.SITE + "/bil-och-energi"},
            {"@type": "ListItem", "position": 3, "name": "Leasingkalkylator", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    kr0 = lambda v: fmt(v)  # noqa: E731

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Leasingkalkylator 2026</div>
<h1>Vad kostar bilen att leasa?</h1>
<p class="gk-lead">Räkna ut månadsavgiften, jämför med att köpa bilen med lån och se om erbjudandet du fått är rimligt.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Snittkörsträcka: <a href="{SRC['trafa']}" target="_blank" rel="noopener">Trafikanalys</a></p>
</div>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="lform" novalidate onsubmit="return false">
<div class="gk-field">
<label for="pris">Bilens pris</label>
<div class="gk-input"><input id="pris" inputmode="numeric" autocomplete="off" value="{kr0(D['PRIS'])}"><span class="unit">kr</span></div>
<div class="gk-seg" style="--n:3" id="prisq" role="group" aria-label="Vanliga priser">
{seg_btns([250000, 350000, 500000], D['PRIS'], kr0)}
</div>
</div>

<fieldset class="gk-fieldset">
<legend class="gk-legend">Avtalstid</legend>
<div class="gk-seg" style="--n:4" id="manq" role="group" aria-label="Avtalstid i månader">
{seg_btns([24, 36, 48, 60], D['MAN'], lambda v: f"{v}", {24: "mån", 36: "mån", 48: "mån", 60: "mån"})}
</div>
</fieldset>

<div class="gk-field">
<label for="rv">Restvärde efter avtalet</label>
<div class="gk-input"><input id="rv" inputmode="decimal" autocomplete="off" value="{D['RV']}"><span class="unit">% av priset</span></div>
<div class="gk-seg" style="--n:3" id="rvq" role="group" aria-label="Restvärde">
{seg_btns([40, 50, 60], D['RV'], lambda v: f"{v} %")}
</div>
<span class="gk-hint">Det leasingbolaget räknar med att bilen är värd när du lämnar tillbaka den. Fråga efter det i offerten.</span>
</div>

<div class="gk-field">
<label for="hp">Handpenning</label>
<div class="gk-input"><input id="hp" inputmode="numeric" autocomplete="off" value="{kr0(D['HP'])}"><span class="unit">kr</span></div>
<span class="gk-hint">Kallas ibland förhöjd första hyra. Du får inte tillbaka den.</span>
</div>

<details class="gk-more">
<summary>Ändra räntor och lån</summary>
<div class="gk-stack" style="gap:14px">
<div class="gk-field">
<label for="rl">Ränta i leasingen</label>
<div class="gk-input"><input id="rl" inputmode="decimal" autocomplete="off" value="{str(D['RL']).replace('.', ',')}"><span class="unit">% per år</span></div>
</div>
<div class="gk-field">
<label for="rk">Ränta på billånet</label>
<div class="gk-input"><input id="rk" inputmode="decimal" autocomplete="off" value="{str(D['RK']).replace('.', ',')}"><span class="unit">% per år</span></div>
</div>
<div class="gk-field">
<label for="lt">Lånets löptid</label>
<div class="gk-input"><input id="lt" inputmode="numeric" autocomplete="off" value="{D['LT']}"><span class="unit">mån</span></div>
<span class="gk-hint">Säljer du bilen innan lånet är betalt löses resten med pengarna från försäljningen.</span>
</div>
<div class="gk-field">
<label for="ovr">Ingår service eller däck i leasingen?</label>
<div class="gk-input"><input id="ovr" inputmode="numeric" autocomplete="off" placeholder="0"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Fyll i vad det skulle kosta dig per månad om du köper bilen. Läggs på köpet i jämförelsen.</span>
</div>
<span class="gk-hint">Räntorna är exempel. Byt till räntorna i dina offerter.</span>
</div>
</details>
</form>

<section class="gk-card gk-stack gk-o3" style="gap:14px" aria-labelledby="offH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="offH" style="font-size:22px">Har du fått ett erbjudande?</h2>
<p class="gk-hint">Fyll i månadsavgiften i offerten så ser du om den är i nivå med uträkningen.</p>
</div>
<div class="gk-field">
<label for="off">Månadsavgift i erbjudandet</label>
<div class="gk-input"><input id="off" inputmode="numeric" autocomplete="off" placeholder="t.ex. 5 990"><span class="unit">kr/mån</span></div>
<span class="gk-hint">Samma pris, avtalstid och handpenning som ovan.</span>
</div>
<div id="offRes" aria-live="polite"></div>
</section>

<section class="gk-card gk-stack gk-o4" style="gap:14px" aria-labelledby="milH">
<div style="display:flex;flex-direction:column;gap:4px">
<h2 id="milH" style="font-size:22px">Räcker milen?</h2>
<p class="gk-hint">Kör du mer än avtalet betalar du för varje mil över gränsen.</p>
</div>
<div class="gk-field">
<label for="kor">Så långt kör du per år</label>
<div class="gk-input"><input id="kor" inputmode="numeric" autocomplete="off" value="{fmt(TRAFA['PRIVAT'])}"><span class="unit">mil/år</span></div>
<div class="gk-seg" style="--n:3" id="korq" role="group" aria-label="Körsträcka">
{seg_btns([TRAFA['PRIVAT'], 1500, TRAFA['EL']], TRAFA['PRIVAT'], kr0, {TRAFA['PRIVAT']: "snittet", TRAFA['EL']: "snitt elbil"})}
</div>
<span class="gk-hint">Snitt för privatägda bilar och för elbilar 2025 enligt Trafikanalys.</span>
</div>
<div class="gk-field">
<label for="avt">Mil per år i avtalet</label>
<div class="gk-input"><input id="avt" inputmode="numeric" autocomplete="off" value="1 500"><span class="unit">mil/år</span></div>
</div>
<div class="gk-field">
<label for="omp">Pris per mil över gränsen</label>
<div class="gk-input"><input id="omp" inputmode="decimal" autocomplete="off" placeholder="står i avtalet"><span class="unit">kr/mil</span></div>
</div>
<div id="milRes" aria-live="polite"></div>
</section>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">Din leasingavgift</div>
<div class="gk-big"><strong id="resBig">–</strong><span>kr/mån</span></div>
<p class="gk-hint" id="resSub"></p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-o5" style="gap:12px" aria-labelledby="cmpH">
<h2 id="cmpH" style="font-size:22px">Leasa eller köpa – vad kostar bilen?</h2>
<figure style="margin:0">
<figcaption class="gk-hint" style="margin-bottom:8px" id="chartCap"></figcaption>
<div id="chart"></div>
</figure>
<details class="gk-more">
<summary>Visa år för år</summary>
<div class="gk-table-wrap"><table class="gk-table gk-table-tight" id="planTable"></table></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="/kalkylatorer/bilkostnadsraknare"><span>Vad kostar bilen totalt?<small>Lägg till försäkring, skatt, drivmedel och service</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/formansbilkalkylator"><span>Förmånsbil i stället?<small>Räkna ut förmånsvärdet och vad det kostar dig netto</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/privatleasing-eller-kopa-bil-2026"><span>Guide: privatleasing eller köpa bil<small>Det du ska ha koll på innan du skriver på</small></span>{CHEV}</a>
<!--GK-PARTNER:bilforsakring:START--><!--GK-PARTNER:bilforsakring:END-->
</section>
</div>
</div>

<div class="gk-prose">
<h2>Så räknas leasingavgiften</h2>
<p>När du leasar betalar du för den del av bilens värde som försvinner under avtalet, plus ränta. Leasingbolaget räknar med att bilen är värd ett visst <strong>restvärde</strong> när du lämnar tillbaka den, och resten av priset fördelas på avtalets månader.</p>
<ul>
<li><strong>Värdeminskning per månad</strong> = (pris − handpenning − restvärde) / antal månader</li>
<li><strong>Ränta per månad</strong> = (pris − handpenning + restvärde) / 2 × årsräntan / 12</li>
</ul>
<p>Räntan räknas på det genomsnittliga beloppet under avtalet, eftersom du i början lånar hela priset och i slutet bara restvärdet. Med {fmt(D['PRIS'])} kr, {D['RV']} % restvärde, {D['MAN']} månader och {str(D['RL']).replace('.', ',')} % ränta blir avgiften ungefär <strong>{fmt(round(EX['man'], -1))} kr i månaden</strong>.</p>
<p>Ett leasingbolags pris kan skilja från uträkningen. Ofta ingår service och ibland vinterdäck eller försäkring, och bolaget kan ha ett annat restvärde än det du räknar med.</p>

<h2>Leasa eller köpa?</h2>
<p>Jämför vad bilen kostar dig netto, inte vad du betalar per månad. Med leasing äger du inget när avtalet är slut. Köper du bilen med lån får du tillbaka det den är värd när du säljer den.</p>
<ul>
<li><strong>Leasing</strong> = handpenning + alla månadsavgifter.</li>
<li><strong>Köp med lån</strong> = handpenning + lånebetalningar + restskulden på lånet − det du får för bilen. Kalkylatorn räknar med att du säljer bilen för restvärdet när avtalstiden är slut.</li>
</ul>
<p>Vid samma ränta blir köp ofta något billigare, eftersom leasingräntan betalas på ett belopp som inkluderar restvärdet under hela avtalet. Men vid köp bär du själv risken att bilen är värd mindre än du trott, och du betalar oftast mer per månad. Kalkylatorn visar därför också vad bilen minst måste säljas för för att köpet ska löna sig.</p>
<p>Leasing passar dig som vill byta bil med jämna mellanrum och ha en fast kostnad. Planerar du att behålla bilen länge blir köp oftast billigare, eftersom en bil tappar mest i värde de första åren.</p>

<h2>Restvärdet avgör månadsavgiften</h2>
<p>Ju högre restvärde, desto mindre av bilens pris betalar du under avtalet. Därför kan en dyrare bil som håller värdet bra kosta lika mycket att leasa som en billigare bil som tappar snabbt. Fråga alltid efter restvärdet i offerten och jämför med vad liknande begagnade bilar säljs för.</p>

<h2>Mil och övermil</h2>
<p>Leasingavtal har en milgräns per år. Kör du längre betalar du en avgift per mil över gränsen, och gränsen går ofta inte att ändra under avtalstiden. Enligt Trafikanalys körde personbilar i snitt <strong>{fmt(TRAFA['ALLA'])} mil</strong> under 2025 och privatägda bilar <strong>{fmt(TRAFA['PRIVAT'])} mil</strong>. Elbilar och laddhybrider körde längre, ungefär {fmt(TRAFA['EL'])} mil.</p>

<h2>Innan du skriver på</h2>
<ul>
<li>Jämför <strong>totalkostnaden</strong> för hela avtalet, med handpenning och avgifter – inte bara månadsavgiften.</li>
<li>Kolla vad som <strong>ingår</strong>: service, vinterdäck, försäkring. Det som inte ingår betalar du själv.</li>
<li>Välj en <strong>milgräns</strong> som räcker. Räkna på hur långt du faktiskt kör.</li>
<li>Läs vad avtalet säger om <strong>skador och slitage</strong> när bilen lämnas tillbaka.</li>
<li>Kontrollera vad det kostar att <strong>avsluta avtalet i förtid</strong>, till exempel om du flyttar eller behöver en annan bil.</li>
</ul>

<h2>Vanliga frågor om leasing</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['trafa']}" target="_blank" rel="noopener">Trafikanalys – Körsträckor 2025</a> (snittkörsträcka {fmt(TRAFA['ALLA'])} mil, privatägda {fmt(TRAFA['PRIVAT'])} mil, elbil och laddhybrid ca {fmt(TRAFA['EL'])} mil)</li>
<li>Leasingavgiften räknas med rak värdeminskning till restvärdet och ränta på genomsnittligt kapital. Billånet räknas som ett annuitetslån. Räntorna är exempel som du kan ändra.</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/bilkostnadsraknare"><span>Bilkostnadsräknare<small>Vad kostar bilen per månad och per mil?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/drivmedelskalkylator"><span>Drivmedelskalkylator<small>Bensin, diesel eller el</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/lanekalkylator"><span>Lånekalkylator<small>Månadskostnad och ränta för ett billån</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-leasing" type="application/json">{{"lt":{D['LT']},"rl":{D['RL']},"rk":{D['RK']},"privat":{TRAFA['PRIVAT']}}}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Leasingkalkylator 2026 – vad kostar bilen att leasa?", jsonld=ld)
            + S.header() + body + S.footer("Leasingberäkningen är en uppskattning – leasingbolagets offert gäller."))


JS = r"""
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-leasing').textContent);
  var $ = function (id) { return document.getElementById(id); };
  var kr = function (v) { return GK.fmt(Math.round(v / 10) * 10, 0) + ' kr'; };
  var st = { man: 36 };

  function seg(id, cb) {
    var el = $(id);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      el.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cb(b.getAttribute('data-v')); calc();
    });
  }
  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', +x.getAttribute('data-v') === v ? 'true' : 'false'); }); }
  seg('prisq', function (v) { $('pris').value = GK.fmt(+v, 0); });
  seg('manq', function (v) { st.man = +v; });
  seg('rvq', function (v) { $('rv').value = v; });
  seg('korq', function (v) { $('kor').value = GK.fmt(+v, 0); });
  ['pris', 'rv', 'hp', 'rl', 'rk', 'lt', 'ovr', 'off', 'kor', 'avt', 'omp'].forEach(function (id) { $(id).addEventListener('input', calc); });
  $('pris').addEventListener('input', function () { press('prisq', GK.parse($('pris').value)); });
  $('rv').addEventListener('input', function () { press('rvq', GK.parse($('rv').value)); });
  $('kor').addEventListener('input', function () { press('korq', GK.parse($('kor').value)); });
  ['pris', 'hp', 'ovr', 'off', 'kor', 'avt'].forEach(function (id) { GK.groupInput($(id)); });

  function val(id) { var v = GK.parse($(id).value); return isFinite(v) && v >= 0 ? v : null; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '" style="margin-top:12px">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }
  function pct(v, d) { return GK.fmt(v, d == null ? 1 : d) + ' %'; }
  function rp(v) { return GK.fmt(v, 2).replace(/,?0+$/, ''); }

  /* Modell – samma som scripts/build_leasing.py */
  function leasing(P, H, n, rvp, rl) {
    var F = P - H, RV = P * rvp / 100, dep = (F - RV) / n, ranta = (F + RV) / 2 * rl / 100 / 12;
    return { F: F, RV: RV, dep: dep, ranta: ranta, man: dep + ranta, tot: H + (dep + ranta) * n };
  }
  function annuitet(L, rk, lt) { var i = rk / 100 / 12; return i === 0 ? L / lt : L * i / (1 - Math.pow(1 + i, -lt)); }
  function restskuld(L, rk, lt, n) {
    if (n >= lt) return 0;
    var i = rk / 100 / 12, m = annuitet(L, rk, lt);
    return i === 0 ? L - m * n : L * Math.pow(1 + i, n) - m * (Math.pow(1 + i, n) - 1) / i;
  }
  function kop(P, H, n, rvp, rk, lt, ovr) {
    var L = P - H, m = annuitet(L, rk, lt), k = Math.min(n, lt), B = restskuld(L, rk, lt, n);
    var brutto = H + m * k + B + ovr * n;
    return { L: L, man: m, betalt: H + m * k, rest: B, brutto: brutto, netto: brutto - P * rvp / 100 };
  }
  function clear(msg) {
    $('resBig').textContent = '–'; $('resSub').textContent = msg;
    ['tiles', 'verdict', 'how', 'chart', 'chartCap', 'planTable', 'offRes', 'milRes'].forEach(function (id) { $(id).innerHTML = ''; });
  }

  function calc() {
    var P = val('pris'), H = val('hp') || 0, rvp = val('rv'), n = st.man;
    var rl = val('rl'), rk = val('rk'), lt = val('lt'), ovr = val('ovr') || 0;
    if (rl == null || rl > 30) rl = C.rl;
    if (rk == null || rk > 30) rk = C.rk;
    if (!lt || lt < 12 || lt > 120) lt = C.lt;
    lt = Math.round(lt);
    if (!P || P < 10000) return clear('Fyll i bilens pris.');
    if (rvp == null || rvp >= 100) return clear('Fyll i restvärdet i procent, till exempel 50.');
    if (H >= P) return clear('Handpenningen kan inte vara lika stor som priset.');
    var l = leasing(P, H, n, rvp, rl);
    if (l.F <= l.RV) return clear('Handpenning och restvärde blir tillsammans mer än bilens pris. Sänk handpenningen eller restvärdet.');
    var k = kop(P, H, n, rvp, rk, lt, ovr);

    $('resBig').textContent = GK.fmt(Math.round(l.man / 10) * 10, 0);
    $('resSub').textContent = 'Totalt ' + kr(l.tot) + ' på ' + n + ' månader' + (H > 0 ? ', handpenningen inräknad' : '') + '. Du lämnar tillbaka bilen och äger inget efteråt.';
    $('tiles').innerHTML = tile('Värdeminskning', kr(l.dep) + '/mån', 'Pris ner till restvärdet ' + kr(l.RV)) +
      tile('Ränta', kr(l.ranta) + '/mån', rp(rl) + ' % på snittkapitalet') +
      tile('Köpa med lån', kr(k.man) + '/mån', 'Lån ' + kr(k.L) + ' på ' + lt + ' mån, ' + rp(rk) + ' %') +
      tile('Bilens värde efter ' + n + ' mån', kr(l.RV), GK.fmt(rvp, 1).replace(/,0$/, '') + ' % av priset');

    var diff = l.tot - k.netto;                     /* > 0: köp billigare */
    var grans = k.brutto - l.tot;                   /* sälj minst för detta för att köp ska löna sig */
    var v = '';
    if (Math.abs(diff) < Math.max(1000, l.tot * 0.01)) {
      v = verdict('info', 'Leasing och köp kostar ungefär lika mycket', 'Över ' + n + ' månader kostar båda ca ' + kr(l.tot) + ' netto – om bilen kan säljas för ' + kr(l.RV) + '.');
    } else if (diff > 0) {
      v = verdict('good', 'Köpa med lån blir ca ' + kr(diff) + ' billigare', 'Över ' + n + ' månader, om du kan sälja bilen för ' + kr(l.RV) + '. Köpet lönar sig så länge bilen går att sälja för mer än ' + kr(Math.max(0, grans)) + ' (' + pct(Math.max(0, grans) / P * 100, 0) + ' av priset). Säljer du för mindre är leasing billigare.');
    } else {
      v = verdict('good', 'Leasing blir ca ' + kr(-diff) + ' billigare', 'Över ' + n + ' månader jämfört med att köpa med lån och sälja för ' + kr(l.RV) + '. Köp lönar sig först om bilen går att sälja för mer än ' + kr(grans) + ' (' + pct(grans / P * 100, 0) + ' av priset).');
    }
    if (k.man > l.man * 1.05) v += verdict('info', 'Köp kostar mer per månad', 'Lånet kostar ' + kr(k.man) + ' i månaden mot ' + kr(l.man) + ' för leasing – ' + kr(k.man - l.man) + ' mer varje månad, pengar som du annars kunde spara.');
    $('verdict').innerHTML = v;

    $('how').innerHTML =
      '<p><strong>Leasing:</strong> värdeminskning (' + kr(l.F) + ' − ' + kr(l.RV) + ') / ' + n + ' = ' + kr(l.dep) + ' per månad. Ränta (' + kr(l.F) + ' + ' + kr(l.RV) + ') / 2 × ' + rp(rl) + ' % / 12 = ' + kr(l.ranta) + ' per månad. Finansierat belopp = pris − handpenning.</p>' +
      '<p><strong>Köp:</strong> annuitetslån på ' + kr(k.L) + ' över ' + lt + ' månader med ' + rp(rk) + ' % ränta = ' + kr(k.man) + ' per månad. Efter ' + n + ' månader har du betalat ' + kr(k.betalt) + (k.rest > 0 ? ' och har ' + kr(k.rest) + ' kvar på lånet, som du löser när du säljer' : '') + '. Du säljer bilen för ' + kr(l.RV) + ' (restvärdet). Nettokostnad: ' + kr(k.netto) + (ovr > 0 ? ', inklusive ' + kr(ovr * n) + ' för det som ingår i leasingen' : '') + '.</p>' +
      '<p>Vi räknar inte med uppläggnings- och aviavgifter, försäkring, skatt eller drivmedel – de tillkommer i båda fallen. Leasingbolagets pris kan skilja från uträkningen, till exempel om service ingår.</p>';

    offer(l, P, H, n, rvp, rl);
    mil(l, n);
    chart(l, k, n);

    var rows = [], m;
    for (m = 12; m < n; m += 12) rows.push(m);
    rows.push(n);
    $('planTable').innerHTML = '<thead><tr><th scope="col">Efter</th><th scope="col">Leasing betalt</th><th scope="col">Köp: betalt</th><th scope="col">Kvar på lånet</th></tr></thead><tbody>' +
      rows.map(function (mm) {
        return '<tr><td>' + mm + ' mån</td><td>' + GK.fmt(Math.round(H + l.man * mm), 0) + '</td><td>' + GK.fmt(Math.round(H + k.man * Math.min(mm, lt)), 0) + '</td><td>' + GK.fmt(Math.round(restskuld(k.L, rk, lt, mm)), 0) + '</td></tr>';
      }).join('') + '</tbody><caption class="gk-hint" style="caption-side:bottom;text-align:left;padding-top:8px">Kronor, handpenning inräknad. Vid köp får du tillbaka det bilen säljs för.</caption>';
  }

  function offer(l, P, H, n, rvp, rl) {
    var O = val('off');
    if (!O || O < 100) { $('offRes').innerHTML = ''; return; }
    var d = O - l.man, imp = (O - l.dep) * 24 / (l.F + l.RV) * 100;
    var h = '<div class="gk-tiles">' + tile('Totalt för erbjudandet', kr(H + O * n), n + ' mån' + (H > 0 ? ', handpenning inräknad' : '')) +
      tile('Motsvarar en ränta på', imp > 0 ? pct(imp) : 'under 0 %', 'Om restvärdet är ' + GK.fmt(rvp, 1).replace(/,0$/, '') + ' %') + '</div>';
    if (Math.abs(d) <= l.man * 0.03) {
      h += verdict('good', 'I nivå med uträkningen', 'Erbjudandet ligger nära ' + kr(l.man) + ' i månaden, som vi räknar fram med ' + rp(rl) + ' % ränta och ' + GK.fmt(rvp, 1).replace(/,0$/, '') + ' % restvärde.');
    } else if (d > 0) {
      h += verdict('warn', 'Erbjudandet är ' + kr(d) + ' dyrare per månad', 'Det blir ' + kr(d * n) + ' mer på ' + n + ' månader än uträkningen. Det kan bero på att service, däck eller försäkring ingår – då kan det vara rimligt – eller på högre ränta eller lägre restvärde. Fråga vilket restvärde och vilken ränta erbjudandet bygger på.');
    } else {
      h += verdict('good', 'Erbjudandet är ' + kr(-d) + ' billigare per månad', 'Det blir ' + kr(-d * n) + ' mindre på ' + n + ' månader än uträkningen. Leasingbolaget räknar troligen med ett högre restvärde eller har en kampanjränta. Kolla milgränsen och vad som händer vid återlämning.');
    }
    $('offRes').innerHTML = h;
  }

  function mil(l, n) {
    var K = val('kor'), A = val('avt'), p = val('omp');
    if (!K || K < 50 || !A || A < 50) { $('milRes').innerHTML = ''; return; }
    var ar = n / 12, over = Math.max(0, K - A) * ar, kost = p ? over * p : 0;
    var h = '<div class="gk-tiles">' + tile('Kostnad per mil', GK.fmt((l.tot + kost) / (K * ar), 1) + ' kr', 'Leasing' + (kost ? ' och övermil' : '') + ' delat på ' + GK.fmt(Math.round(K * ar), 0) + ' mil') +
      tile('Snittet', GK.fmt(C.privat, 0) + ' mil/år', 'Privatägda bilar 2025, Trafikanalys') + '</div>';
    if (K > A) {
      h += verdict('warn', 'Du kör ca ' + GK.fmt(Math.round(over), 0) + ' mil för mycket', 'Det är ' + GK.fmt(Math.round(K - A), 0) + ' mil per år över avtalets gräns' +
        (p ? ', och kostar ca ' + kr(kost) + ' på ' + n + ' månader (' + kr(kost / n) + '/mån). Jämför med vad en högre milgräns kostar i avtalet.' : '. Fyll i priset per mil så räknar vi ut vad det kostar – eller välj en högre milgräns i avtalet.'));
    } else {
      h += verdict('good', 'Milgränsen räcker', 'Du har ' + GK.fmt(Math.round(A - K), 0) + ' mil per år i marginal. Har du mycket marginal kan en lägre milgräns ge en lägre avgift.');
    }
    $('milRes').innerHTML = h;
  }

  function chart(l, k, n) {
    var W = Math.max(300, Math.min(760, $('chart').clientWidth || 600)), Lw = W < 480 ? 92 : 120, R = 16, bh = 30, gap = 34, T = 6;
    var hi = Math.max(l.tot, k.brutto), sx = function (v) { return (W - Lw - R) * Math.max(0, v) / hi; };
    var H = T + 2 * bh + gap + 4;
    var y1 = T, y2 = T + bh + gap;
    var lab = function (y, t, s) { return '<text x="0" y="' + (y + 13) + '" font-size="13" font-weight="700" fill="var(--gk-ink)">' + t + '</text><text x="0" y="' + (y + 28) + '" font-size="11" fill="var(--gk-muted)">' + s + '</text>'; };
    var vt = function (x, y, t, anchorEnd) { return '<text x="' + x + '" y="' + (y + bh / 2 + 5) + '" font-size="13" font-weight="700" text-anchor="' + (anchorEnd ? 'end' : 'start') + '" fill="' + (anchorEnd ? 'var(--gk-surface)' : 'var(--gk-ink)') + '">' + t + '</text>'; };
    var s = lab(y1, 'Leasing', 'betalt') + lab(y2, 'Köpa', 'netto');
    var wl = sx(l.tot), wn = sx(Math.max(0, k.netto)), wb = sx(k.brutto);
    s += '<rect x="' + Lw + '" y="' + y1 + '" width="' + wl + '" height="' + bh + '" rx="6" fill="var(--gk-accent)"/>';
    s += wl > 110 ? vt(Lw + wl - 8, y1, kr(l.tot), true) : vt(Lw + wl + 6, y1, kr(l.tot));
    s += '<rect x="' + Lw + '" y="' + y2 + '" width="' + wb + '" height="' + bh + '" rx="6" fill="var(--gk-surface-2)" stroke="var(--gk-border-strong)" stroke-dasharray="4 3"/>';
    s += '<rect x="' + Lw + '" y="' + y2 + '" width="' + wn + '" height="' + bh + '" rx="6" fill="var(--gk-ink-2)"/>';
    s += wn > 110 ? vt(Lw + wn - 8, y2, kr(k.netto), true) : vt(Lw + wn + 6, y2, kr(k.netto));

    $('chartCap').textContent = 'Vad bilen kostar dig på ' + n + ' månader. Köp: det du betalar minus det du får när du säljer bilen.';
    $('chart').innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Leasing kostar ' + kr(l.tot) + ', att köpa med lån kostar netto ' + kr(k.netto) + ' på ' + n + ' månader" style="display:block;font-family:inherit">' + s + '</svg>' +
      '<p class="gk-hint" style="margin:8px 0 0;display:flex;align-items:flex-start;gap:8px"><svg width="22" height="12" aria-hidden="true" style="flex:none;margin-top:3px"><rect x="1" y="1" width="20" height="10" rx="3" fill="var(--gk-surface-2)" stroke="var(--gk-border-strong)" stroke-dasharray="4 3"/></svg><span>Vid köp betalar du ' + kr(k.brutto) + ' men får tillbaka ' + kr(l.RV) + ' när du säljer bilen.</span></p>';
  }

  calc();
});
"""


def main():
    out = os.path.join(ROOT, "kalkylatorer", "leasingkalkylator.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    print(f"Exempel: leasing {EX['man']:.0f} kr/mån (dep {EX['dep']:.0f} + ränta {EX['ranta']:.0f}), totalt {EX['tot']:.0f}; "
          f"lån {EXK['man']:.0f} kr/mån, netto köp {EXK['netto']:.0f}")


if __name__ == "__main__":
    main()
