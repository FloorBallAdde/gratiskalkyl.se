/**
 * GratisKalkyl.se — Delad navigeringskomponent + Dark mode toggle
 * Lägg till i varje kalkylator, direkt efter <body>:
 *
 *   <script src="/nav.js"></script>
 *
 * Valfritt — sätt aktiv kategori:
 *   <script>window.GK_CAT='pk';</script>
 *   <script src="/nav.js"></script>
 *
 * Kategorikoder: pk | sp | bo | fo | jo | ha
 *
 * Dark mode: Hanteras automatiskt via prefers-color-scheme.
 * Användaren kan växla ljust/mörkt tema med knappen i navbaren.
 * Preferens sparas i localStorage under nyckeln "gk-theme".
 */
(function(){
  'use strict';

  /* ── 1. Tillämpa tema ASAP (förhindra FOUC) ─────────────────────────── */
  var savedTheme=null;
  try{savedTheme=localStorage.getItem('gk-theme');}catch(e){}
  var prefersDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)').matches;
  var isDark=(savedTheme==='dark')||(savedTheme===null&&prefersDark);
  if(isDark)document.documentElement.setAttribute('data-theme','dark');

  /* ── 2. Injicera CSS-variabler för [data-theme="dark"] ─────────────────
     Säkrar att toggle fungerar även om sidan inte har egna dark-media-queries.
     Sidor med @media(prefers-color-scheme:dark) och samma CSS-variabler
     fungerar parallellt — data-theme-reglerna har högre specificitet.
  ─────────────────────────────────────────────────────────────────────── */
  var themeCss=
    'html[data-theme="dark"]{'
      +'color-scheme:dark;'
      +'--text:#f3f4f6!important;'
      +'--text-light:#d1d5db!important;'
      +'--bg:#111827!important;'
      +'--white:#1f2937!important;'
      +'--border:#374151!important;'
      +'--primary:#34d399!important;'
      +'--primary-light:rgba(26,107,74,0.2)!important;'
      +'--primary-dark:#059669!important;'
      +'--accent:#60a5fa!important;'
      +'--shadow:0 2px 8px rgba(0,0,0,0.35)!important;'
    +'}'
    +'html[data-theme="dark"] body{'
      +'background:#111827!important;'
      +'color:#f3f4f6!important;'
    +'}'
    +'html[data-theme="dark"] canvas{'
      +'filter:brightness(.92);'
    +'}';

  var themeStyle=document.createElement('style');
  themeStyle.id='gk-theme-style';
  themeStyle.textContent=themeCss;
  document.head.appendChild(themeStyle);

  /* ── 3. Navigationskonfiguration ───────────────────────────────────── */
  var CATS=[
    {id:'pk',label:'💰 Privatekonomi',href:'/?filter=pk'},
    {id:'sp',label:'💹 Sparande',href:'/?filter=sp'},
    {id:'bo',label:'🏠 Boende & Lån',href:'/?filter=bo'},
    {id:'fo',label:'🚗 Fordon',href:'/?filter=fo'},
    {id:'jo',label:'👪 Jobb & Familj',href:'/?filter=jo'},
    {id:'ha',label:'💪 Hälsa',href:'/?filter=ha'}
  ];
  var activeCat=window.GK_CAT||null;

  /* ── 4. Navstil inkl. dark-mode-stöd ───────────────────────────────── */
  var css=
    '.gk-nav{'
      +'position:sticky;top:0;z-index:999;'
      +'background:#fff;border-bottom:1px solid #e5e7eb;'
      +'box-shadow:0 1px 4px rgba(0,0,0,.07);'
      +'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;'
      +'transition:background .2s,border-color .2s;'
    +'}'
    +'html[data-theme="dark"] .gk-nav{'
      +'background:#1f2937!important;border-bottom-color:#374151!important;'
      +'box-shadow:0 1px 4px rgba(0,0,0,.3)!important;'
    +'}'
    +'.gk-nav-inner{max-width:1120px;margin:0 auto;padding:0 1rem;height:56px;display:flex;align-items:center;gap:.75rem;}'
    +'.gk-logo{text-decoration:none;font-size:1.05rem;font-weight:800;color:#16a34a;letter-spacing:-.01em;white-space:nowrap;flex-shrink:0;}'
    +'html[data-theme="dark"] .gk-logo{color:#34d399!important;}'
    +'.gk-logo span{color:#9ca3af;font-weight:400;}'
    +'html[data-theme="dark"] .gk-logo span{color:#6b7280!important;}'
    +'.gk-links{display:flex;gap:.2rem;overflow-x:auto;flex:1;scrollbar-width:none;-ms-overflow-style:none;}'
    +'.gk-links::-webkit-scrollbar{display:none;}'
    +'.gk-links a{white-space:nowrap;padding:.3rem .65rem;border-radius:99px;text-decoration:none;font-size:.78rem;font-weight:600;color:#6b7280;transition:background .12s,color .12s;flex-shrink:0;}'
    +'.gk-links a:hover{background:#f3f4f6;color:#111827;}'
    +'html[data-theme="dark"] .gk-links a{color:#9ca3af!important;}'
    +'html[data-theme="dark"] .gk-links a:hover{background:#374151!important;color:#f3f4f6!important;}'
    +'.gk-links a.gk-active{background:#dcfce7;color:#15803d;}'
    +'html[data-theme="dark"] .gk-links a.gk-active{background:rgba(52,211,153,.15)!important;color:#34d399!important;}'
    +'.gk-all{flex-shrink:0;display:flex;align-items:center;gap:.35rem;padding:.35rem .75rem;border:1.5px solid #e5e7eb;border-radius:8px;text-decoration:none;font-size:.78rem;font-weight:600;color:#6b7280;background:#fff;transition:border-color .12s,color .12s;white-space:nowrap;}'
    +'.gk-all:hover{border-color:#16a34a;color:#16a34a;}'
    +'html[data-theme="dark"] .gk-all{background:#1f2937!important;border-color:#374151!important;color:#9ca3af!important;}'
    +'html[data-theme="dark"] .gk-all:hover{border-color:#34d399!important;color:#34d399!important;}'
    /* Toggle-knapp */
    +'.gk-theme-btn{'
      +'flex-shrink:0;display:flex;align-items:center;justify-content:center;'
      +'width:36px;height:36px;border-radius:8px;border:1.5px solid #e5e7eb;'
      +'background:#fff;cursor:pointer;color:#6b7280;'
      +'transition:border-color .12s,color .12s,background .15s;'
      +'padding:0;'
    +'}'
    +'.gk-theme-btn:hover{border-color:#16a34a;color:#16a34a;}'
    +'html[data-theme="dark"] .gk-theme-btn{'
      +'background:#1f2937!important;border-color:#374151!important;color:#fbbf24!important;'
    +'}'
    +'html[data-theme="dark"] .gk-theme-btn:hover{border-color:#34d399!important;color:#34d399!important;}'
    +'@media(max-width:640px){.gk-links{display:none;}}';

  var style=document.createElement('style');style.textContent=css;document.head.appendChild(style);

  /* ── 5. SVG-ikoner ──────────────────────────────────────────────────── */
  var MOON_SVG='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  var SUN_SVG='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';

  function toggleLabel(dark){return dark?'Aktivera ljust läge':'Aktivera mörkt läge';}
  function toggleIcon(dark){return dark?SUN_SVG:MOON_SVG;}

  /* ── 6. Bygg navbaren ───────────────────────────────────────────────── */
  var links=CATS.map(function(c){
    return '<a href="'+c.href+'"'+(activeCat===c.id?' class="gk-active"':'')+'>'+c.label+'</a>';
  }).join('');

  var currentDark=isDark;
  var nav=document.createElement('header');
  nav.className='gk-nav';
  nav.setAttribute('role','banner');
  nav.innerHTML=
    '<div class="gk-nav-inner">'
      +'<a href="/" class="gk-logo" aria-label="Till startsidan">GratisKalkyl<span>.se</span></a>'
      +'<nav class="gk-links" aria-label="Kategorier">'+links+'</nav>'
      +'<a href="/" class="gk-all" aria-label="Alla kalkylatorer">'
        +'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
        +' Alla kalkylatorer</a>'
      +'<button class="gk-theme-btn" id="gk-theme-btn" type="button" aria-label="'+toggleLabel(currentDark)+'">'
        +toggleIcon(currentDark)
      +'</button>'
    +'</div>';

  /* ── 7. Infoga nav & koppla toggle-logik ───────────────────────────── */
  function insert(){
    document.body.insertBefore(nav,document.body.firstChild);
    var btn=document.getElementById('gk-theme-btn');
    if(!btn)return;
    btn.addEventListener('click',function(){
      var nowDark=document.documentElement.getAttribute('data-theme')==='dark';
      var next=!nowDark;
      if(next){
        document.documentElement.setAttribute('data-theme','dark');
      }else{
        document.documentElement.removeAttribute('data-theme');
      }
      try{localStorage.setItem('gk-theme',next?'dark':'light');}catch(e){}
      btn.setAttribute('aria-label',toggleLabel(next));
      btn.innerHTML=toggleIcon(next);
    });
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',insert);
  }else{
    insert();
  }

  /* ── 8. Lyssna på OS-temabyte (respekterar manuellt val) ───────────── */
  if(window.matchMedia){
    window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',function(e){
      var manual=null;
      try{manual=localStorage.getItem('gk-theme');}catch(ex){}
      if(manual)return;
      var btn=document.getElementById('gk-theme-btn');
      if(e.matches){
        document.documentElement.setAttribute('data-theme','dark');
        if(btn){btn.setAttribute('aria-label',toggleLabel(true));btn.innerHTML=toggleIcon(true);}
      }else{
        document.documentElement.removeAttribute('data-theme');
        if(btn){btn.setAttribute('aria-label',toggleLabel(false));btn.innerHTML=toggleIcon(false);}
      }
    });
  }

})();
