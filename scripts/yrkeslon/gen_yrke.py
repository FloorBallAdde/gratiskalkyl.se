"""Genererar lönesidorna per yrke (kalkylatorer/yrkeslon/). Kör från repots rot:
    python3 scripts/yrkeslon/gen_yrke.py && python3 scripts/gk2_skin.py kalkylatorer/yrkeslon
Data: SCB lönestrukturstatistik 2025 (p1–p4.txt, n.txt). Skatt: scripts/skatt2026.py.
"""
import json, re, html, math, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(HERE))
from yrken import Y
T=open(os.path.join(HERE,'template.html'),encoding='utf-8').read()
STYLE=T[T.index('  <style>'):T.index('</head>')]
HEADTOP=T[:T.index('  <title>')]
NAV=T[T.index('<body>'):T.index('  <main class="container">')]
D={}
for f in ['p1','p2','p3','p4']:
    for l in open(os.path.join(HERE,f'{f}.txt'),encoding='utf-8'):
        c,n,s0,pu,pr,ag=l.rstrip('\n').split('|')
        D[c]=dict(scb=n,s0=[int(x)*100 for x in s0.split(',')],pub=[int(x)*100 for x in pu.split(',')],pri=[int(x)*100 for x in pr.split(',')],age=[int(x)*100 for x in ag.split(',')])
for tok in open(os.path.join(HERE,'n.txt')).read().split():
    p=tok.split(':')
    if p[0] in D: D[p[0]].update(antal=int(p[1]),mean=int(p[2])*100,men=int(p[3])*100,women=int(p[4])*100)
PBB=59200; SKIKT=643000; S=0.3238
def ga(FI):
    if FI<=0.99*PBB: g=0.423*PBB
    elif FI<=2.72*PBB: g=0.225*PBB+0.2*FI
    elif FI<=3.11*PBB: g=0.770*PBB
    elif FI<=7.88*PBB: g=1.081*PBB-0.1*FI
    else: g=0.293*PBB
    return min(math.ceil(g/100)*100,FI)
def jsa(AI,G):
    if AI<=0.91*PBB: u=AI-G
    elif AI<=3.24*PBB: u=0.91*PBB+0.3874*(AI-0.91*PBB)-G
    elif AI<=8.08*PBB: u=1.813*PBB+0.251*(AI-3.24*PBB)-G
    else: u=3.027*PBB-G
    return max(0,u*S)
import sys
sys.path.insert(0,os.path.dirname(HERE))
from skatt2026 import netto_manad
def netto(m):
    return netto_manad(m)
kr=lambda n: f"{int(round(n)):,}".replace(',',' ')+' kr'
e=lambda s: html.escape(s,quote=True)
def cap(s): return s[0].upper()+s[1:]
AGE=['18–24 år','25–34 år','35–44 år','45–54 år','55–64 år']
bycat={}
for y in Y: bycat.setdefault(y[3],[]).append(y)
out={}
def fixmob(h):
    h=re.sub(r'(<table class="table">.*?</table>)',r'<div style="overflow-x:auto;">\1</div>',h,flags=re.S)
    if '@media (max-width:560px){ .table' in h: return h
    return h.replace('</style>','    @media (max-width:560px){ .table{font-size:.8rem;} .table th,.table td{padding:8px 7px;} .table th{font-size:.7rem;letter-spacing:0;} .stats{gap:8px;} .stat{padding:12px 6px;} .stat .num{font-size:1.15rem;} }\n  </style>',1)
for code,slug,namn,cat in Y:
    d=D[code]; med,p10,p25,p75,p90=d['s0']; mean=d.get('mean',0)
    url=f'https://gratiskalkyl.se/kalkylatorer/yrkeslon/{slug}'
    nmed=netto(med)
    en='en' if namn.split()[0] not in ('VD','IT-chef') else 'en'
    title=f'Lön {namn} 2026 – medianlön {kr(med)}/mån enligt SCB'
    desc=f'Vad tjänar {en} {namn}? Medianlön {kr(med)}/mån ({kr(netto(med))} netto). Hälften tjänar mellan {kr(p25)} och {kr(p75)}. Lön efter ålder, sektor och kön – SCB 2025.' if p25 and p75 else f'Vad tjänar {en} {namn}? Medianlön {kr(med)}/mån ({kr(nmed)} netto). Lön efter ålder, sektor och kön enligt SCB 2025.'
    # spridning
    rows=[('10 % tjänar under',p10),('25 % tjänar under',p25),('Medianlön',med),('25 % tjänar över',p75),('10 % tjänar över',p90)]
    rows=[r for r in rows if r[1]]
    table=''.join(f'<tr><td>{a}</td><td class="num">{kr(v)}</td><td class="num">{kr(netto(v))}</td><td class="num">{kr(v*12)}</td></tr>' for a,v in rows)
    # sektor
    sek=''
    pm,prm=d['pub'][0],d['pri'][0]
    if pm and prm:
        diff=(prm-pm)/pm*100
        who='privat' if diff>0 else 'offentlig'
        sek=f'<h2>Privat eller offentlig sektor?</h2><p>Medianlönen för {namn} är <strong>{kr(prm)}</strong> i privat sektor och <strong>{kr(pm)}</strong> i offentlig sektor. '+(f'Det är {abs(diff):.0f} % högre i {who} sektor.'.replace('.',',',0) if abs(diff)>=2 else 'Skillnaden mellan sektorerna är liten.')+' Tänk på att offentlig sektor ofta har bättre tjänstepension och längre semester, så den totala ersättningen kan skilja mindre än lönen.</p>'
    elif pm or prm:
        s='offentlig' if pm else 'privat'
        sek=f'<h2>Var jobbar {namn}?</h2><p>SCB redovisar lön för {namn} främst i {s} sektor, där medianlönen är <strong>{kr(pm or prm)}</strong>. För den andra sektorn är antalet i urvalet för litet för att visas.</p>'
    # ålder
    ag=[(AGE[i],v) for i,v in enumerate(d['age']) if v]
    alder=''
    if len(ag)>=2:
        alder='<h2>Lön efter ålder</h2><table class="table"><thead><tr><th>Ålder</th><th class="num">Snittlön/mån</th><th class="num">Netto/mån</th></tr></thead><tbody>'+''.join(f'<tr><td>{a}</td><td class="num">{kr(v)}</td><td class="num">{kr(netto(v))}</td></tr>' for a,v in ag)+'</tbody></table>'
        lo,hi=ag[0],max(ag,key=lambda x:x[1])
        if hi[1]>lo[1]:
            alder+=f'<p>Lönen stiger med erfarenheten: från {kr(lo[1])} i snitt för {lo[0]} till {kr(hi[1])} för {hi[0]} – en skillnad på {kr(hi[1]-lo[1])} i månaden ({(hi[1]-lo[1])/lo[1]*100:.0f} %).</p>'
    # kön
    kon=''
    if d.get('men') and d.get('women'):
        pct=d['women']/d['men']*100
        kon=f'<h2>Lön för kvinnor och män</h2><p>Kvinnliga {namn if namn.endswith(("are","ör","ist","ekonom","ingenjör","läkare","chef","tekniker","sekreterare","assistent")) else namn} tjänar i snitt <strong>{kr(d["women"])}</strong> och män <strong>{kr(d["men"])}</strong> i månaden. Kvinnors lön motsvarar {pct:.0f} % av mäns inom yrket (ovägt snitt – skillnader i ålder och befattning påverkar).</p>'.replace('Kvinnliga '+namn,'Kvinnor som arbetar som '+namn)
    antal=f' Omkring <strong>{d["antal"]:,}</strong> personer i Sverige arbetar i yrket.'.replace(',',' ') if d.get('antal') else ''
    related=[y for y in bycat[cat] if y[0]!=code][:6]
    rel=''.join(f'<a href="/kalkylatorer/yrkeslon/{s}"><span class="em">💼</span><div class="name">Lön {n}</div></a>' for c,s,n,_ in related)
    faq=[
     (f'Vad tjänar {en} {namn} 2026?', f'Medianlönen för {en} {namn} är {kr(med)} i månaden enligt SCB:s lönestrukturstatistik 2025'+(f', och snittlönen är {kr(mean)}.' if mean else '.')+(f' Hälften tjänar mellan {kr(p25)} och {kr(p75)}.' if p25 and p75 else '')),
     (f'Vad blir nettolönen för {en} {namn}?', f'Med medianlönen {kr(med)} blir nettolönen cirka {kr(nmed)} i månaden efter skatt, räknat med 2026 års regler och genomsnittlig kommunalskatt 32,38 %.'),
     (f'Vad är ingångslönen för {en} {namn}?', (f'Nyanställda och personer med kort erfarenhet ligger ofta runt den lägre delen av lönespannet. 10 % i yrket tjänar under {kr(p10)} och 25 % under {kr(p25)}.' if p10 and p25 else f'Nyanställda ligger ofta under medianlönen på {kr(med)}.')+(f' Snittlönen för {ag[0][0]} är {kr(ag[0][1])}.' if ag else '')),
     (f'Hur mycket ska jag begära i löneförhandlingen?', f'Jämför din lön med medianlönen och snittet för din ålder. I kalkylatorn för löneförhandling väljer du {namn} och får ett konkret lönekrav och första bud baserat på SCB:s statistik.'),
    ]
    faq_ld={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub('<[^>]+>','',a)}} for q,a in faq]}
    bc_ld={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Hem","item":"https://gratiskalkyl.se/"},{"@type":"ListItem","position":2,"name":"Lön per yrke","item":"https://gratiskalkyl.se/kalkylatorer/yrkeslon/"},{"@type":"ListItem","position":3,"name":f"Lön {namn}","item":url}]}
    head=HEADTOP+f'''  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <link rel="canonical" href="{url}">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="https://gratiskalkyl.se/favicon.svg">
  <meta property="og:locale" content="sv_SE">
'''+''.join('  <script type="application/ld+json">\n'+json.dumps(x,ensure_ascii=False,indent=2)+'\n  </script>\n' for x in (faq_ld,bc_ld))+'\n'+STYLE+'</head>\n'
    body=NAV+f'''  <main class="container">
    <nav class="breadcrumb">
      <a href="/">Hem</a> &rsaquo; <a href="/kalkylatorer/yrkeslon/">Lön per yrke</a> &rsaquo; <span>Lön {namn}</span>
    </nav>

    <span class="tag">{cat}</span>
    <h1>Lön {namn} 2026</h1>
    <p class="lead">Medianlönen för {'en ' if en else ''}<strong>{namn}</strong> är <strong>{kr(med)} i månaden</strong> enligt SCB:s senaste lönestatistik (2025).{(' Hälften av alla i yrket tjänar mellan '+kr(p25)+' och '+kr(p75)+'.') if p25 and p75 else ''}{antal} Här ser du lönen efter ålder, sektor och kön – och vad du får ut efter skatt.</p>

    <div class="stats">
      <div class="stat"><div class="num">{kr(med)}</div><div class="lbl">Medianlön/mån</div></div>
      <div class="stat"><div class="num">{kr(nmed)}</div><div class="lbl">Netto/mån (median)</div></div>
      <div class="stat"><div class="num">{kr(mean) if mean else kr(med*12)}</div><div class="lbl">{'Snittlön/mån' if mean else 'Årslön (median)'}</div></div>
    </div>

    <div class="cta" style="margin-bottom:16px;">
      <h3>Dags att löneförhandla?</h3>
      <p style="color:rgba(255,255,255,0.92);font-size:0.95rem;">Se var din lön ligger jämfört med andra i yrket och vilket lönekrav du ska lägga.</p>
      <a href="/kalkylatorer/loneforhandling?yrke={code}">Räkna ut ditt lönekrav &rarr;</a>
    </div>

    <h2>Lönespridning för {namn}</h2>
    <p>Tabellen visar hur lönerna fördelar sig i yrket, från de 10 % som tjänar minst till de 10 % som tjänar mest. Månadslön inklusive fasta tillägg, heltid.</p>
    <table class="table">
      <thead><tr><th>Nivå</th><th class="num">Brutto/mån</th><th class="num">Netto/mån</th><th class="num">Brutto/år</th></tr></thead>
      <tbody>{table}</tbody>
    </table>

    <div class="info-box">
      <strong>Om nettolönen:</strong> beräknad med 2026 års skatteregler (grundavdrag, jobbskatteavdrag, skattereduktion för förvärvsinkomst, public service- och begravningsavgift) och genomsnittlig kommunalskatt 32,38 %. Räkna med just din kommun i <a href="/kalkylatorer/loneraknare">löneräknaren</a>.
    </div>

    {sek}
    {alder}
    {kon}

    <div class="cta">
      <h3>Räkna ut din exakta nettolön</h3>
      <p style="color:rgba(255,255,255,0.92);font-size:0.95rem;">Välj din kommun och skriv in din lön – se nettolönen på 10 sekunder.</p>
      <a href="/kalkylatorer/loneraknare">Öppna löneräknaren &rarr;</a>
    </div>

    <h2>Vanliga frågor</h2>
'''+''.join(f'    <h3>{q}</h3>\n    <p>{a}</p>\n' for q,a in faq)+f'''
    <h2>Lön i liknande yrken</h2>
    <div class="related">
      {rel}
      <a href="/kalkylatorer/yrkeslon/"><span class="em">📋</span><div class="name">Alla {len(Y)} yrken</div></a>
    </div>
  </main>

  <footer>
    <p>&copy; 2026 GratisKalkyl.se — Källa: SCB, lönestrukturstatistik 2025 (yrke enligt SSYK 2012: {code} {e(d["scb"])}). Belopp avrundade till hundratal.<br>
    Beräkningarna är ungefärliga. Använd <a href="/kalkylatorer/loneraknare">löneräknaren</a> för exakt nettolön i din kommun.</p>
  </footer>
</body>
</html>
'''
    out[slug]=fixmob(head+body)
os.makedirs(os.path.join(ROOT,'kalkylatorer','yrkeslon'),exist_ok=True)
for s,h in out.items(): open(os.path.join(ROOT,'kalkylatorer','yrkeslon',f'{s}.html'),'w',encoding='utf-8').write(h)
# hub
cats=list(bycat)
hub_rows=''.join(f'<h2 id="{re.sub("[^a-z]","",c.lower())}">{c}</h2><table class="table"><thead><tr><th>Yrke</th><th class="num">Medianlön</th><th class="num">Netto</th></tr></thead><tbody>'+''.join(f'<tr data-n="{e(n.lower())}"><td><a href="/kalkylatorer/yrkeslon/{s}">{cap(n)}</a></td><td class="num">{kr(D[c2]["s0"][0])}</td><td class="num">{kr(netto(D[c2]["s0"][0]))}</td></tr>' for c2,s,n,_ in sorted(bycat[c],key=lambda y:-D[y[0]]['s0'][0]))+'</tbody></table>' for c in cats)
HT='Lön per yrke 2026 – medianlön för 105 yrken enligt SCB'
HD='Vad tjänar olika yrken i Sverige? Medianlön och nettolön för 105 vanliga yrken enligt SCB:s lönestatistik 2025. Sök ditt yrke och jämför.'
hub=HEADTOP+f'''  <title>{e(HT)}</title>
  <meta name="description" content="{e(HD)}">
  <link rel="canonical" href="https://gratiskalkyl.se/kalkylatorer/yrkeslon/">
  <meta property="og:title" content="{e(HT)}">
  <meta property="og:description" content="{e(HD)}">
  <meta property="og:url" content="https://gratiskalkyl.se/kalkylatorer/yrkeslon/">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="sv_SE">
'''+STYLE.replace('</style>','    #q { width:100%; padding:12px 14px; border:1px solid var(--border); border-radius:10px; font-size:16px; background:var(--card); color:var(--text); margin:8px 0 8px; }\n    .table td a { color: var(--text); text-decoration:none; font-weight:600; }\n    .table td a:hover { color: var(--primary); }\n  </style>')+'</head>\n'+NAV+f'''  <main class="container">
    <nav class="breadcrumb"><a href="/">Hem</a> &rsaquo; <span>Lön per yrke</span></nav>
    <h1>Lön per yrke 2026</h1>
    <p class="lead">Medianlön och lön efter skatt för {len(Y)} vanliga yrken enligt <strong>SCB:s lönestrukturstatistik 2025</strong>. Klicka på ett yrke för lön efter ålder, sektor och kön.</p>
    <div class="cta" style="margin-bottom:16px;">
      <h3>Dags att löneförhandla?</h3>
      <p style="color:rgba(255,255,255,0.92);font-size:0.95rem;">Jämför din lön med 395 yrken och få ett konkret lönekrav.</p>
      <a href="/kalkylatorer/loneforhandling">Räkna ut ditt lönekrav &rarr;</a>
    </div>
    <input type="search" id="q" placeholder="Sök yrke, t.ex. sjuksköterska" oninput="f(this.value)" aria-label="Sök yrke">
    {hub_rows}
  </main>
  <footer><p>&copy; 2026 GratisKalkyl.se — Källa: SCB, lönestrukturstatistik 2025. Nettolön med genomsnittlig kommunalskatt 32,38 %.</p></footer>
  <script>function f(v){{v=v.toLowerCase().trim();document.querySelectorAll('tr[data-n]').forEach(function(r){{r.style.display=!v||r.dataset.n.indexOf(v)>-1?'':'none';}});document.querySelectorAll('main h2').forEach(function(h){{var t=h.nextElementSibling;var any=[].some.call(t.querySelectorAll('tr[data-n]'),function(r){{return r.style.display!=='none';}});h.style.display=t.style.display=any?'':'none';}});}}</script>
</body>
</html>
'''
open(os.path.join(ROOT,'kalkylatorer','yrkeslon','index.html'),'w',encoding='utf-8').write(fixmob(hub))
json.dump([[c,s,n,cat,D[c]['s0'][0]] for c,s,n,cat in Y],open(os.path.join(HERE,'yrken.json'),'w'),ensure_ascii=False)
print(len(out))
