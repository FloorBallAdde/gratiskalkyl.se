/* Unified search dropdown — works on /, /artiklar/, and (future) other pages.
   Reads window.SITE_SEARCH_INDEX (loaded via search-index.js).
   Attaches to any <input data-search-dropdown="auto"> or to #search / #article-search.
*/
(function(){
  'use strict';

  if (!window.SITE_SEARCH_INDEX || !Array.isArray(window.SITE_SEARCH_INDEX)) {
    console.warn('[search-dropdown] SITE_SEARCH_INDEX not loaded');
    return;
  }

  var INDEX = window.SITE_SEARCH_INDEX;

  // Find any search input on the page to enhance
  var inputs = Array.prototype.slice.call(
    document.querySelectorAll('input#search, input#article-search, input[data-search-dropdown]')
  );
  if (!inputs.length) return;

  function score(item, q) {
    var t = (item.title || '').toLowerCase();
    var kw = item.kw || '';
    if (t === q) return 1000;
    if (t.startsWith(q)) return 800;
    if (t.indexOf(q) !== -1) return 600;
    if (kw.indexOf(q) !== -1) return 400;
    // Match each word
    var words = q.split(/\s+/).filter(Boolean);
    var hits = 0;
    for (var i=0;i<words.length;i++){
      if (t.indexOf(words[i])!==-1 || kw.indexOf(words[i])!==-1) hits++;
    }
    return hits > 0 ? (200 * hits / words.length) : 0;
  }

  function search(query, limit) {
    var q = (query||'').trim().toLowerCase();
    if (!q) return [];
    var scored = [];
    for (var i=0;i<INDEX.length;i++){
      var s = score(INDEX[i], q);
      if (s > 0) scored.push({ item: INDEX[i], s: s });
    }
    scored.sort(function(a,b){
      if (b.s !== a.s) return b.s - a.s;
      // ties broken by type (kalkylator first) then title
      if (a.item.type !== b.item.type) return a.item.type === 'kalkylator' ? -1 : 1;
      return a.item.title.localeCompare(b.item.title, 'sv');
    });
    return scored.slice(0, limit || 8).map(function(x){ return x.item; });
  }

  function highlight(text, q) {
    if (!q) return text;
    var qLower = q.toLowerCase();
    var tLower = text.toLowerCase();
    var idx = tLower.indexOf(qLower);
    if (idx === -1) return text;
    return text.substring(0, idx) +
      '<mark>' + text.substring(idx, idx + q.length) + '</mark>' +
      text.substring(idx + q.length);
  }

  function buildDropdown() {
    var el = document.createElement('div');
    el.className = 'gk-search-dropdown';
    el.setAttribute('role', 'listbox');
    el.hidden = true;
    document.body.appendChild(el);
    return el;
  }

  function render(dropdown, results, query) {
    if (!results.length) {
      dropdown.innerHTML =
        '<div class="gk-sd-empty">Inga träffar för "' + escapeHtml(query) + '"</div>' +
        '<div class="gk-sd-footer">Prova andra ord eller <a href="/">bläddra alla sidor</a></div>';
      return;
    }
    var nCalc = 0, nGuide = 0;
    results.forEach(function(r){ if(r.type==='kalkylator') nCalc++; else nGuide++; });
    var html = '<div class="gk-sd-summary">' + results.length + ' träff' + (results.length===1?'':'ar');
    if (nCalc) html += ' · ' + nCalc + ' kalkylator' + (nCalc===1?'':'er');
    if (nGuide) html += ' · ' + nGuide + ' guide' + (nGuide===1?'':'r');
    html += '</div>';
    html += '<ul class="gk-sd-list">';
    results.forEach(function(item, i){
      var typeLabel = item.type === 'kalkylator' ? '🧮 Kalkylator' : '📖 Guide';
      var typeClass = item.type === 'kalkylator' ? 'is-calc' : 'is-guide';
      html += '<li role="option" data-index="' + i + '" class="gk-sd-item">' +
        '<a href="' + item.url + '" class="gk-sd-link">' +
          '<span class="gk-sd-icon">' + (item.icon || (item.type==='kalkylator'?'🧮':'📖')) + '</span>' +
          '<span class="gk-sd-text">' +
            '<span class="gk-sd-title">' + highlight(escapeHtml(item.title), query) + '</span>' +
            (item.desc ? '<span class="gk-sd-desc">' + highlight(escapeHtml(item.desc), query) + '</span>' : '') +
          '</span>' +
          '<span class="gk-sd-type ' + typeClass + '">' + typeLabel + '</span>' +
        '</a>' +
      '</li>';
    });
    html += '</ul>';
    dropdown.innerHTML = html;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  function positionDropdown(input, dropdown) {
    var rect = input.getBoundingClientRect();
    dropdown.style.position = 'fixed';
    dropdown.style.left = rect.left + 'px';
    dropdown.style.top = (rect.bottom + 6) + 'px';
    dropdown.style.width = rect.width + 'px';
  }

  function attach(input) {
    var dropdown = buildDropdown();
    var activeIndex = -1;
    var currentResults = [];

    function open(query) {
      currentResults = search(query, 8);
      render(dropdown, currentResults, query);
      positionDropdown(input, dropdown);
      dropdown.hidden = false;
      activeIndex = -1;
      document.body.classList.add('gk-searching');
    }

    function close() {
      dropdown.hidden = true;
      activeIndex = -1;
      // Only remove if no other dropdown is open
      var anyOpen = false;
      document.querySelectorAll('.gk-search-dropdown').forEach(function(d){
        if (!d.hidden) anyOpen = true;
      });
      if (!anyOpen) document.body.classList.remove('gk-searching');
    }

    function setActive(i) {
      var items = dropdown.querySelectorAll('.gk-sd-item');
      if (!items.length) return;
      if (i < 0) i = items.length - 1;
      if (i >= items.length) i = 0;
      activeIndex = i;
      for (var j=0;j<items.length;j++){
        items[j].classList.toggle('is-active', j===i);
      }
      // Scroll into view if needed
      items[i].scrollIntoView({ block: 'nearest' });
    }

    function activate() {
      if (activeIndex < 0 || activeIndex >= currentResults.length) {
        // Default: navigate to first result
        if (currentResults.length) location.href = currentResults[0].url;
        return;
      }
      location.href = currentResults[activeIndex].url;
    }

    input.addEventListener('input', function(){
      var q = input.value.trim();
      if (!q) { close(); return; }
      open(q);
    });

    input.addEventListener('focus', function(){
      if (input.value.trim()) open(input.value);
    });

    input.addEventListener('keydown', function(e){
      if (dropdown.hidden) return;
      if (e.key === 'ArrowDown') { e.preventDefault(); setActive(activeIndex+1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(activeIndex-1); }
      else if (e.key === 'Enter') { e.preventDefault(); activate(); }
      else if (e.key === 'Escape') { close(); }
    });

    // Click outside closes
    document.addEventListener('click', function(e){
      if (e.target === input) return;
      if (dropdown.contains(e.target)) return;
      close();
    });

    // Reposition on resize/scroll
    window.addEventListener('resize', function(){
      if (!dropdown.hidden) positionDropdown(input, dropdown);
    });
    window.addEventListener('scroll', function(){
      if (!dropdown.hidden) positionDropdown(input, dropdown);
    }, { passive: true });
  }

  inputs.forEach(attach);

})();
