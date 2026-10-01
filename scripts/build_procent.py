#!/usr/bin/env python3
"""Bygger kalkylatorer/procentraknare.html i den nya verktygsmallen.

Sidan har två delar:
  1. Ett snabbfält där man skriver som man söker: "15 % av 350", "vad är 30% av 1752000", "25 av 500",
     "500*1,25", "500 + 25 %", "500 - 20 %", "200 till 250", "52,5 är 15 % av", "2 % till 3 %".
  2. Fyra lägen (gk-seg): X % av ett tal, hur många procent, ökning/minskning, lägg till/dra av procent.

Formler (samma i Python-referensen nedan och i sidans JS):
  X % av tal          = p × tal / 100
  Hur många procent   = del / hela × 100                    (hela = 0 → går inte)
  Förändring i %      = (nytt − gammalt) / |gammalt| × 100   (gammalt = 0 → går inte)
  Lägg till / dra av  = tal × (100 ± p) / 100
  Hela talet          = del × 100 / p                        (p = 0 → går inte)
Avrundning: högst två decimaler (sex om svaret annars blir 0), heltal från 10^12. Talformat sv-SE.
Inga fakta om moms, skatter eller avgifter på sidan – bara matematik. Källa för formlerna och för
procent/procentenheter: UHR, Tolkning av sifferuppgifter (2021).

    python3 scripts/build_procent.py
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = "/kalkylatorer/procentraknare"
UPDATED = "1 oktober 2026"

# Förval och exempel (inga fakta – bara exempeltal)
K = {
    "START": "15 % av 350",
    "EXEMPEL": ["15 % av 350", "vad är 30 % av 1 752 000", "25 av 500", "500 * 1,25", "500 + 25 %",
                "500 − 20 %", "200 till 250", "52,5 är 15 % av"],
    "LAGE": {"av": ["15", "350"], "andel": ["25", "500"], "for": ["200", "250"], "just": ["500", "25"]},
    "TABELL_P": [1, 5, 10, 15, 20, 25, 30, 50],
    "TABELL_TAL": [50, 100, 350, 500, 1000],
}

SRC = {
    "uhr": "https://www.uhr.se/globalassets/_uhr.se/internationellt/jobba-vid-eu/tolkning-av-sifferuppgifter-2021.pdf",
}

NB = " "   # hårt mellanslag (tusental och före %)
MI = "−"   # minustecken

# ── Talformat ────────────────────────────────────────────────────────────────


def grp(ip):
    out = ""
    while len(ip) > 3:
        out = NB + ip[-3:] + out
        ip = ip[:-3]
    return ip + out


def fnum(x, dec=2):
    """Samma som F() i sidans JS."""
    if x is None or not math.isfinite(x) or abs(x) >= 1e21:
        return "–"
    if abs(x) >= 1e12:
        dec = 0
    f = 10 ** dec
    r = math.floor(x * f + 0.5) / f
    if r == 0 and x != 0 and dec < 6:
        return fnum(x, 6)
    s = f"{abs(r):.{dec}f}"
    ip, fp = (s.split(".") + [""])[:2]
    fp = fp.rstrip("0")
    return (MI if r < 0 else "") + grp(ip) + ("," + fp if fp else "")


def T(x):
    return fnum(x, 6)


def P(x):
    return fnum(x, 6) + NB + "%"


def sgn(s):
    """'+' framför positiva tal (för förändringar)."""
    return s if s.startswith(MI) or s in ("0", "–") else "+" + s


# ── Räknefunktioner ──────────────────────────────────────────────────────────


def av(p, tal):
    return p * tal / 100


def andel(d, hela_):
    return None if hela_ == 0 else d / hela_ * 100


def forandring(fran, till):
    return None if fran == 0 else (till - fran) / abs(fran) * 100


def justera(tal, p, upp):
    return tal * (100 + p) / 100 if upp else tal * (100 - p) / 100


def hela(d, p):
    return None if p == 0 else d * 100 / p


# ── Tolkning av snabbfältet ──────────────────────────────────────────────────

NUM = r"[0-9]{1,3}(?: [0-9]{3}(?![0-9]))+(?:[.,][0-9]+)?|[0-9]+(?:[.,][0-9]+)*"
RE_NUM = re.compile("^(?:" + NUM + ")")
RE_FALT = re.compile("^-?(?:" + NUM + ")$")
RE_WORD = re.compile("^[a-zåäöéü]+")
HELP = "Skriv till exempel 15 % av 350, 25 av 500, 500 + 25 % eller 200 till 250."

S_AV = {"av", "utav", "of"}
S_TILL = {"till", ">"}
S_AR = {"är", "blir", "utgör", "motsvarar"}
S_SUB = {"rabatt", "dra", "drar", "avdrag", "minus", "minska", "sänk", "sänka", "sänkt", "rea"}
S_ADD = {"lägg", "lägga", "plus", "påslag", "öka", "höj", "höja", "höjd", "addera"}
S_MUL = {"*", "x", "gånger", "ggr"}
S_DIV = {"/", "delat", "delad"}
S_PLUS = {"+", "plus"}
S_MINUS = {"-", "minus"}
S_CHG = {"ökning", "minskning", "förändring", "ökat", "minskat"}


def norm(s):
    s = str(s or "").lower()
    s = re.sub("[    \t\r\n]", " ", s)
    s = re.sub("[−–—]", "-", s)
    s = s.replace("×", "*").replace("·", "*").replace("÷", "/").replace("→", ">").replace("->", ">").replace("=>", ">")
    s = s.replace("procent", "%")
    s = re.sub(" +", " ", s).strip()
    return s


def tonum(raw):
    t = raw.replace(" ", "")
    nd, nc = t.count("."), t.count(",")
    if nd and nc:
        t = t.replace(".", "").replace(",", ".", 1) if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif nc:
        t = t.replace(",", "") if nc > 1 else t.replace(",", ".")
    elif nd > 1:
        t = t.replace(".", "")
    return float(re.match(r"[0-9]+(?:\.[0-9]+)?", t).group(0))


def isd(c):
    return "0" <= c <= "9"


def tokens(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == " ":
            i += 1
            continue
        j, neg = i, False
        if c == "-" and i + 1 < n and isd(s[i + 1]) and not (out and out[-1]["t"] == "n"):
            j, neg = i + 1, True
        if isd(s[j]):
            raw = RE_NUM.match(s[j:]).group(0)
            v = tonum(raw)
            out.append({"t": "n", "v": -v if neg else v, "p": False})
            i = j + len(raw)
            continue
        if c == "%":
            if out and out[-1]["t"] == "n" and not out[-1]["p"]:
                out[-1]["p"] = True
            else:
                out.append({"t": "w", "w": "%"})
            i += 1
            continue
        if c in "+-*/>":
            out.append({"t": "w", "w": c})
            i += 1
            continue
        m = RE_WORD.match(s[i:])
        if m:
            out.append({"t": "w", "w": m.group(0)})
            i += len(m.group(0))
            continue
        i += 1
    return out


def falt(s):
    """Tolkar ett vanligt inmatningsfält (läget-verktyget). None om det inte är ett tal."""
    t = norm(s).replace("%", "").strip()
    if not RE_FALT.match(t):
        return None
    v = tonum(t.lstrip("-"))
    return -v if t.startswith("-") else v


def mk(typ, a, b=None, pp=False):
    r = {"typ": typ, "a": a, "b": b, "pp": pp, "svar": None, "fel": ""}
    if typ == "av":
        r["svar"] = av(a, b)
    elif typ == "andel":
        r["svar"] = andel(a, b)
        if r["svar"] is None:
            r["fel"] = "Det hela kan inte vara 0 – då går det inte att räkna ut procenten."
    elif typ == "for":
        r["svar"] = forandring(a, b)
        if r["svar"] is None:
            r["fel"] = "Från 0 går det inte att räkna förändringen i procent. Skillnaden är " + fnum(b - a) + "."
    elif typ in ("upp", "ned"):
        r["svar"] = justera(a, b, typ == "upp")
    elif typ == "hela":
        r["svar"] = hela(a, b)
        if r["svar"] is None:
            r["fel"] = "Procenten kan inte vara 0."
    elif typ == "mul":
        r["svar"] = a * b
    elif typ == "div":
        if b == 0:
            r["fel"] = "Det går inte att dela med 0."
        else:
            r["svar"] = a / b
    elif typ == "sum":
        r["svar"] = a + b
    elif typ == "diff":
        r["svar"] = a - b
    elif typ == "dec":
        r["svar"] = a / 100
    if r["svar"] is not None and not (abs(r["svar"]) < 1e15):
        r["svar"] = None
        r["fel"] = "Talet blir för stort för att visa."
    return r


def tolka(text):
    s = norm(text)
    if not s:
        return {"typ": "tom", "svar": None, "fel": HELP}
    tk = tokens(s)
    idx = [i for i, t in enumerate(tk) if t["t"] == "n"]

    def words(a, b):
        return [t["w"] for t in tk[a:b] if t["t"] == "w"]

    if len(idx) == 1:
        t0 = tk[idx[0]]
        if t0["p"]:
            return mk("dec", t0["v"])
        return {"typ": "fel", "svar": None,
                "fel": "Vad vill du räkna ut med " + T(t0["v"]) + "? Skriv till exempel " + T(t0["v"]) + " % av 350."}
    if len(idx) != 2:
        return {"typ": "fel", "svar": None, "fel": HELP}
    n1, n2 = tk[idx[0]], tk[idx[1]]
    a, b = n1["v"], n2["v"]
    pre, mid, post = words(0, idx[0]), words(idx[0] + 1, idx[1]), words(idx[1] + 1, len(tk))
    allw = set(pre + mid + post)
    mid = set(mid)
    pre = set(pre)
    if n1["p"] and not n2["p"]:
        if mid & S_AV or mid & S_MUL:
            return mk("av", a, b)
        if allw & S_SUB:
            return mk("ned", b, a)
        if allw & S_ADD:
            return mk("upp", b, a)
        return mk("av", a, b)
    if not n1["p"] and n2["p"]:
        if mid & S_PLUS:
            return mk("upp", a, b)
        if mid & S_MINUS:
            return mk("ned", a, b)
        if mid & S_MUL:
            return mk("av", b, a)
        if mid & S_AR:
            return mk("hela", a, b)
        if allw & S_SUB:
            return mk("ned", a, b)
        if allw & S_ADD or "med" in mid:
            return mk("upp", a, b)
        return mk("av", b, a)
    if not n1["p"] and not n2["p"]:
        if mid & S_AV:
            return mk("andel", a, b)
        if pre & S_AV and mid & S_AR:
            return mk("andel", b, a)
        if mid & S_TILL:
            return mk("for", a, b)
        if mid & S_MUL:
            return mk("mul", a, b)
        if mid & S_DIV:
            return mk("andel", a, b) if "%" in allw else mk("div", a, b)
        if mid & S_PLUS:
            return mk("sum", a, b)
        if mid & S_MINUS:
            return mk("diff", a, b)
        if allw & S_CHG:
            return mk("for", a, b)
        return {"typ": "fel", "svar": None, "fel": HELP}
    # båda är procent
    if mid & S_TILL or allw & S_CHG:
        return mk("for", a, b, True)
    if mid & S_AV:
        return mk("av", a, b, True)
    return {"typ": "fel", "svar": None, "fel": HELP}


def big(r):
    if r.get("fel") or r.get("svar") is None:
        return "–"
    if r["typ"] == "dec":
        return fnum(r["svar"], 6)
    s = fnum(r["svar"])
    if r["typ"] == "for":
        s = sgn(s)
    if r["typ"] in ("andel", "for") or (r["typ"] == "av" and r["pp"]):
        s += NB + "%"
    return s


def label(r):
    t, a, b = r["typ"], r.get("a"), r.get("b")
    X = P if r.get("pp") else T
    if t == "av":
        return P(a) + " av " + X(b) + " är"
    if t == "andel":
        return "Så många procent är " + T(a) + " av " + T(b) + ":"
    if t == "for":
        return "Förändring från " + X(a) + " till " + X(b) + ":"
    if t == "upp":
        return T(a) + " + " + P(b) + " är"
    if t == "ned":
        return T(a) + " " + MI + " " + P(b) + " är"
    if t == "hela":
        return T(a) + " är " + P(b) + " av"
    if t == "mul":
        return T(a) + " × " + T(b) + " ="
    if t == "div":
        return T(a) + " / " + T(b) + " ="
    if t == "sum":
        return T(a) + " + " + T(b) + " ="
    if t == "diff":
        return T(a) + " " + MI + " " + T(b) + " ="
    if t == "dec":
        return P(a) + " som decimaltal är"
    if t == "tom":
        return "Skriv en uträkning"
    return "Det gick inte att tolka"


def how(r):
    if r.get("fel") or r.get("svar") is None:
        return r.get("fel") or HELP
    t, a, b, v, B = r["typ"], r["a"], r["b"], r["svar"], big(r)
    if t == "av":
        return T(b) + " × " + T(a) + " / 100 = " + B + "."
    if t == "andel":
        return T(a) + " / " + T(b) + " × 100 = " + B + "."
    if t == "for":
        s = "(" + T(b) + " " + MI + " " + T(a) + ") / " + T(abs(a)) + " × 100 = " + B
        s += " – en ökning" if v > 0 else (" – en minskning" if v < 0 else "")
        if r["pp"]:
            d = fnum(abs(b - a))
            s += ". Skillnaden är " + d + " procentenhet" + ("" if d == "1" else "er")
        return s + "."
    if t == "upp":
        return T(a) + " × " + fnum((100 + b) / 100, 6) + " = " + B + ". Påslaget är " + fnum(v - a) + "."
    if t == "ned":
        return T(a) + " × " + fnum((100 - b) / 100, 6) + " = " + B + ". Avdraget är " + fnum(a - v) + "."
    if t == "hela":
        return T(a) + " / " + T(b) + " × 100 = " + B + "."
    if t == "mul":
        if 0 < b < 1:
            return ("Samma sak som " + P(b * 100) + " av " + T(a) + ", eller " + T(a) + " " + MI + " "
                    + fnum((1 - b) * 100) + NB + "%.")
        if 1 < b < 10:
            return ("Samma sak som " + T(a) + " + " + fnum((b - 1) * 100) + NB + "%: " + T(a) + " + "
                    + fnum(a * (b - 1)) + " = " + B + ".")
        return T(a) + " × " + T(b) + " = " + B + "."
    if t == "div":
        if 1 < b < 10:
            return "Samma sak som att ta bort ett påslag på " + fnum((b - 1) * 100) + NB + "% från " + T(a) + "."
        return T(a) + " / " + T(b) + " = " + B + "."
    if t == "sum":
        return "Vill du lägga till procent? Skriv " + T(a) + " + " + T(b) + " %."
    if t == "diff":
        return "Vill du dra av procent? Skriv " + T(a) + " " + MI + " " + T(b) + " %."
    if t == "dec":
        return T(a) + " / 100 = " + B + ". " + P(a) + " av ett tal är talet × " + B + "."
    return HELP


def quick(text):
    r = tolka(text)
    return {"q": text, "typ": r["typ"], "svar": r.get("svar"), "big": big(r), "label": label(r), "how": how(r)}


# ── Innehåll ─────────────────────────────────────────────────────────────────

Q0 = quick(K["START"])
M0 = mk("av", 15, 350)
EX = {
    "av": fnum(av(15, 350)),                       # 52,5
    "av30": fnum(av(30, 1752000)),                 # 525 600
    "andel": fnum(andel(25, 500)),                 # 5
    "andel2": fnum(andel(120, 480)),               # 25
    "hela": fnum(hela(52.5, 15)),                  # 350
    "for": fnum(forandring(200, 250)),             # 25
    "back": fnum(abs(forandring(250, 200))),       # 20
    "for25": fnum(justera(250, 25, False)),        # 187,5
    "lon": fnum(forandring(30000, 31500)),         # 5
    "upp": fnum(justera(500, 25, True)),           # 625
    "ned": fnum(justera(500, 20, False)),          # 400
    "rab": fnum(500 - justera(500, 20, False)),    # 100
    "tio": fnum(av(10, 350)),                      # 35
    "fem": fnum(av(5, 350)),                       # 17,5
    "ranta": fnum(forandring(2, 3)),               # 50
    "hons": fnum(forandring(4, 6)),                # 50
}

FAQ = [
    ("Hur räknar man ut procent av en summa?",
     f"Multiplicera summan med procentsatsen och dela med 100. 30 % av 1 752 000 är 1 752 000 × 30 / 100 = {EX['av30']}. "
     "Du kan också multiplicera med procenten i decimalform: 1 752 000 × 0,3 ger samma svar."),
    ("Hur många procent är 25 av 500?",
     f"{EX['andel']} %. Dela delen med det hela och multiplicera med 100: 25 / 500 × 100 = {EX['andel']}. "
     f"Samma sätt fungerar för alla tal – 120 av 480 är till exempel {EX['andel2']} %."),
    ("Hur räknar man ut ökning i procent?",
     "Ta skillnaden mellan det nya och det gamla värdet, dela med det gamla värdet och multiplicera med 100. "
     f"Går en lön från 30 000 till 31 500 kr är ökningen 1 500 / 30 000 × 100 = {EX['lon']} %. "
     "Ett negativt svar betyder att värdet har minskat."),
    ("Hur drar man av procent från ett pris?",
     "Multiplicera priset med 1 minus procenten i decimalform. 20 % rabatt på 500 kr blir "
     f"500 × 0,8 = {EX['ned']} kr, och rabatten är {EX['rab']} kr."),
    ("Vad är 500 × 1,25?",
     f"{EX['upp']}. Att multiplicera med 1,25 är samma sak som att lägga till 25 %: 500 + 125 = {EX['upp']}. "
     "På samma sätt är × 1,1 en ökning med 10 % och × 0,9 en minskning med 10 %."),
    ("Hur räknar man procent i huvudet?",
     f"Börja med 10 %, som du får genom att flytta decimalkommat ett steg åt vänster: 10 % av 350 är {EX['tio']}. "
     f"5 % är hälften av det, {EX['fem']}, och 15 % är summan, {EX['av']}. "
     "1 % får du genom att dela med 100, 25 % genom att dela med 4 och 50 % genom att halvera."),
    ("Hur räknar man ut hela beloppet om man vet procenten?",
     f"Dela delen med procenten och multiplicera med 100. Om 52,5 är 15 % av ett belopp är beloppet "
     f"52,5 / 15 × 100 = {EX['hela']}. Skriv 52,5 är 15 % av i rutan överst så räknar sidan ut det."),
    ("Vad är skillnaden mellan procent och procentenheter?",
     "Procentenheter anger hur många steg två procentsatser skiljer sig åt, medan procent anger förändringen i "
     f"förhållande till startvärdet. Ökar en andel från 4 % till 6 % har den ökat med 2 procentenheter, men med {EX['hons']} procent."),
]

CHEV = S.ICON_CHEV

CSS = """<style>
.pq{display:grid;gap:12px;margin-bottom:14px;grid-template-areas:"in" "res" "ex"}
.pq-in{grid-area:in}.pq-res{grid-area:res}.pq-ex{grid-area:ex;align-items:center}
.pq-in{display:flex;flex-direction:column;gap:10px;min-width:0}
.pq .gk-input{height:58px}
.pq .gk-input input{font-size:20px}
.pq-ex{display:flex;flex-wrap:wrap;gap:6px}
.pq-ex .gk-chip{border:0;font:inherit;font-size:14px;cursor:pointer;min-height:36px}
.pq-res{display:flex;flex-direction:column;gap:6px;padding:14px 16px;border-radius:12px;background:var(--gk-soft);min-width:0}
.pq-res .gk-result-label{color:var(--gk-good-ink)}
.pq-how{font-size:15px;line-height:1.5;color:var(--gk-ink-2);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.gk-big strong,.gk-tile strong,.gk-tile span{overflow-wrap:anywhere;min-width:0}
.gk-big strong.is-long{font-size:30px}
.gk-big strong.is-xlong{font-size:24px}
.pr-tab td,.pr-tab th{padding:9px 5px}
.pr-tab tbody th{text-align:left;font-weight:700}
.gk-prose .gk-table-wrap{margin:12px 0}
@media (min-width:900px){
.pq{grid-template-columns:minmax(0,7fr) minmax(0,5fr);grid-template-areas:"in res" "ex res";grid-template-rows:auto 1fr;column-gap:24px;row-gap:14px;margin-bottom:24px}
.pq-ex{align-content:flex-start}
.pq-res{justify-content:center;padding:18px 22px}
.gk-big strong.is-long{font-size:40px}
.gk-big strong.is-xlong{font-size:30px}
}
</style>"""


def table_html():
    head = "".join(f'<th scope="col">{S.e(fnum(t))}</th>' for t in K["TABELL_TAL"])
    rows = []
    for p in K["TABELL_P"]:
        cells = "".join(f"<td>{fnum(av(p, t))}</td>" for t in K["TABELL_TAL"])
        rows.append(f'<tr><th scope="row">{p}{NB}%</th>{cells}</tr>')
    return (f'<div class="gk-table-wrap"><table class="gk-table pr-tab">'
            f'<caption>Så mycket är X{NB}% av 50, 100, 350, 500 och 1{NB}000. Exempel: 15{NB}% av 350 = {EX["av"]}.</caption>'
            f'<thead><tr><th scope="col">Procent av</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def page():
    title = "Procenträknare – räkna ut procent direkt | GratisKalkyl"
    desc = (f"Skriv 15 % av 350 och få svaret direkt: {EX['av']}. Räkna procent av en summa, hur många procent, "
            "ökning i procent och lägg till eller dra av procent.")
    crumbs = [("Hem", "/"), ("Procenträknare", None)]
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Procenträknare",
         "url": S.SITE + PATH, "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}, "inLanguage": "sv", "description": desc,
         "dateModified": "2026-10-01"},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "GratisKalkyl.se", "item": S.SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Procenträknare", "item": S.SITE + PATH}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    faq_html = "".join(f"<details><summary>{S.e(q)}</summary><p>{S.e(a)}</p></details>" for q, a in FAQ)
    chips = "".join(f'<button type="button" class="gk-chip" data-q="{S.e(x)}">{S.e(x)}</button>' for x in K["EXEMPEL"])

    body = f"""
<main id="innehall" class="gk-wrap">
<div class="gk-tool-head">
{S.breadcrumbs(crumbs)}
<div class="gk-eyebrow">Procentkalkylator</div>
<h1>Procenträknare – räkna ut procent</h1>
<p class="gk-lead">Skriv uträkningen som du skulle söka på den – till exempel 15 % av 350 – så får du svaret direkt.</p>
<p class="gk-meta">Uppdaterad {UPDATED} · Fritext eller fyra räknesätt · Formler: <a href="{SRC['uhr']}" target="_blank" rel="noopener">UHR – tolkning av sifferuppgifter</a></p>
</div>

<section class="gk-card pq" aria-label="Snabbräkning">
<form class="pq-in" id="qform" novalidate onsubmit="return false">
<label for="q" class="gk-legend">Skriv din uträkning</label>
<div class="gk-input"><input id="q" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="done" value="{S.e(K['START'])}" aria-describedby="qHow"></div>
</form>
<div class="pq-res" aria-live="polite">
<div class="gk-result-label" id="qLabel">{S.e(Q0['label'])}</div>
<div class="gk-big"><strong id="qBig">{Q0['big']}</strong></div>
<p class="pq-how" id="qHow">{S.e(Q0['how'])}</p>
</div>
<div class="pq-ex" role="group" aria-labelledby="exL"><span class="gk-hint" id="exL">Prova:</span>{chips}</div>
</section>

<div class="gk-tool">
<div class="gk-tool-col">
<form class="gk-card gk-stack gk-o1" id="pform" novalidate onsubmit="return false">
<fieldset class="gk-fieldset">
<legend class="gk-legend">Vad vill du räkna ut?</legend>
<div class="gk-seg" style="--n:2" id="mode" role="group" aria-label="Typ av uträkning">
<button type="button" data-v="av" aria-pressed="true">X % av ett tal<small>15 % av 350</small></button>
<button type="button" data-v="andel" aria-pressed="false">Hur många procent?<small>25 av 500</small></button>
<button type="button" data-v="for" aria-pressed="false">Ökning eller minskning<small>200 → 250</small></button>
<button type="button" data-v="just" aria-pressed="false">Lägg till/dra av<small>500 + 25 %</small></button>
</div>
</fieldset>
<fieldset class="gk-fieldset" id="dirWrap" style="display:none">
<legend class="gk-legend">Lägga till eller dra av?</legend>
<div class="gk-seg" style="--n:2" id="dir" role="group" aria-label="Lägga till eller dra av procent">
<button type="button" data-v="upp" aria-pressed="true">Lägg till<small>t.ex. påslag</small></button>
<button type="button" data-v="ned" aria-pressed="false">Dra av<small>t.ex. rabatt</small></button>
</div>
</fieldset>
<div class="gk-field">
<label for="f1" id="f1l">Procent</label>
<div class="gk-input"><input id="f1" inputmode="decimal" autocomplete="off" value="15"><span class="unit" id="f1u">%</span></div>
</div>
<div class="gk-field">
<label for="f2" id="f2l">Av talet</label>
<div class="gk-input"><input id="f2" inputmode="decimal" autocomplete="off" value="350"><span class="unit" id="f2u" style="display:none">%</span></div>
<span class="gk-hint" id="fHint">Decimaler skriver du med komma, till exempel 12,5.</span>
</div>
</form>
</div>

<div class="gk-tool-col">
<section class="gk-card gk-result gk-o2" aria-live="polite" aria-labelledby="resLabel">
<div class="gk-result-label" id="resLabel">{S.e(label(M0))}</div>
<div class="gk-big"><strong id="resBig">{big(M0)}</strong></div>
<p class="gk-hint" id="resSub">{S.e(how(M0))}</p>
<div class="gk-tiles" id="tiles"></div>
<div id="verdict"></div>
<details class="gk-how">
<summary>Så räknade vi</summary>
<div id="how"></div>
</details>
</section>

<section class="gk-card gk-stack gk-no-print gk-o6" style="gap:10px" aria-labelledby="nextH">
<h2 id="nextH" style="font-size:22px">Nästa steg</h2>
<a class="gk-linkcard" href="/kalkylatorer/momsraknare"><span>Räkna moms<small>Momsräknaren – lägg till eller dra av moms på ett pris</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/ranta-pa-ranta"><span>Ränta på ränta<small>Se hur pengar växer med några procent om året</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/inflationskalkylator"><span>Inflationskalkylator<small>Hur mycket har priserna ökat i procent?</small></span>{CHEV}</a>
</section>
</div>
</div>

<div class="gk-prose">
<h2>Vanliga uträkningar</h2>
{table_html()}

<h2>Hur räknar man ut procent?</h2>
<p>Procent betyder hundradel, så 15 % är 15 / 100 = 0,15. De tre vanligaste uträkningarna:</p>
<ul>
<li><strong>X % av ett tal:</strong> talet × X / 100. 15 % av 350 = 350 × 15 / 100 = {EX['av']}.</li>
<li><strong>Hur många procent:</strong> delen / det hela × 100. 25 av 500 = 25 / 500 × 100 = {EX['andel']} %.</li>
<li><strong>Hela talet baklänges:</strong> delen / procenten × 100. Om 52,5 är 15 % är det hela 52,5 / 15 × 100 = {EX['hela']}.</li>
</ul>

<h2>Räkna ut ökning i procent</h2>
<p>Förändringen i procent är <strong>(nytt − gammalt) / gammalt × 100</strong>. Går ett pris från 200 till 250 kr är ökningen 50 / 200 × 100 = {EX['for']} %. Blir svaret negativt är det en minskning.</p>
<p>En ökning och en lika stor minskning tar inte ut varandra. Från 250 tillbaka till 200 är en minskning med {EX['back']} %, och 250 minus 25 % blir {EX['for25']}.</p>

<h2>Lägga till och dra av procent</h2>
<p>Multiplicera med förändringsfaktorn. Lägga till 25 % är att multiplicera med 1,25: 500 × 1,25 = {EX['upp']}. Dra av 20 % är att multiplicera med 0,8: 500 × 0,8 = {EX['ned']}. Ska du räkna moms finns en egen <a href="/kalkylatorer/momsraknare">momsräknare</a>.</p>

<h2>Procent och procentenheter</h2>
<p>Går räntan från 2 % till 3 % har den ökat med <strong>1 procentenhet</strong> men med <strong>{EX['ranta']} procent</strong>. Procentenheter är skillnaden mellan två procentsatser. Procent visar hur stor förändringen är jämfört med där man började. Skriv 2 % till 3 % i rutan överst så får du båda.</p>

<h2>Vanliga frågor om procent</h2>
<div class="gk-faq">{faq_html}</div>

<h2>Källor</h2>
<ul>
<li><a href="{SRC['uhr']}" target="_blank" rel="noopener">Universitets- och högskolerådet (UHR) – Tolkning av sifferuppgifter (2021)</a> – formlerna delen / hela = procenten, hela × procenten = delen och delen / procenten = hela, och skillnaden mellan procent och procentenheter (en andel som ökar från 4 % till 6 % ökar med 2 procentenheter, men med 50 %)</li>
<li>Förändring i procent, påslag och avdrag räknas med vanlig aritmetik: (nytt − gammalt) / gammalt × 100 och talet × (100 ± procenten) / 100. Svaren avrundas till högst två decimaler.</li>
</ul>

<h2>Räkna vidare</h2>
<div class="gk-list-links">
<a class="gk-linkcard" href="/kalkylatorer/loneforhandling"><span>Löneförhandling<small>Vilket lönekrav ska du lägga?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/kalkylatorer/sparkalkylator"><span>Sparkalkylator<small>Hur mycket behöver du spara per månad?</small></span>{CHEV}</a>
<a class="gk-linkcard" href="/artiklar/vad-ar-inflation"><span>Guide: Vad är inflation?<small>Så mäts prisökningar i procent</small></span>{CHEV}</a>
</div>
</div>
</main>
<script id="gk-pr" type="application/json">{json.dumps(K, ensure_ascii=False)}</script>
<script>
{JS}
</script>
"""
    return (S.head(title, desc, PATH, og_title="Procenträknare – räkna ut procent direkt", jsonld=ld, extra_head=CSS)
            + S.header() + body + S.footer("Svaren avrundas till högst två decimaler."))


JS = r"""
(function () {
  'use strict';
  /* Modell – samma som scripts/build_procent.py */
  var NB = ' ', MI = '−';
  var NUM = '[0-9]{1,3}(?: [0-9]{3}(?![0-9]))+(?:[.,][0-9]+)?|[0-9]+(?:[.,][0-9]+)*';
  var RE_NUM = new RegExp('^(?:' + NUM + ')'), RE_FALT = new RegExp('^-?(?:' + NUM + ')$'), RE_WORD = /^[a-zåäöéü]+/;
  var HELP = 'Skriv till exempel 15 % av 350, 25 av 500, 500 + 25 % eller 200 till 250.';
  var S_AV = ['av', 'utav', 'of'], S_TILL = ['till', '>'], S_AR = ['är', 'blir', 'utgör', 'motsvarar'],
    S_SUB = ['rabatt', 'dra', 'drar', 'avdrag', 'minus', 'minska', 'sänk', 'sänka', 'sänkt', 'rea'],
    S_ADD = ['lägg', 'lägga', 'plus', 'påslag', 'öka', 'höj', 'höja', 'höjd', 'addera'],
    S_MUL = ['*', 'x', 'gånger', 'ggr'], S_DIV = ['/', 'delat', 'delad'], S_PLUS = ['+', 'plus'], S_MINUS = ['-', 'minus'],
    S_CHG = ['ökning', 'minskning', 'förändring', 'ökat', 'minskat'];

  function grp(ip) { var out = ''; while (ip.length > 3) { out = NB + ip.slice(-3) + out; ip = ip.slice(0, -3); } return ip + out; }
  function F(x, dec) {
    if (dec == null) dec = 2;
    if (x == null || !isFinite(x) || Math.abs(x) >= 1e21) return '–';
    if (Math.abs(x) >= 1e12) dec = 0;
    var f = Math.pow(10, dec), r = Math.floor(x * f + 0.5) / f;
    if (r === 0 && x !== 0 && dec < 6) return F(x, 6);
    var s = Math.abs(r).toFixed(dec).split('.'), fp = (s[1] || '').replace(/0+$/, '');
    return (r < 0 ? MI : '') + grp(s[0]) + (fp ? ',' + fp : '');
  }
  function T(x) { return F(x, 6); }
  function P(x) { return F(x, 6) + NB + '%'; }
  function sgn(s) { return (s.charAt(0) === MI || s === '0' || s === '–') ? s : '+' + s; }

  function av(p, tal) { return p * tal / 100; }
  function andel(d, h) { return h === 0 ? null : d / h * 100; }
  function forandring(fr, ti) { return fr === 0 ? null : (ti - fr) / Math.abs(fr) * 100; }
  function justera(tal, p, upp) { return upp ? tal * (100 + p) / 100 : tal * (100 - p) / 100; }
  function hela(d, p) { return p === 0 ? null : d * 100 / p; }

  function norm(s) {
    s = String(s == null ? '' : s).toLowerCase();
    s = s.replace(/[    \t\r\n]/g, ' ').replace(/[−–—]/g, '-');
    s = s.replace(/×/g, '*').replace(/·/g, '*').replace(/÷/g, '/').replace(/→/g, '>').replace(/->/g, '>').replace(/=>/g, '>');
    s = s.replace(/procent/g, '%').replace(/ +/g, ' ');
    return s.trim();
  }
  function tonum(raw) {
    var t = raw.replace(/ /g, ''), nd = t.split('.').length - 1, nc = t.split(',').length - 1;
    if (nd && nc) t = t.lastIndexOf(',') > t.lastIndexOf('.') ? t.replace(/\./g, '').replace(',', '.') : t.replace(/,/g, '');
    else if (nc) t = nc > 1 ? t.replace(/,/g, '') : t.replace(',', '.');
    else if (nd > 1) t = t.replace(/\./g, '');
    return parseFloat(t.match(/^[0-9]+(?:\.[0-9]+)?/)[0]);
  }
  function isd(c) { return c >= '0' && c <= '9'; }
  function tokens(s) {
    var out = [], i = 0, n = s.length;
    while (i < n) {
      var c = s.charAt(i);
      if (c === ' ') { i++; continue; }
      var j = i, neg = false;
      if (c === '-' && i + 1 < n && isd(s.charAt(i + 1)) && !(out.length && out[out.length - 1].t === 'n')) { j = i + 1; neg = true; }
      if (isd(s.charAt(j))) {
        var raw = s.slice(j).match(RE_NUM)[0], v = tonum(raw);
        out.push({ t: 'n', v: neg ? -v : v, p: false }); i = j + raw.length; continue;
      }
      if (c === '%') {
        var last = out[out.length - 1];
        if (last && last.t === 'n' && !last.p) last.p = true; else out.push({ t: 'w', w: '%' });
        i++; continue;
      }
      if ('+-*/>'.indexOf(c) >= 0) { out.push({ t: 'w', w: c }); i++; continue; }
      var m = s.slice(i).match(RE_WORD);
      if (m) { out.push({ t: 'w', w: m[0] }); i += m[0].length; continue; }
      i++;
    }
    return out;
  }
  function falt(s) {
    var t = norm(s).replace(/%/g, '').trim();
    if (!RE_FALT.test(t)) return null;
    var v = tonum(t.replace(/^-/, ''));
    return t.charAt(0) === '-' ? -v : v;
  }
  function has(ws, set) { for (var i = 0; i < ws.length; i++) if (set.indexOf(ws[i]) >= 0) return true; return false; }

  function mk(typ, a, b, pp) {
    var r = { typ: typ, a: a, b: b == null ? null : b, pp: !!pp, svar: null, fel: '' };
    if (typ === 'av') r.svar = av(a, b);
    else if (typ === 'andel') { r.svar = andel(a, b); if (r.svar === null) r.fel = 'Det hela kan inte vara 0 – då går det inte att räkna ut procenten.'; }
    else if (typ === 'for') { r.svar = forandring(a, b); if (r.svar === null) r.fel = 'Från 0 går det inte att räkna förändringen i procent. Skillnaden är ' + F(b - a) + '.'; }
    else if (typ === 'upp' || typ === 'ned') r.svar = justera(a, b, typ === 'upp');
    else if (typ === 'hela') { r.svar = hela(a, b); if (r.svar === null) r.fel = 'Procenten kan inte vara 0.'; }
    else if (typ === 'mul') r.svar = a * b;
    else if (typ === 'div') { if (b === 0) r.fel = 'Det går inte att dela med 0.'; else r.svar = a / b; }
    else if (typ === 'sum') r.svar = a + b;
    else if (typ === 'diff') r.svar = a - b;
    else if (typ === 'dec') r.svar = a / 100;
    if (r.svar !== null && !(Math.abs(r.svar) < 1e15)) { r.svar = null; r.fel = 'Talet blir för stort för att visa.'; }
    return r;
  }

  function tolka(text) {
    var s = norm(text);
    if (!s) return { typ: 'tom', svar: null, fel: HELP };
    var tk = tokens(s), idx = [];
    tk.forEach(function (t, i) { if (t.t === 'n') idx.push(i); });
    function words(a, b) { return tk.slice(a, b).filter(function (t) { return t.t === 'w'; }).map(function (t) { return t.w; }); }
    if (idx.length === 1) {
      var t0 = tk[idx[0]];
      if (t0.p) return mk('dec', t0.v);
      return { typ: 'fel', svar: null, fel: 'Vad vill du räkna ut med ' + T(t0.v) + '? Skriv till exempel ' + T(t0.v) + ' % av 350.' };
    }
    if (idx.length !== 2) return { typ: 'fel', svar: null, fel: HELP };
    var n1 = tk[idx[0]], n2 = tk[idx[1]], a = n1.v, b = n2.v;
    var pre = words(0, idx[0]), mid = words(idx[0] + 1, idx[1]), post = words(idx[1] + 1, tk.length), all = pre.concat(mid, post);
    if (n1.p && !n2.p) {
      if (has(mid, S_AV) || has(mid, S_MUL)) return mk('av', a, b);
      if (has(all, S_SUB)) return mk('ned', b, a);
      if (has(all, S_ADD)) return mk('upp', b, a);
      return mk('av', a, b);
    }
    if (!n1.p && n2.p) {
      if (has(mid, S_PLUS)) return mk('upp', a, b);
      if (has(mid, S_MINUS)) return mk('ned', a, b);
      if (has(mid, S_MUL)) return mk('av', b, a);
      if (has(mid, S_AR)) return mk('hela', a, b);
      if (has(all, S_SUB)) return mk('ned', a, b);
      if (has(all, S_ADD) || mid.indexOf('med') >= 0) return mk('upp', a, b);
      return mk('av', b, a);
    }
    if (!n1.p && !n2.p) {
      if (has(mid, S_AV)) return mk('andel', a, b);
      if (has(pre, S_AV) && has(mid, S_AR)) return mk('andel', b, a);
      if (has(mid, S_TILL)) return mk('for', a, b);
      if (has(mid, S_MUL)) return mk('mul', a, b);
      if (has(mid, S_DIV)) return all.indexOf('%') >= 0 ? mk('andel', a, b) : mk('div', a, b);
      if (has(mid, S_PLUS)) return mk('sum', a, b);
      if (has(mid, S_MINUS)) return mk('diff', a, b);
      if (has(all, S_CHG)) return mk('for', a, b);
      return { typ: 'fel', svar: null, fel: HELP };
    }
    if (has(mid, S_TILL) || has(all, S_CHG)) return mk('for', a, b, true);
    if (has(mid, S_AV)) return mk('av', a, b, true);
    return { typ: 'fel', svar: null, fel: HELP };
  }

  function big(r) {
    if (r.fel || r.svar == null) return '–';
    if (r.typ === 'dec') return F(r.svar, 6);
    var s = F(r.svar);
    if (r.typ === 'for') s = sgn(s);
    if (r.typ === 'andel' || r.typ === 'for' || (r.typ === 'av' && r.pp)) s += NB + '%';
    return s;
  }
  function label(r) {
    var t = r.typ, a = r.a, b = r.b, X = r.pp ? P : T;
    if (t === 'av') return P(a) + ' av ' + X(b) + ' är';
    if (t === 'andel') return 'Så många procent är ' + T(a) + ' av ' + T(b) + ':';
    if (t === 'for') return 'Förändring från ' + X(a) + ' till ' + X(b) + ':';
    if (t === 'upp') return T(a) + ' + ' + P(b) + ' är';
    if (t === 'ned') return T(a) + ' ' + MI + ' ' + P(b) + ' är';
    if (t === 'hela') return T(a) + ' är ' + P(b) + ' av';
    if (t === 'mul') return T(a) + ' × ' + T(b) + ' =';
    if (t === 'div') return T(a) + ' / ' + T(b) + ' =';
    if (t === 'sum') return T(a) + ' + ' + T(b) + ' =';
    if (t === 'diff') return T(a) + ' ' + MI + ' ' + T(b) + ' =';
    if (t === 'dec') return P(a) + ' som decimaltal är';
    if (t === 'tom') return 'Skriv en uträkning';
    return 'Det gick inte att tolka';
  }
  function how(r) {
    if (r.fel || r.svar == null) return r.fel || HELP;
    var t = r.typ, a = r.a, b = r.b, v = r.svar, B = big(r), s;
    if (t === 'av') return T(b) + ' × ' + T(a) + ' / 100 = ' + B + '.';
    if (t === 'andel') return T(a) + ' / ' + T(b) + ' × 100 = ' + B + '.';
    if (t === 'for') {
      s = '(' + T(b) + ' ' + MI + ' ' + T(a) + ') / ' + T(Math.abs(a)) + ' × 100 = ' + B;
      s += v > 0 ? ' – en ökning' : (v < 0 ? ' – en minskning' : '');
      if (r.pp) { var d = F(Math.abs(b - a)); s += '. Skillnaden är ' + d + ' procentenhet' + (d === '1' ? '' : 'er'); }
      return s + '.';
    }
    if (t === 'upp') return T(a) + ' × ' + F((100 + b) / 100, 6) + ' = ' + B + '. Påslaget är ' + F(v - a) + '.';
    if (t === 'ned') return T(a) + ' × ' + F((100 - b) / 100, 6) + ' = ' + B + '. Avdraget är ' + F(a - v) + '.';
    if (t === 'hela') return T(a) + ' / ' + T(b) + ' × 100 = ' + B + '.';
    if (t === 'mul') {
      if (b > 0 && b < 1) return 'Samma sak som ' + P(b * 100) + ' av ' + T(a) + ', eller ' + T(a) + ' ' + MI + ' ' + F((1 - b) * 100) + NB + '%.';
      if (b > 1 && b < 10) return 'Samma sak som ' + T(a) + ' + ' + F((b - 1) * 100) + NB + '%: ' + T(a) + ' + ' + F(a * (b - 1)) + ' = ' + B + '.';
      return T(a) + ' × ' + T(b) + ' = ' + B + '.';
    }
    if (t === 'div') {
      if (b > 1 && b < 10) return 'Samma sak som att ta bort ett påslag på ' + F((b - 1) * 100) + NB + '% från ' + T(a) + '.';
      return T(a) + ' / ' + T(b) + ' = ' + B + '.';
    }
    if (t === 'sum') return 'Vill du lägga till procent? Skriv ' + T(a) + ' + ' + T(b) + ' %.';
    if (t === 'diff') return 'Vill du dra av procent? Skriv ' + T(a) + ' ' + MI + ' ' + T(b) + ' %.';
    if (t === 'dec') return T(a) + ' / 100 = ' + B + '. ' + P(a) + ' av ett tal är talet × ' + B + '.';
    return HELP;
  }
  function quick(text) { var r = tolka(text); return { q: text, typ: r.typ, svar: r.svar, big: big(r), label: label(r), how: how(r) }; }

  window.GKProcent = { tolka: tolka, quick: quick, mk: mk, big: big, label: label, how: how, F: F, falt: falt,
    av: av, andel: andel, forandring: forandring, justera: justera, hela: hela, T: T, P: P, sgn: sgn, NB: NB, MI: MI };
})();

document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var C = JSON.parse(document.getElementById('gk-pr').textContent);
  var G = window.GKProcent, F = G.F, T = G.T, P = G.P, NB = G.NB, MI = G.MI;
  var $ = function (id) { return document.getElementById(id); };

  function setBig(el, txt) {
    el.textContent = txt;
    var n = txt.replace(/\s/g, '').length;
    el.classList.toggle('is-long', n > 9 && n <= 13);
    el.classList.toggle('is-xlong', n > 13);
  }

  /* ── Snabbfältet ── */
  function runQuick() {
    var r = G.quick($('q').value);
    $('qLabel').textContent = r.label;
    setBig($('qBig'), r.big);
    $('qHow').textContent = r.how;
  }
  $('q').addEventListener('input', runQuick);
  $('q').addEventListener('focus', function () { var el = this; setTimeout(function () { try { el.select(); } catch (e) {} }, 0); });
  document.querySelectorAll('.pq-ex [data-q]').forEach(function (b) {
    b.addEventListener('click', function () { $('q').value = b.getAttribute('data-q'); runQuick(); });
  });

  /* ── Fyra lägen ── */
  var MODES = {
    av: { l1: 'Procent', u1: true, l2: 'Av talet', u2: false },
    andel: { l1: 'Delen', u1: false, l2: 'Av det hela', u2: false },
    for: { l1: 'Från (gammalt värde)', u1: false, l2: 'Till (nytt värde)', u2: false },
    just: { l1: 'Talet', u1: false, l2: 'Procent', u2: true }
  };
  var st = { mode: 'av', dir: 'upp', v: {} };
  Object.keys(C.LAGE).forEach(function (k) { st.v[k] = C.LAGE[k].slice(); });

  function press(id, v) { $(id).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x.getAttribute('data-v') === v ? 'true' : 'false'); }); }
  function seg(id, cb) {
    $(id).addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      press(id, b.getAttribute('data-v')); cb(b.getAttribute('data-v')); calc();
    });
  }
  function setMode(m) {
    st.v[st.mode] = [$('f1').value, $('f2').value];
    st.mode = m;
    var M = MODES[m];
    $('f1l').textContent = M.l1; $('f2l').textContent = M.l2;
    $('f1u').style.display = M.u1 ? '' : 'none'; $('f2u').style.display = M.u2 ? '' : 'none';
    $('f1').value = st.v[m][0]; $('f2').value = st.v[m][1];
    $('dirWrap').style.display = m === 'just' ? '' : 'none';
  }
  seg('mode', setMode);
  seg('dir', function (v) { st.dir = v; });
  ['f1', 'f2'].forEach(function (id) { $(id).addEventListener('input', calc); });

  function tile(l, v, s) { return '<div class="gk-tile"><span>' + l + '</span><strong>' + v + '</strong>' + (s ? '<small class="gk-hint" style="display:block;margin-top:2px">' + s + '</small>' : '') + '</div>'; }
  function verdict(kind, title, text) {
    var ico = kind === 'good' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
    return '<div class="gk-verdict ' + kind + '">' + ico + '<div><strong>' + title + '</strong><span>' + text + '</span></div></div>';
  }
  function pct(x) { return G.sgn(F(x)) + NB + '%'; }

  function calc() {
    var m = st.mode, x = G.falt($('f1').value), y = G.falt($('f2').value);
    if (x === null || y === null) {
      $('resLabel').textContent = 'Svar'; setBig($('resBig'), '–');
      $('resSub').textContent = 'Fyll i båda fälten med siffror.';
      $('tiles').innerHTML = ''; $('verdict').innerHTML = ''; $('how').innerHTML = '';
      return;
    }
    var r = G.mk(m === 'just' ? st.dir : m, x, y);
    $('resLabel').textContent = G.label(r);
    setBig($('resBig'), G.big(r));
    $('resSub').textContent = G.how(r);
    var t = '', v = '', h = '';
    if (r.svar !== null && !r.fel) {
      var s = r.svar;
      if (m === 'av') {
        t = tile('Resten, ' + P(100 - x), F(y - s)) + tile(T(y) + ' + ' + P(x), F(G.justera(y, x, true))) +
          tile('Som decimaltal', F(x / 100, 6)) + tile('1 % av ' + T(y), F(y / 100));
        v = verdict('info', 'Räkna i huvudet', '10 % av ' + T(y) + ' är ' + F(y / 10) + ' – flytta decimalkommat ett steg åt vänster.' + (x !== 10 && x > 0 ? ' ' + P(x) + ' är ' + F(x / 10, 6) + ' gånger så mycket.' : ''));
        h = '<p>Formel: talet × procenten / 100. Eller talet × procenten i decimalform: ' + T(y) + ' × ' + F(x / 100, 6) + '.</p>';
      } else if (m === 'andel') {
        t = tile('Resten', F(100 - s) + NB + '%', F(y - x)) + tile('Som decimaltal', F(x / y, 6)) +
          (x > 0 && y / x >= 2 ? tile('Ungefär', '1 av ' + F(y / x, 0)) : '');
        v = verdict('info', 'Kontroll', F(s) + ' % av ' + T(y) + ' är ' + F(G.av(s, y)) + '.' + (x > y ? ' Delen är större än det hela, därför blir det mer än 100 %.' : ''));
        h = '<p>Formel: delen / det hela × 100.</p>';
      } else if (m === 'for') {
        var back = G.forandring(y, x);
        t = tile('Skillnad', G.sgn(F(y - x))) + (x > 0 ? tile('Förändringsfaktor', '× ' + F(y / x, 4)) : '') +
          (back !== null ? tile('Tillbaka till ' + T(x), pct(back)) : '');
        v = s === 0 ? verdict('info', 'Ingen förändring', 'Talen är lika stora.')
          : verdict('info', 'Procent eller procentenheter?', 'Är ' + T(x) + ' och ' + T(y) + ' procentsatser, till exempel räntor, har de ändrats med ' + F(Math.abs(y - x)) + ' procentenhet' + (F(Math.abs(y - x)) === '1' ? '' : 'er') + ' – men med ' + F(Math.abs(s)) + ' %.');
        h = '<p>Formel: (nytt ' + MI + ' gammalt) / gammalt × 100. Är det gamla värdet negativt delar vi med talet utan minustecken.</p>';
      } else {
        var up = st.dir === 'upp', b2 = G.forandring(s, x), round = G.justera(s, y, !up);
        t = tile(up ? 'Påslag' : 'Avdrag', F(Math.abs(s - x))) + tile('Förändringsfaktor', '× ' + F((up ? 100 + y : 100 - y) / 100, 6)) +
          (b2 !== null ? tile('Tillbaka till ' + T(x), pct(b2)) : '');
        v = verdict('info', 'Det tar inte ut varandra', T(x) + (up ? ' + ' : ' ' + MI + ' ') + P(y) + (up ? ' ' + MI + ' ' : ' + ') + P(y) + ' blir ' + F(round) + ', inte ' + T(x) + '.');
        h = '<p>Lägga till: talet × (100 + procenten) / 100. Dra av: talet × (100 ' + MI + ' procenten) / 100.</p><p>Ska du räkna moms finns en egen <a href="/kalkylatorer/momsraknare">momsräknare</a>.</p>';
      }
    }
    $('tiles').innerHTML = t;
    $('verdict').innerHTML = v;
    $('how').innerHTML = h + '<p>' + G.how(r) + '</p><p>Svaren avrundas till högst två decimaler.</p>';
  }

  runQuick();
  calc();
});
"""


CASES_Q = ["15% av 350", "vad är 30% av 1752000", "30 % av 1 752 000", "25 av 500", "500*1,25", "500 + 25%",
           "500 - 20 %", "200 till 250", "250 till 200", "från -200 till -100", "0 till 50", "25 av 0",
           "12,5 % av 80", "52,5 är 15 % av", "hur många procent är 45 av 180", "2 % till 3 %",
           "dra av 20% från 500", "625/1,25", "1.752.000 * 0,3", "hur mycket är 15", "20 % rabatt på 1 299,90",
           "1 av 3", "0,001 % av 50", "hur många % av 500 är 25", "10 / 0", "25%"]
CASES_M = [("av", "15", "350"), ("av", "12,5", "1 299,90"), ("andel", "25", "500"), ("andel", "25", "0"),
           ("for", "250", "200"), ("for", "0", "50"), ("for", "-200", "-100"), ("upp", "500", "25"), ("ned", "1 299,90", "20")]


def mode_ref(m, s1, s2):
    x, y = falt(s1), falt(s2)
    r = mk(m, x, y)
    return {"m": m, "f1": s1, "f2": s2, "svar": r["svar"], "big": big(r), "label": label(r), "how": how(r)}


def main():
    out = os.path.join(ROOT, "kalkylatorer", "procentraknare.html")
    html_text = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print("Skrev", out, len(html_text), "tecken")
    for q in CASES_Q:
        r = quick(q)
        print(f"{q!r:32} {r['typ']:6} {r['big']!r:16} {r['how']}")
    for c in CASES_M:
        r = mode_ref(*c)
        print(c, r["big"], "|", r["how"])


if __name__ == "__main__":
    main()
