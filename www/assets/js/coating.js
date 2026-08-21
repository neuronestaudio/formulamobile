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

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) setStage(panels.indexOf(e.target)); });
  }, { rootMargin: '-35% 0px -35% 0px', threshold: 0 });
  panels.forEach(function (p) { io.observe(p); });
  setStage(0);

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
  if (!reduced) {
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
