/**
 * GratisKalkyl.se — Dark mode toggle (standalone)
 * Används av äldre kalkylator-sidor som har egen nav (inte nav.js).
 * Lägg till i varje sida direkt efter <body>:
 *   <script src="/theme.js"></script>
 *
 * Delar localStorage-nyckel "gk-theme" med nav.js och index.html
 * så att temavalet är konsekvent över hela sajten.
 */
(function(){
  'use strict';

  /* ── 1. Tillämpa tema ASAP (förhindrar FOUC) ──────────────────────── */
  var saved=null;
  try{saved=localStorage.getItem('gk-theme');}catch(e){}
  var prefersDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)').matches;
  var isDark=(saved==='dark')||(saved===null&&prefersDark);
  if(isDark)document.documentElement.setAttribute('data-theme','dark');

  /* ── 2. CSS-variabler för [data-theme="dark"] ─────────────────────── */
  var s=document.createElement('style');
  s.textContent=
    'html[data-theme="dark"]{'
      +'color-scheme:dark;'
      +'--primary:#34d399!important;--primary-light:rgba(26,107,74,.2)!important;'
      +'--primary-dark:#059669!important;--accent:#60a5fa!important;'
      +'--text:#f3f4f6!important;--text-light:#d1d5db!important;'
      +'--bg:#111827!important;--white:#1f2937!important;'
      +'--border:#374151!important;--shadow:0 2px 8px rgba(0,0,0,.35)!important;'
      +'--muted:#9ca3af!important;'
    +'}'
    +'html[data-theme="dark"] body{background:#111827!important;color:#f3f4f6!important;}'
    /* Nav-specifik dark mode */
    +'html[data-theme="dark"] .site-nav{'
      +'background:#1f2937!important;border-bottom-color:#374151!important;'
    +'}'
    +'html[data-theme="dark"] .nav-logo{color:#34d399!important;}'
    +'html[data-theme="dark"] .nav-logo span{color:#6b7280!important;}'
    +'html[data-theme="dark"] .nav-back{color:#9ca3af!important;}'
    +'html[data-theme="dark"] .nav-back:hover{color:#34d399!important;}'
    +'html[data-theme="dark"] canvas{filter:brightness(.92);}'
    /* Toggle-knapp */
    +'.gk-theme-btn{'
      +'display:flex;align-items:center;justify-content:center;'
      +'width:32px;height:32px;border-radius:8px;border:1.5px solid #e5e7eb;'
      +'background:#fff;cursor:pointer;color:#6b7280;'
      +'transition:border-color .12s,color .12s,background .15s;'
      +'padding:0;flex-shrink:0;margin-left:auto;'
    +'}'
    +'.gk-theme-btn:hover{border-color:#16a34a;color:#16a34a;}'
    +'html[data-theme="dark"] .gk-theme-btn{'
      +'background:#1f2937!important;border-color:#374151!important;color:#fbbf24!important;'
    +'}'
    +'html[data-theme="dark"] .gk-theme-btn:hover{border-color:#34d399!important;color:#34d399!important;}';
  document.head.appendChild(s);

  /* ── 3. SVG-ikoner ────────────────────────────────────────────────── */
  var MOON='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  var SUN='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';

  /* ── 4. Infoga knapp i .site-nav ──────────────────────────────────── */
  function inject(){
    var nav=document.querySelector('.site-nav');
    if(!nav)return;
    var btn=document.createElement('button');
    btn.className='gk-theme-btn';
    btn.type='button';
    var dark=document.documentElement.getAttribute('data-theme')==='dark';
    btn.innerHTML=dark?SUN:MOON;
    btn.setAttribute('aria-label',dark?'Aktivera ljust läge':'Aktivera mörkt läge');
    nav.appendChild(btn);

    btn.addEventListener('click',function(){
      var nowDark=document.documentElement.getAttribute('data-theme')==='dark';
      var next=!nowDark;
      if(next){document.documentElement.setAttribute('data-theme','dark');}
      else{document.documentElement.removeAttribute('data-theme');}
      try{localStorage.setItem('gk-theme',next?'dark':'light');}catch(e){}
      btn.innerHTML=next?SUN:MOON;
      btn.setAttribute('aria-label',next?'Aktivera ljust läge':'Aktivera mörkt läge');
    });

    /* Lyssna på OS-temabyte */
    if(window.matchMedia){
      window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',function(e){
        var m=null;try{m=localStorage.getItem('gk-theme');}catch(ex){}
        if(m)return;
        if(e.matches){document.documentElement.setAttribute('data-theme','dark');btn.innerHTML=SUN;btn.setAttribute('aria-label','Aktivera ljust läge');}
        else{document.documentElement.removeAttribute('data-theme');btn.innerHTML=MOON;btn.setAttribute('aria-label','Aktivera mörkt läge');}
      });
    }
  }

  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',inject);}
  else{inject();}
})();
