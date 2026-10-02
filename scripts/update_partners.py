#!/usr/bin/env python3
"""Lägger in annonsrutor (Adtraction-partner) på kalkylatorsidorna från data/partners.json.

En annonsör visas först när den har en spårningslänk (`tracking`), dvs. är godkänd i Adtraction.
Rutan döljs helt så länge ingen i kategorin är godkänd, eller om kategorin har "aktiv": false
(t.ex. Nordnet, där texten också måste godkännas av annonsören).

Varje ruta står mellan markörerna <!--GK-PARTNER:<kategori>:START--> och <!--GK-PARTNER:<kategori>:END-->.
Saknas markörerna på en äldre sida läggs rutan in före första <div class="info-section">.
Elkostnads- och leasingsidan har markörerna i sina byggmallar (build_elkostnad.py, build_leasing.py).
En kategori kan visas på flera sidor: "_sidor": {"kat": [{"fil": ..., "variant": ...}, ...]}.

    python3 scripts/update_partners.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gk2_shell as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e = html.escape


def reklam_for(d):
    n = [p["namn"] for p in d["partners"]]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " och " + n[-1]


def render(kat, d, variant):
    d = dict(d, partners=[p for p in d["partners"] if p["tracking"]])  # bara godkända annonsörer
    def namn(p):  # liten logga (lagrad på sajten, t.ex. assets/partners/fortum.png) eller bara namnet
        if p.get("logo"):
            return (f'<img src="{e(p["logo"])}" alt="{e(p["namn"])}" width="{p.get("logo_w", 94)}" height="22" '
                    'style="display:block;height:22px;width:auto;margin:2px 0 4px" loading="lazy">')
        return e(p["namn"])
    links = "".join(
        f'<a class="gk-linkcard" href="{e(p["tracking"])}" target="_blank" rel="sponsored noopener" '
        f'data-gkp="{e(p["id"])}" data-gkp-kat="{kat}"><span>{namn(p)}<small>{e(p["text"])}</small></span>{S.ICON_CHEV}</a>'
        for p in d["partners"])
    neutral = ""
    if d.get("neutral"):
        n = d["neutral"]
        neutral = (f'<p class="gk-hint" style="margin:0">{e(n["text"])} '
                   f'<a href="{e(n["url"])}" target="_blank" rel="noopener">{e(n["namn"])}</a>.</p>')
    risk = (f'<p class="gk-hint" style="margin:0;padding:10px 12px;border-radius:10px;background:var(--gk-surface-2)">'
            f'<strong>Risk:</strong> {e(d["risk"])}</p>') if d.get("risk") else ""
    hid = f"gkp-{kat}"
    tag = "h3" if variant == "inline" else "h2"
    box = ('display:flex;flex-direction:column;gap:10px;margin:4px 0 0;padding-top:14px;border-top:1px solid var(--gk-border)' if variant == "inline" else
           'display:flex;flex-direction:column;gap:10px;margin:24px 0;padding:18px;border:1px solid var(--gk-border);'
           'border-radius:16px;background:var(--gk-surface)')
    return (f'<section class="gk-partner" aria-labelledby="{hid}" data-gkp-sec="{kat}" style="{box}">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">'
            f'<{tag} id="{hid}" style="font-size:{18 if variant == "inline" else 20}px;line-height:1.25;margin:0">{e(d["rubrik"])}</{tag}>'
            f'<span class="gk-ad-label">ANNONS</span></div>'
            f'<p class="gk-hint" style="margin:0"><strong>Annons – reklam för {e(reklam_for(d))}.</strong> {e(d["intro"])}'
            f'{(" " + e(d["intro_flera"])) if d.get("intro_flera") and len(d["partners"]) > 1 else ""}</p>'
            f'<div style="display:flex;flex-direction:column;gap:8px">{links}</div>{risk}{neutral}'
            '<script>(function(){if(window.__gkp)return;window.__gkp=1;document.addEventListener("click",function(ev){'
            'var a=ev.target.closest&&ev.target.closest("[data-gkp]");if(a&&typeof gtag==="function")'
            'gtag("event","partner_klick",{partner:a.getAttribute("data-gkp"),kategori:a.getAttribute("data-gkp-kat")});});'
            'if("IntersectionObserver" in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){'
            'if(en.isIntersecting){io.unobserve(en.target);if(typeof gtag==="function")gtag("event","partner_visning",'
            '{kategori:en.target.getAttribute("data-gkp-sec")});}});},{threshold:0.5});'
            'document.querySelectorAll(".gk-partner[data-gkp-sec]").forEach(function(s){io.observe(s);});}})();</script>'
            '</section>')


def main():
    with open(os.path.join(ROOT, "data", "partners.json"), encoding="utf-8") as f:
        data = json.load(f)
    jobb = [(kat, sida) for kat, sidor in data["_sidor"].items()
            for sida in (sidor if isinstance(sidor, list) else [sidor])]
    for kat, sida in jobb:
        path = os.path.join(ROOT, sida["fil"])
        with open(path, encoding="utf-8") as f:
            s = f.read()
        start, end = f"<!--GK-PARTNER:{kat}:START-->", f"<!--GK-PARTNER:{kat}:END-->"
        aktiv = data[kat].get("aktiv", True)
        godkanda = [p for p in data[kat]["partners"] if p["tracking"]]
        block = render(kat, data[kat], sida["variant"]) if aktiv and godkanda else ""
        if start in s:
            s = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: start + block + end, s, count=1, flags=re.S)
            how = "uppdaterad"
        else:
            i = s.find('<div class="info-section">')
            if i < 0:
                print("HITTAR INGEN PLATS:", sida["fil"]); continue
            s = s[:i] + start + block + end + "\n        " + s[i:]
            how = "inlagd"
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        print(f"{kat}: {how} i {sida['fil']} ({len(data[kat]['partners'])} partner, {len(godkanda)} godkända)"
              + ("" if block else " – DOLD (" + ("aktiv: false" if not aktiv else "ingen godkänd ännu") + ")"))


if __name__ == "__main__":
    main()
