/* ==========================================================================
   select.js — infinite game-style coverflow.

   Infinite looping without cloning any DOM. For each card we compute its
   SIGNED SHORTEST distance to the active index, wrapped around the ring:

       d = ((i - current + n/2 + n) % n) - n/2          (n even)

   so with 7 cards, card 0 sits at d = -1 when current is 1, and at d = +3
   when current is 4 — it takes the short way round either way. Cards are then
   placed purely by transform from that d. Nothing is reordered, nothing is
   duplicated, and there is no seam to jump at because there is no seam.

   Backgrounds use the same opacity-only crossfade as the home splash.
   ========================================================================== */

(function () {
  'use strict';

  var root = document.querySelector('[data-select]');
  if (!root) return;

  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-card]'));
  var bgs = Array.prototype.slice.call(root.querySelectorAll('[data-bg]'));
  var pips = Array.prototype.slice.call(root.querySelectorAll('[data-pip]'));
  var curEl = root.querySelector('[data-cur]');
  var n = cards.length;
  if (!n) return;

  var current = 0;
  var busy = false;

  function reduced() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* signed shortest distance around the ring */
  function dist(i) {
    var half = n / 2;
    return ((((i - current) % n) + n + Math.floor(half)) % n) - Math.floor(half);
  }

  function render() {
    cards.forEach(function (card, i) {
      var d = dist(i);
      var ad = Math.abs(d);
      var active = d === 0;

      // only the nearest few are worth painting
      var visible = ad <= 3;
      card.style.setProperty('--d', d);
      card.style.setProperty('--ad', ad);
      card.style.setProperty('--s', active ? 1 : Math.max(0.66, 1 - ad * 0.13));
      card.style.setProperty('--o', visible ? (active ? 1 : Math.max(0, 0.62 - (ad - 1) * 0.22)) : 0);
      card.style.setProperty('--z', String(20 - ad));
      card.classList.toggle('is-active', active);
      card.setAttribute('aria-hidden', active ? 'false' : 'true');
      card.tabIndex = active ? 0 : -1;
      // keep offscreen cards out of hit-testing
      card.style.pointerEvents = visible ? 'auto' : 'none';
    });

    bgs.forEach(function (b, i) { b.classList.toggle('is-on', i === current); });
    pips.forEach(function (p, i) {
      p.setAttribute('aria-selected', i === current ? 'true' : 'false');
    });
    if (curEl) curEl.textContent = String(current + 1).padStart(2, '0');
  }

  function go(delta) {
    current = ((current + delta) % n + n) % n;
    render();
  }

  function goTo(i) {
    current = ((i % n) + n) % n;
    render();
  }

  function touched() { root.classList.add('is-touched'); }

  /* ---- wheel / trackpad: accumulate then step, with a cooldown ---- */
  var acc = 0;
  var cooling = false;
  root.addEventListener(
    'wheel',
    function (e) {
      e.preventDefault();
      touched();
      if (cooling) return;

      // trackpads fire many small deltas; mice fire few large ones
      acc += Math.abs(e.deltaY) > Math.abs(e.deltaX) ? e.deltaY : e.deltaX;

      if (Math.abs(acc) > 42) {
        go(acc > 0 ? 1 : -1);
        acc = 0;
        cooling = true;
        setTimeout(function () { cooling = false; }, reduced() ? 40 : 340);
      }
    },
    { passive: false }
  );

  /* ---- drag / swipe ---- */
  var startX = null;
  var moved = false;

  root.addEventListener('pointerdown', function (e) {
    if (e.target.closest('a,button')) return;
    startX = e.clientX;
    moved = false;
  });

  root.addEventListener('pointermove', function (e) {
    if (startX === null) return;
    var dx = e.clientX - startX;
    if (Math.abs(dx) > 60) {
      touched();
      go(dx < 0 ? 1 : -1);
      startX = e.clientX;
      moved = true;
    }
  });

  var endDrag = function () { startX = null; };
  root.addEventListener('pointerup', endDrag);
  root.addEventListener('pointercancel', endDrag);
  root.addEventListener('pointerleave', endDrag);

  /* ---- click a side card to bring it forward ---- */
  cards.forEach(function (card, i) {
    card.addEventListener('click', function (e) {
      if (moved) { e.preventDefault(); return; }
      if (dist(i) !== 0) {
        e.preventDefault();
        touched();
        goTo(i);
      }
      // the active card's CTA is a real link — let it through
    });
  });

  /* ---- arrows + pips ---- */
  var prev = root.querySelector('[data-prev]');
  var next = root.querySelector('[data-next]');
  if (prev) prev.addEventListener('click', function () { touched(); go(-1); });
  if (next) next.addEventListener('click', function () { touched(); go(1); });

  pips.forEach(function (p, i) {
    p.addEventListener('click', function () { touched(); goTo(i); });
  });

  /* ---- keyboard ---- */
  window.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight') { touched(); go(1); e.preventDefault(); }
    else if (e.key === 'ArrowLeft') { touched(); go(-1); e.preventDefault(); }
    else if (e.key === 'Home') { touched(); goTo(0); e.preventDefault(); }
    else if (e.key === 'End') { touched(); goTo(n - 1); e.preventDefault(); }
  });

  render();
})();
