"""GratisKalkyl v2 – gemensamt sidskal (head, sidhuvud, meny, sidfot).

Används av byggskripten för sidor i den nya designen så att alla sidor
får exakt samma meny och sidfot. Ändra här och bygg om sidorna.
"""
import html
import json

SITE = "https://gratiskalkyl.se"

# Ämnen i menyn. (namn, undertext, hubb-url eller None, [(titel, url), ...])
TOPICS = [
    ("Lön & jobb", "Lön, semester, egen firma", "/lon-och-jobb", [
        ("Löneräknare – nettolön", "/kalkylatorer/loneraknare"),
        ("Löneförhandling – vad ska du begära?", "/kalkylatorer/loneforhandling"),
        ("Lön per yrke (105 yrken)", "/kalkylatorer/yrkeslon/"),
        ("Semesterlön", "/kalkylatorer/semesterlonekalkylator"),
        ("Semesterersättning", "/kalkylatorer/semesterersattning"),
        ("Frilans och eget företag", "/kalkylatorer/frilanskalkylator"),
        ("Arbetsgivaravgift", "/kalkylatorer/arbetsgivaravgift-kalkylator"),
        ("Traktamente", "/kalkylatorer/traktamentekalkylator"),
    ]),
    ("Skatt & deklaration", "Återbäring, avdrag, marginalskatt", "/skatt-och-deklaration", [
        ("Skatteåterbäring", "/kalkylatorer/skatteaterbarings-kalkylator"),
        ("Reseavdrag", "/kalkylatorer/reseavdragskalkylator"),
        ("Marginalskatt", "/kalkylatorer/marginalskattekalkylator"),
        ("ROT- och RUT-avdrag", "/kalkylatorer/rot-rut"),
        ("ISK-skatt", "/kalkylatorer/isk-skatteberaknare"),
        ("Kapitalvinstskatt", "/kalkylatorer/kapitalvinstskatt"),
        ("Moms", "/kalkylatorer/momsraknare"),
    ]),
    ("Boende & lån", "Bolån, amortering, budget", "/boende-och-lan", [
        ("Bolån – månadskostnad", "/kalkylatorer/bolanekalkylator"),
        ("Amorteringskrav", "/kalkylatorer/amorteringskalkylator"),
        ("Lån och privatlån", "/kalkylatorer/lanekalkylator"),
        ("Hyra eller köpa?", "/kalkylatorer/hyra-vs-kopa-kalkylator"),
        ("Uthyrning av bostad", "/kalkylatorer/uthyrningskalkylator"),
        ("Hushållsbudget", "/kalkylatorer/hushallsbudget"),
    ]),
    ("Bil & energi", "El, bil, leasing, solceller", "/bil-och-energi", [
        ("Elkostnad och elavtal", "/kalkylatorer/elkostnadskalkylator"),
        ("Bilkostnad", "/kalkylatorer/bilkostnadsraknare"),
        ("Leasing", "/kalkylatorer/leasingkalkylator"),
        ("Förmånsbil", "/kalkylatorer/formansbilkalkylator"),
        ("Drivmedel", "/kalkylatorer/drivmedelskalkylator"),
        ("Milersättning", "/kalkylatorer/milersattningskalkylator"),
        ("Solceller", "/kalkylatorer/solcellskalkylator"),
    ]),
    ("Sparande & pension", "Ränta på ränta, pension, CSN", "/sparande-och-pension", [
        ("Sparande och ränta på ränta", "/kalkylatorer/sparkalkylator"),
        ("Pension", "/kalkylatorer/pensionskalkylator"),
        ("Tjänstepension", "/kalkylatorer/tjanstepensionskalkylator"),
        ("Löneväxling", "/kalkylatorer/lonevaxling-kalkylator"),
        ("Direktavkastning", "/kalkylatorer/direktavkastningskalkylator"),
        ("Inflation", "/kalkylatorer/inflationskalkylator"),
        ("CSN – studielån", "/kalkylatorer/csn-kalkylator"),
    ]),
    ("Familj & trygghet", "Föräldrapenning, sjuk, a-kassa", "/familj-och-trygghet", [
        ("Föräldrapenning", "/kalkylatorer/foraldrapenning"),
        ("Barnbidrag", "/kalkylatorer/barnbidragskalkylator"),
        ("Sjukpenning", "/kalkylatorer/sjukpenningkalkylator"),
        ("Karensavdrag", "/kalkylatorer/karensavdragskalkylator"),
        ("A-kassa", "/kalkylatorer/akassa-kalkylator"),
        ("Underhållsstöd", "/kalkylatorer/underhallsstod-kalkylator"),
    ]),
    ("Övriga räknare", "Procent", None, [
        ("Procent", "/kalkylatorer/procentraknare"),
    ]),
]

N_CALC = 41
N_GUIDES = 27
GA_ID = "G-XGTX1PYYFJ"
ADSENSE = "ca-pub-8657228803389245"

ICON_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
ICON_MENU = '<svg class="gk-ico-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
ICON_CLOSE = '<svg class="gk-ico-close" style="display:none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>'
ICON_CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
ICON_ALERT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>'

e = html.escape


def head(title, description, path, og_title=None, jsonld=(), extra_head=""):
    url = SITE + path
    ld = "\n".join(
        '<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + "</script>" for x in jsonld
    )
    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>(function(){{var s=null;try{{s=localStorage.getItem("gk-theme");}}catch(e){{}}var d=s==="dark";document.documentElement.setAttribute("data-theme",d?"dark":"light");}})();</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE}" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{e(og_title or title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta property="og:image" content="{SITE}/favicon.svg">
<meta property="og:locale" content="sv_SE">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="/search-dropdown.css">
<link rel="stylesheet" href="/assets/gk.css?v=20261001">
<script defer src="/search-index.js"></script>
<script defer src="/search-dropdown.js"></script>
<script defer src="/assets/gk.js?v=20261001"></script>
{ld}
{extra_head}
</head>
"""


def shell_top(skin=False):
    """Sidhuvud + meny utan <body>. skin=True används på äldre sidor (div i stället för header/nav,
    så att sidornas egna elementregler i CSS inte påverkar skalet)."""
    groups = []
    for i, (name, sub, hub, links) in enumerate(TOPICS):
        items = "".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in links)
        if hub:
            items = f'<li class="gk-mg-hubli"><a href="{hub}"><strong>Allt om {e(name)} →</strong></a></li>' + items
            title = f'<a class="gk-mg-title" href="{hub}">{e(name)}<small>{e(sub)}</small></a>'
        else:
            title = f'<span class="gk-mg-title">{e(name)}<small>{e(sub)}</small></span>'
        groups.append(
            f'<div class="gk-mg"><button class="gk-mg-btn" type="button" aria-expanded="false">'
            f'<span>{e(name)}<small>{e(sub)}</small></span>{ICON_CHEV}</button>{title}<ul>{items}</ul></div>'
        )
    tag, extra = ("div", ' role="banner"') if skin else ("header", "")
    g2 = " gk2" if skin else ""
    return f"""<a class="gk-skip{g2}" href="#innehall">Hoppa till innehållet</a>
<{tag} class="gk-hdr{g2}"{extra}>
<div class="gk-wrap gk-hdr-in">
<a class="gk-logo" href="/">Gratis<span>Kalkyl</span></a>
<label class="gk-search gk-hdr-search"><span class="gk-sr">Sök</span>{ICON_SEARCH}<input type="search" data-search-dropdown="auto" placeholder="Sök kalkylator eller yrke" autocomplete="off" spellcheck="false"></label>
<div class="gk-hdr-actions">
<button class="gk-icon-btn gk-search-open-btn" type="button" data-gk-menu="search" aria-controls="gk-menu" aria-expanded="false" aria-label="Sök">{ICON_SEARCH}</button>
<button class="gk-icon-btn gk-menu-btn" type="button" data-gk-menu="menu" aria-controls="gk-menu" aria-expanded="false">{ICON_MENU}{ICON_CLOSE}<span class="gk-menu-btn-label">Alla verktyg</span><span class="gk-sr"> – meny</span></button>
</div>
</div>
</{tag}>
<div class="gk-menu{g2}" id="gk-menu" hidden>
<div class="gk-menu-in">
<label class="gk-search"><span class="gk-sr gk-menu-search-label">Sök</span>{ICON_SEARCH}<input type="search" data-search-dropdown="auto" placeholder="Sök kalkylator eller yrke" autocomplete="off" spellcheck="false"></label>
<span class="gk-menu-label">Ämnen</span>
<div class="gk-menu-groups">{''.join(groups)}</div>
<span class="gk-menu-label">Allt på ett ställe</span>
<ul class="gk-menu-links">
<li><a href="/#kalkylatorer">Alla kalkylatorer <span>{N_CALC}</span></a></li>
<li><a href="/kalkylatorer/yrkeslon/">Lön per yrke <span>105</span></a></li>
<li><a href="/artiklar/">Alla guider <span>{N_GUIDES}</span></a></li>
</ul>
<button class="gk-theme-btn" id="gk-theme-btn" type="button">Byt till mörkt läge</button>
</div>
</div>
"""


def header():
    return '<body class="gk2">\n' + shell_top(False)


def breadcrumbs(items):
    """items: [(namn, url eller None)] – sista utan url."""
    lis = ""
    for i, (n, u) in enumerate(items):
        if i == len(items) - 1:
            lis += f'<li aria-current="page">{e(n)}</li>'
        elif u:
            lis += f'<li><a href="{u}">{e(n)}</a></li>'
        else:
            lis += f'<li>{e(n)}</li>'
    return f'<nav class="gk-crumbs" aria-label="Brödsmulor"><ol>{lis}</ol></nav>'


def breadcrumb_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + (u or "")}
            for i, (n, u) in enumerate(items)
            if u is not None
        ],
    }


def footer_html(note="", skin=False):
    tag, extra = ("div", ' role="contentinfo"') if skin else ("footer", "")
    ntag, nextra = ("div", ' role="navigation"') if skin else ("nav", "")
    g2 = " gk2" if skin else ""
    return f"""<{tag} class="gk-ftr{g2}"{extra}>
<div class="gk-wrap gk-ftr-in">
<div style="display:flex;flex-direction:column;gap:10px">
<a class="gk-logo" href="/">Gratis<span>Kalkyl</span></a>
<p>Oberoende kalkylatorer med öppen källredovisning. Vi finansieras av annonser. Eventuella samarbetslänkar märks alltid med Annons och påverkar aldrig uträkningarna.</p>
<p>Beräkningarna är uppskattningar och kan innehålla fel. Använd dem som vägledning.{(' ' + note) if note else ''}</p>
</div>
<{ntag} class="gk-ftr-nav" aria-label="Sidfot"{nextra}>
<a href="/#kalkylatorer">Alla kalkylatorer</a>
<a href="/artiklar/">Guider</a>
<a href="/om-oss">Om oss</a>
<a href="/integritetspolicy">Integritet</a>
</{ntag}>
</div>
</{tag}>
"""


def footer(note=""):
    return footer_html(note) + "</body>\n</html>\n"
