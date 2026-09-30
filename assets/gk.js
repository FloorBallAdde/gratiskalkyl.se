/* GratisKalkyl v2 – delad kod för meny, tema, talformat och Min ekonomi. */
(function () {
  'use strict';
  var GK = window.GK = window.GK || {};

  /* Talformat: "35 000", "81,0" */
  GK.fmt = function (n, dec) {
    if (n == null || !isFinite(n)) return '–';
    dec = dec || 0;
    return Number(n).toLocaleString('sv-SE', { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace(/−/g, '-');
  };
  GK.parse = function (s) {
    if (typeof s === 'number') return s;
    if (!s) return NaN;
    var t = String(s).replace(/\s| /g, '').replace(',', '.').replace(/[^0-9.\-]/g, '');
    return t === '' ? NaN : parseFloat(t);
  };
  /* Mellanslag som tusentalsavgränsare medan man skriver (heltal) */
  GK.groupInput = function (input) {
    input.addEventListener('blur', function () {
      var v = GK.parse(input.value);
      if (isFinite(v) && Math.abs(v) >= 1000 && Math.round(v) === v) input.value = GK.fmt(v);
    });
  };

  /* Min ekonomi – sparas bara i webbläsaren */
  var KEY = 'gk-min-ekonomi';
  GK.ekonomi = {
    all: function () {
      try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { return {}; }
    },
    get: function (k) { return this.all()[k] || null; },
    set: function (k, v) {
      try {
        var a = this.all(); v.sparad = new Date().toISOString().slice(0, 10); a[k] = v;
        localStorage.setItem(KEY, JSON.stringify(a)); return true;
      } catch (e) { return false; }
    },
    remove: function (k) {
      try { var a = this.all(); delete a[k]; localStorage.setItem(KEY, JSON.stringify(a)); return true; } catch (e) { return false; }
    }
  };

  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }

  ready(function () {
    var menu = document.getElementById('gk-menu');
    var btns = document.querySelectorAll('[data-gk-menu]');
    function setOpen(open, focusSearch) {
      if (!menu) return;
      menu.hidden = !open;
      document.body.classList.toggle('gk-menu-open', open);
      btns.forEach(function (b) { b.setAttribute('aria-expanded', open ? 'true' : 'false'); });
      var closeIcon = document.querySelectorAll('.gk-ico-close'), openIcon = document.querySelectorAll('.gk-ico-open');
      closeIcon.forEach(function (i) { i.style.display = open ? '' : 'none'; });
      openIcon.forEach(function (i) { i.style.display = open ? 'none' : ''; });
      if (open && focusSearch) { var s = menu.querySelector('input[type="search"]'); if (s) setTimeout(function () { s.focus(); }, 30); }
    }
    btns.forEach(function (b) {
      b.addEventListener('click', function () { setOpen(menu.hidden, b.getAttribute('data-gk-menu') === 'search'); });
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu && !menu.hidden) setOpen(false); });
    document.addEventListener('click', function (e) {
      if (!menu || menu.hidden) return;
      if (menu.contains(e.target) || e.target.closest('[data-gk-menu]') || e.target.closest('.gk-search-dropdown')) return;
      if (window.innerWidth >= 900) setOpen(false);
    });

    document.querySelectorAll('.gk-mg-btn').forEach(function (b) {
      b.addEventListener('click', function () {
        var g = b.closest('.gk-mg'); var open = !g.classList.contains('is-open');
        g.classList.toggle('is-open', open); b.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });

    /* Min ekonomi-räknare i menyn */
    var mc = document.getElementById('gk-menu-min-count');
    if (mc) { var n = Object.keys(GK.ekonomi.all()).length; mc.textContent = n ? (n + (n === 1 ? ' sparad siffra' : ' sparade siffror')) : 'Spara dina siffror och följ dem'; }

    /* Tema */
    var tb = document.getElementById('gk-theme-btn');
    function label() { if (tb) tb.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? 'Byt till ljust läge' : 'Byt till mörkt läge'; }
    label();
    if (tb) tb.addEventListener('click', function () {
      var dark = document.documentElement.getAttribute('data-theme') !== 'dark';
      document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
      try { localStorage.setItem('gk-theme', dark ? 'dark' : 'light'); } catch (e) {}
      label();
    });
  });
})();
