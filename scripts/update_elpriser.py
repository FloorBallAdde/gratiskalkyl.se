#!/usr/bin/env python3
"""Hämtar SCB:s elhandelspriser och uppdaterar elkostnadssidan.

Körs automatiskt en gång om dagen den 23–28 varje månad (GitHub Actions,
.github/workflows/elpriser.yml) och kan köras för hand:

    python3 scripts/update_elpriser.py

Källa: SCB/Energimyndigheten, Elhandelspriser på elenergi för nytecknade
avtal (tabell SSDManadElhandelpris) och Elnätspriser (SSDArElnatspris).

Skriptet ändrar ingenting om kontrollerna inte går igenom, och avslutar
då med felkod 1 så att GitHub skickar ett mejl.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "elpriser.json")
PAGE_FILE = os.path.join(ROOT, "kalkylatorer", "elkostnadskalkylator.html")

API = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/EN/EN0301/EN0301A/"
TABLE_URL = "https://www.statistikdatabasen.scb.se/goto/sv/ssd/SSDManadElhandelpris"

AVTAL = ["rorligt", "avtal1ar", "avtal2ar", "avtal3ar", "anvisat"]
OMRADEN = ["SE1", "SE2", "SE3", "SE4"]
KATEGORIER = ["1", "2", "3", "4"]
TYPKUND_KWH = {"1": 2000, "2": 5000, "3": 20000, "4": 30000}
N_MANADER = 13

# Energiskatt på el (Skatteverket). Ändras vid årsskiftet – se arsskifte-2027.md.
ENERGISKATT = {"ar": 2026, "ore": 36.0, "avdragNorr": 9.6}

MANADSNAMN = ["januari", "februari", "mars", "april", "maj", "juni", "juli",
              "augusti", "september", "oktober", "november", "december"]


def http_json(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json",
                                                          "User-Agent": "gratiskalkyl.se-elpriser"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8-sig"))


def fetch_scb():
    listing = http_json(API)
    updated = next((t.get("updated", "") for t in listing if t.get("id") == "SSDManadElhandelpris"), "")
    q = {"query": [{"code": "Tid", "selection": {"filter": "top", "values": [str(N_MANADER)]}}],
         "response": {"format": "json"}}
    pris = http_json(API + "SSDManadElhandelpris", q)
    nat = http_json(API + "SSDArElnatspris",
                    {"query": [{"code": "Tid", "selection": {"filter": "top", "values": ["1"]}}],
                     "response": {"format": "json"}})
    rows = [(d["key"][0], d["key"][1], d["key"][2], d["key"][3], d["values"][0]) for d in pris["data"]]
    natrows = [(d["key"][0], d["key"][1], d["key"][2], d["values"][0]) for d in nat["data"]]
    return rows, natrows, updated[:10]


def build_payload(rows, natrows, published, fetched=None):
    months = sorted({r[3] for r in rows})
    pris = {}
    for a, o, k, t, v in rows:
        pris.setdefault(a, {}).setdefault(o, {}).setdefault(k, {})[t] = v
    out = {a: {o: {k: [] for k in KATEGORIER} for o in OMRADEN} for a in AVTAL}
    for a in AVTAL:
        for o in OMRADEN:
            for k in KATEGORIER:
                out[a][o][k] = [float(pris[a][o][k][t]) for t in months]
    # Elnät: senaste år, viktat snitt
    nat_year = max(r[2] for r in natrows)
    elnat = {k: float(v) for k, w, y, v in natrows if w == "viktat" and y == nat_year}
    return {
        "kalla": "SCB och Energimyndigheten – Elhandelspriser på elenergi för nytecknade avtal",
        "tabell": "SSDManadElhandelpris",
        "tabellUrl": TABLE_URL,
        "publicerad": published,
        "hamtad": fetched or dt.date.today().isoformat(),
        "manader": [m[:4] + "-" + m[5:] for m in months],
        "typkundKwh": TYPKUND_KWH,
        "pris": out,
        "elnat": {"ar": int(nat_year), "ore": elnat, "kalla": "SCB – Elnätspriser per den 1 januari (SSDArElnatspris), viktat snitt"},
        "energiskatt": ENERGISKATT,
    }


def validate(p, previous=None):
    errs = []
    m = p["manader"]
    if len(m) != N_MANADER:
        errs.append(f"fel antal månader: {len(m)}")
    for i in range(1, len(m)):
        y0, m0 = map(int, m[i - 1].split("-")); y1, m1 = map(int, m[i].split("-"))
        if (y1 * 12 + m1) - (y0 * 12 + m0) != 1:
            errs.append(f"månader inte i följd: {m[i-1]} -> {m[i]}")
    for a in AVTAL:
        for o in OMRADEN:
            for k in KATEGORIER:
                vals = p["pris"][a][o][k]
                if len(vals) != len(m) or any(not (5 <= v <= 500) for v in vals):
                    errs.append(f"orimligt värde i {a}/{o}/{k}: {vals}")
    for k in KATEGORIER:
        v = p["elnat"]["ore"].get(k)
        if v is None or not (10 <= v <= 300):
            errs.append(f"orimligt elnätspris för kategori {k}: {v}")
    if previous and previous.get("manader") and m and m[-1] < previous["manader"][-1]:
        errs.append(f"senaste månad {m[-1]} är äldre än tidigare {previous['manader'][-1]}")
    return errs


def fit(vals_by_kat, i):
    """Snittpris = E + F/kWh. Returnerar (E öre/kWh, F kr/år) via minsta kvadrat."""
    xs = [1 / TYPKUND_KWH[k] for k in KATEGORIER]
    ys = [vals_by_kat[k][i] / 100 for k in KATEGORIER]
    mx = sum(xs) / 4; my = sum(ys) / 4
    F = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return (my - F * mx) * 100, F


def fmt1(v):
    return f"{v:.1f}".replace(".", ",")


def manad_text(ym):
    y, mm = ym.split("-")
    return f"{MANADSNAMN[int(mm) - 1]} {y}"


def render_blocks(p):
    last = p["manader"][-1]
    mtxt = manad_text(last)
    pub = p.get("publicerad") or ""
    data = '<script id="gk-eldata" type="application/json">' + json.dumps(p, ensure_ascii=False, separators=(",", ":")) + "</script>"
    meta = (f'Källa: SCB och Energimyndigheten · Senaste siffror: {mtxt}'
            + (f' (publicerade {int(pub[8:10])} {MANADSNAMN[int(pub[5:7]) - 1]})' if len(pub) == 10 else '')
            + ' · Uppdateras varje månad')

    def table(kat, label):
        rows = []
        for o in OMRADEN:
            cells = "".join(f"<td>{fmt1(p['pris'][a][o][kat][-1])}</td>" for a in ["rorligt", "avtal1ar", "avtal3ar", "anvisat"])
            rows.append(f"<tr><td>{o}</td>{cells}</tr>")
        return (f'<div class="gk-table-wrap"><table class="gk-table"><caption>{label}, {mtxt}. Öre/kWh exkl. moms och elskatt, '
                f'inkl. fasta avgifter. Källa: SCB.</caption><thead><tr><th scope="col">Elområde</th><th scope="col">Rörligt</th>'
                f'<th scope="col">Fast 1 år</th><th scope="col">Fast 3 år</th><th scope="col">Anvisat</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>')

    r3 = p["pris"]["rorligt"]["SE3"]["3"]; a3 = p["pris"]["anvisat"]["SE3"]["3"]
    avg12 = lambda v: sum(v[-12:]) / 12
    diff_kr = (avg12(a3) - avg12(r3)) / 100 * 20000 * 1.25
    kr = f"{int(round(abs(diff_kr), -2)):,}".replace(",", " ")
    if diff_kr > 0:
        anv = (f"<p>Anvisat avtal är det du får om du aldrig har valt elhandlare. För en villa med elvärme i SE3 kostade det de senaste "
               f"tolv månaderna i snitt {fmt1(avg12(a3))} öre/kWh mot {fmt1(avg12(r3))} öre för rörligt pris. Att byta hade sparat "
               f"ungefär {kr} kr om året inklusive moms.</p>")
    else:
        anv = (f"<p>Anvisat avtal är det du får om du aldrig har valt elhandlare. För en villa med elvärme i SE3 kostade det de senaste "
               f"tolv månaderna i snitt {fmt1(avg12(a3))} öre/kWh mot {fmt1(avg12(r3))} öre för rörligt pris.</p>")
    text = f"""<h2>Elpriser {mtxt} – snitt för nya avtal</h2>
<p>Så mycket kostade elhandeln i snitt för den som tecknade ett nytt avtal i {mtxt}, enligt SCB:s och Energimyndighetens officiella statistik. Priserna gäller själva elen och inkluderar elhandlarens fasta avgifter, men inte elnät, energiskatt och moms.</p>
{table("3", "Villa med elvärme, 20 000 kWh/år")}
{table("1", "Lägenhet, 2 000 kWh/år")}
{anv}"""
    return {"ELDATA": data, "ELMETA": meta, "ELTEXT": text}


def apply_markers(html_text, blocks):
    for key, content in blocks.items():
        pat = re.compile(r"(<!--%s:START-->)(.*?)(<!--%s:END-->)" % (key, key), re.S)
        if not pat.search(html_text):
            raise SystemExit(f"Markören {key} saknas i sidan")
        html_text = pat.sub(lambda m: m.group(1) + content + m.group(3), html_text)
    return html_text


def main():
    previous = None
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            previous = json.load(f)
    rows, natrows, published = fetch_scb()
    payload = build_payload(rows, natrows, published)
    errs = validate(payload, previous)
    if errs:
        print("Kontrollen misslyckades – inget ändrat:\n  " + "\n  ".join(errs))
        sys.exit(1)
    if previous and previous.get("manader") == payload["manader"] and previous.get("pris") == payload["pris"] \
            and previous.get("elnat") == payload["elnat"]:
        print("Inga nya siffror från SCB – inget ändrat.")
        return
    with open(PAGE_FILE, encoding="utf-8") as f:
        page = f.read()
    page = apply_markers(page, render_blocks(payload))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    with open(PAGE_FILE, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Uppdaterat till {payload['manader'][-1]} (publicerad {payload['publicerad']}).")


if __name__ == "__main__":
    main()
