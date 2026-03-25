/**
 * GratisKalkyl.se — Delad navigeringskomponent
 * Lägg till i varje kalkylator, direkt efter <body>:
 *
 *   <script src="/nav.js"></script>
 *
 * Valfritt — sätt aktiv kategori:
 *   <script>window.GK_CAT='pk';</script>
 *   <script src="/nav.js"></script>
 *
 * Kategorikoder: pk | sp | bo | fo | jo | ha
 */
(function(){
  'use strict';
  var CATS=[
    {id:'pk',label:'💰 Privatekonomi',href:'/?filter=pk'},
    {id:'sp',label:'💹 Sparande',href:'/?filter=sp'},
    {id:'bo',label:'🏠 Boende & Lån',href:'/?filter=bo'},
    {id:'fo',label:'🚗 Fordon',href:'/?filter=fo'},
    {id:'jo',label:'👪 Jobb & Familj',href:'/?filter=jo'},
    {id:'ha',label:'💪 Hälsa',href:'/?filter=ha'}
  ];
  var activeCat=window.GK_CAT||null;
  var css='.gk-nav{position:sticky;top:0;z-index:999;background:#fff;border-bottom:1px solid #e5e7eb;box-shadow:0 1px 4px rgba(0,0,0,.07);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}'
    +'.gk-nav-inner{max-width:1120px;margin:0 auto;padding:0 1rem;height:56px;display:flex;align-items:center;gap:.75rem;}'
    +'.gk-logo{text-decoration:none;font-size:1.05rem;font-weight:800;color:#16a34a;letter-spacing:-.01em;white-space:nowrap;flex-shrink:0;}'
    +'.gk-logo span{color:#9ca3af;font-weight:400;}'
    +'.gk-links{display:flex;gap:.2rem;overflow-x:auto;flex:1;scrollbar-width:none;-ms-overflow-style:none;}'
    +'.gk-links::-webkit-scrollbar{display:none;}'
    +'.gk-links a{white-space:nowrap;padding:.3rem .65rem;border-radius:99px;text-decoration:none;font-size:.78rem;font-weight:600;color:#6b7280;transition:background .12s,color .12s;flex-shrink:0;}'
    +'.gk-links a:hover{background:#f3f4f6;color:#111827;}'
    +'.gk-links a.gk-active{background:#dcfce7;color:#15803d;}'
    +'.gk-all{flex-shrink:0;display:flex;align-items:center;gap:.35rem;padding:.35rem .75rem;border:1.5px solid #e5e7eb;border-radius:8px;text-decoration:none;font-size:.78rem;font-weight:600;color:#6b7280;background:#fff;transition:border-color .12s,color .12s;white-space:nowrap;}'
    +'.gk-all:hover{border-color:#16a34a;color:#16a34a;}'
    +'@media(max-width:640px){.gk-links{display:none;}}';
  var style=document.createElement('style');style.textContent=css;document.head.appendChild(style);
  var links=CATS.map(function(c){return '<a href="'+c.href+'"'+(activeCat===c.id?' class="gk-active"':'')+'>'+c.label+'</a>';}).join('');
  var nav=document.createElement('header');
  nav.className='gk-nav';
  nav.setAttribute('role','banner');
  nav.innerHTML='<div class="gk-nav-inner">'
    +'<a href="/" class="gk-logo" aria-label="Till startsidan">GratisKalkyl<span>.se</span></a>'
    +'<nav class="gk-links" aria-label="Kategorier">'+links+'</nav>'
    +'<a href="/" class="gk-all" aria-label="Alla kalkylatorer">'
    +'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
    +' Alla kalkylatorer</a>'
    +'</div>';
  function insert(){document.body.insertBefore(nav,document.body.firstChild);}
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',insert);}else{insert();}
})();
