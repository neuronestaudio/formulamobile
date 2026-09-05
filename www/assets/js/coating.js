/**
 * Ceramic coating section — stage copy over a looping process film.
 *
 * The background is a stitched, desaturated cut of the coating process, held
 * at 50% so it reads as texture rather than as content. Every shot is a tight
 * crop: no plates, badges or silhouettes, so no vehicle or operator is
 * identifiable.
 *
 * The video is NOT loaded until the section approaches, and never on
 * reduced-motion or Save-Data — the poster frame carries it in those cases and
 * says the same thing. This replaced a 5 MB GLB and a three.js runtime; the
 * whole section is now one 5 MB mp4 and ~2 KB of script.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-coating]');
  if (!root) return;

  var vids = Array.prototype.slice.call(root.querySelectorAll('[data-stage-vid]'));
  var panels = Array.prototype.slice.call(root.querySelectorAll('[data-stage]'));
  if (!panels.length) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var saveData = navigator.connection && navigator.connection.saveData;

  /* ---- stage copy: runs with or without the film ---- */
  var current = -1;
  function setStage(i) {
    if (i === current) return;
    current = i;
    panels.forEach(function (p, k) { p.classList.toggle('is-on', k === i); });
    root.querySelectorAll('[data-stage-pip]').forEach(function (d, k) {
      d.setAttribute('aria-selected', k === i ? 'true' : 'false');
    });
    // crossfade the films, and only ever decode the one on screen
    vids.forEach(function (v, k) {
      var on = k === i;
      v.classList.toggle('is-on', on);
      if (!v.src) return;
      if (on) { var pr = v.play(); if (pr && pr.catch) pr.catch(function () {}); }
      else if (!v.paused) { v.pause(); }
    });
  }


  /* ---- deck mode ----
     On the homepage the four stages run horizontally in one viewport. The
     stage index is driven by input rather than scroll position, and the panels
     track translates instead of the page scrolling. */
  var deck = root.classList.contains('coat--deck');
  if (deck) {
    var track = root.querySelector('.coat__panels');
    var n = panels.length;

    var show = function (i) {
      // wrap rather than clamp: past 04 goes back to 01, before 01 goes to 04,
      // so the four stages run as a loop the way the strip above them does
      i = ((i % n) + n) % n;
      track.style.setProperty('--at', i);
      setStage(i);
    };

    root.querySelectorAll('[data-stage-pip]').forEach(function (d, k) {
      d.addEventListener('click', function () { show(k); });
    });
    var pv = root.querySelector('[data-coat-prev]');
    var nx = root.querySelector('[data-coat-next]');
    if (pv) pv.addEventListener('click', function () { show(current - 1); });
    if (nx) nx.addEventListener('click', function () { show(current + 1); });

    // swipe: horizontal only, so vertical scrolling still passes through
    var sx = null, sy = null;
    root.addEventListener('pointerdown', function (e) {
      if (e.target.closest('a,button')) return;
      sx = e.clientX; sy = e.clientY;
    });
    root.addEventListener('pointerup', function (e) {
      if (sx === null) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1));
      sx = sy = null;
    });
    root.addEventListener('pointercancel', function () { sx = sy = null; });

    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { show(current + 1); e.preventDefault(); }
      if (e.key === 'ArrowLeft')  { show(current - 1); e.preventDefault(); }
    });
    root.tabIndex = 0;

    show(0);
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) setStage(panels.indexOf(e.target)); });
  }, { rootMargin: '-35% 0px -35% 0px', threshold: 0 });
  if (!deck) { panels.forEach(function (p) { io.observe(p); }); setStage(0); }

  /* ---- parallax ----
     Each panel gets --p: -1 when it is a viewport below centre, 0 dead centre,
     +1 a viewport above. The word and the card read that same value but move
     opposite ways, so they separate as the panel crosses — that separation is
     what makes it read as depth rather than as one block sliding. */
  var ticking = false;
  function parallax() {
    var vh = window.innerHeight;
    for (var i = 0; i < panels.length; i++) {
      var r = panels[i].getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) continue;   // far off-screen: skip
      var mid = r.top + r.height / 2;
      var p = (vh / 2 - mid) / vh;                      // -1 .. +1 through centre
      panels[i].style.setProperty('--p', Math.max(-1.4, Math.min(1.4, p)).toFixed(3));
    }
    ticking = false;
  }
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(parallax);
  }
  if (!reduced && !deck) {
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    parallax();
  }

  if (!vids.length || reduced || saveData) return;   // posters are the fallback

  /* ---- load on approach ----
     All four attach at once: a crossfade into a layer that has not started
     loading shows an empty box. They are small (0.3-1.5 MB each) and only the
     active one is ever decoding. */
  var loaded = false;
  new IntersectionObserver(function (entries) {
    var near = entries[0].isIntersecting;
    if (near && !loaded) {
      loaded = true;
      vids.forEach(function (v) { v.src = v.getAttribute('data-src'); v.load(); });
      var act = vids[Math.max(current, 0)];
      if (act) { var pr = act.play(); if (pr && pr.catch) pr.catch(function () {}); }
    }
    if (!loaded) return;
    if (!near) { vids.forEach(function (v) { if (!v.paused) v.pause(); }); }
    else {
      var a = vids[Math.max(current, 0)];
      if (a) { var p2 = a.play(); if (p2 && p2.catch) p2.catch(function () {}); }
    }
  }, { rootMargin: '60% 0px 60% 0px' }).observe(root);

  document.addEventListener('visibilitychange', function () {
    if (!loaded) return;
    if (document.hidden) { vids.forEach(function (v) { v.pause(); }); }
    else {
      var a = vids[Math.max(current, 0)];
      if (a) { var pr = a.play(); if (pr && pr.catch) pr.catch(function () {}); }
    }
  });
})();
