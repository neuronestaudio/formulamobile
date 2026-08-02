/* ==========================================================================
   splash.js — the Tesla `dx-splash` mechanic, rebuilt.

   Identified from https://www.tesla.com/en_au/model3-choose (2 Aug 2026):

     .dx-splash            static, ~20px taller than the viewport
     .dx-splash__wrapper   position: sticky; top: 0  — pins the stage
     .dx-splash__slide-N   position: fixed, stacked at identical coordinates,
                           transition: opacity 0.5s ease-in-out
     .dx-splash__active-slide-N  ONE state class on the wrapper drives everything

   The key insight: it is NOT a scroll-scrubbed animation. The scroll runway is
   a discrete TRIGGER — crossing a threshold flips a state class and CSS runs a
   fixed 500ms crossfade. Because the art is pre-registered (Tesla ships both
   renders at 2880x1800 with the car in the same pixel position) and *only*
   opacity animates, the car appears to swap in place rather than move.

   This version generalises to N slides and drives the same state machine from
   three inputs: scroll position, the switch button, and the pips.
   ========================================================================== */

(function () {
  'use strict';

  var splash = document.querySelector('[data-splash]');
  if (!splash) return;

  var slides = Array.prototype.slice.call(splash.querySelectorAll('.splash__slide'));
  var pips = Array.prototype.slice.call(splash.querySelectorAll('.splash__pip'));
  var count = slides.length;
  if (count < 2) return;

  var current = 1;
  var lockUntil = 0;

  function apply(n, viaScroll) {
    n = Math.min(Math.max(n, 1), count);
    if (n === current) return;
    current = n;
    splash.setAttribute('data-active', String(n));
    pips.forEach(function (p, i) {
      p.setAttribute('aria-selected', i + 1 === n ? 'true' : 'false');
    });
    slides.forEach(function (s, i) {
      // keep the inactive slides out of the a11y tree and tab order
      s.setAttribute('aria-hidden', i + 1 === n ? 'false' : 'true');
    });
    // a manual pick shouldn't immediately get overridden by the scroll handler
    if (!viaScroll) lockUntil = Date.now() + 700;
  }

  /* ---- scroll: map runway progress onto discrete slide indices ---- */
  function fromScroll() {
    if (Date.now() < lockUntil) return;

    var rect = splash.getBoundingClientRect();
    var runway = splash.offsetHeight - window.innerHeight;
    if (runway <= 0) return;

    // 0 at the top of the runway, 1 at the bottom
    var p = Math.min(Math.max(-rect.top / runway, 0), 1);

    // Discrete bands, not a scrub. Slight bias so slide 1 holds a moment
    // before the first swap, matching how Tesla's short runway feels.
    var n = Math.floor(p * count) + 1;
    apply(Math.min(n, count), true);
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      fromScroll();
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });

  /* ---- switch button: same state machine, wraps around ---- */
  splash.addEventListener('click', function (e) {
    var sw = e.target.closest('[data-splash-switch]');
    if (sw) {
      var next = current >= count ? 1 : current + 1;
      apply(next, false);
      // move the page to the matching band so scroll state agrees with the pick
      var runway = splash.offsetHeight - window.innerHeight;
      var target = splash.offsetTop + (runway * (next - 1)) / count + 8;
      window.scrollTo({ top: target, behavior: prefersReduced() ? 'auto' : 'smooth' });
      return;
    }

    var pip = e.target.closest('[data-splash-pip]');
    if (pip) {
      var idx = parseInt(pip.getAttribute('data-splash-pip'), 10);
      apply(idx, false);
      var rw = splash.offsetHeight - window.innerHeight;
      window.scrollTo({
        top: splash.offsetTop + (rw * (idx - 1)) / count + 8,
        behavior: prefersReduced() ? 'auto' : 'smooth',
      });
    }
  });

  function prefersReduced() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* ---- keyboard: arrow keys while the stage is on screen ---- */
  splash.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      apply(current + 1, false);
      e.preventDefault();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      apply(current - 1, false);
      e.preventDefault();
    }
  });

  /* ---- decode the other slides up front so the crossfade never flashes ---- */
  slides.forEach(function (s) {
    var img = s.querySelector('img');
    if (img && !img.complete) img.decoding = 'async';
  });

  splash.setAttribute('data-active', '1');
  slides.forEach(function (s, i) {
    s.setAttribute('aria-hidden', i === 0 ? 'false' : 'true');
  });
  fromScroll();
})();
