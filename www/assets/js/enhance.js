/* ==========================================================================
   enhance.js — premium interaction layer
   Mirrors the role of Premier Mobile Detailing's assets/enhance.js: nav state,
   mobile drawer, scroll reveal, cursor-tracking card spotlights, stat count-up.
   Progressive enhancement only — every page works with JS disabled.
   ========================================================================== */

(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- sticky nav state ---- */
  var nav = document.querySelector('.nav');
  if (nav) {
    var setStuck = function () {
      nav.classList.toggle('is-stuck', window.scrollY > 24);
    };
    setStuck();
    window.addEventListener('scroll', setStuck, { passive: true });
  }

  /* ---- mobile drawer ---- */
  var drawer = document.querySelector('[data-drawer]');
  var burger = document.querySelector('[data-drawer-open]');
  if (drawer && burger) {
    var toggle = function (open) {
      drawer.setAttribute('data-open', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) {
        var first = drawer.querySelector('a');
        if (first) first.focus();
      } else {
        burger.focus();
      }
    };
    burger.addEventListener('click', function () { toggle(true); });
    drawer.addEventListener('click', function (e) {
      if (e.target.closest('[data-drawer-close]') || e.target.tagName === 'A') toggle(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.getAttribute('data-open') === 'true') toggle(false);
    });
  }

  /* ---- scroll reveal ---- */
  var reveals = document.querySelectorAll('[data-reveal]');
  if (reveals.length) {
    if (reduced || !('IntersectionObserver' in window)) {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (en) {
            if (!en.isIntersecting) return;
            var delay = parseFloat(en.target.getAttribute('data-reveal')) || 0;
            setTimeout(function () { en.target.classList.add('is-in'); }, delay * 1000);
            io.unobserve(en.target);
          });
        },
        { rootMargin: '0px 0px -12% 0px', threshold: 0.08 }
      );
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---- cursor-tracking card spotlight ---- */
  if (!reduced && window.matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('.card').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--mx', ((e.clientX - r.left) / r.width) * 100 + '%');
        card.style.setProperty('--my', ((e.clientY - r.top) / r.height) * 100 + '%');
      });
    });
  }

  /* ---- stat count-up ---- */
  var stats = document.querySelectorAll('[data-count]');
  if (stats.length && 'IntersectionObserver' in window) {
    var so = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var el = en.target;
          var target = parseFloat(el.getAttribute('data-count'));
          var suffix = el.getAttribute('data-suffix') || '';
          so.unobserve(el);

          if (reduced) { el.textContent = target + suffix; return; }

          var dur = 1400;
          var t0 = performance.now();
          (function step(now) {
            var p = Math.min((now - t0) / dur, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased) + suffix;
            if (p < 1) requestAnimationFrame(step);
          })(t0);
        });
      },
      { threshold: 0.5 }
    );
    stats.forEach(function (el) { so.observe(el); });
  }

  /* ---- lightweight gallery lightbox ---- */
  var tiles = document.querySelectorAll('[data-lightbox]');
  if (tiles.length) {
    var box = document.createElement('div');
    box.className = 'lb';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML =
      '<button class="lb__x" aria-label="Close">&times;</button><img alt="">';
    document.body.appendChild(box);
    var lbImg = box.querySelector('img');

    var close = function () {
      box.removeAttribute('data-open');
      document.body.style.overflow = '';
    };
    tiles.forEach(function (t) {
      t.addEventListener('click', function () {
        var img = t.querySelector('img');
        if (!img) return;
        lbImg.src = img.currentSrc || img.src;
        lbImg.alt = img.alt || '';
        box.setAttribute('data-open', 'true');
        document.body.style.overflow = 'hidden';
      });
    });
    box.addEventListener('click', function (e) {
      if (e.target === box || e.target.closest('.lb__x')) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }

  /* ---- current-year stamp (never goes stale like the 2021 footer did) ---- */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
