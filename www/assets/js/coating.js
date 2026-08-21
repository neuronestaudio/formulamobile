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

  var vid = root.querySelector('[data-coating-vid]');
  var panels = Array.prototype.slice.call(root.querySelectorAll('[data-stage]'));
  if (!panels.length) return;

  var SRC = '/assets/video/coating-loop.mp4';
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
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) setStage(panels.indexOf(e.target)); });
  }, { rootMargin: '-35% 0px -35% 0px', threshold: 0 });
  panels.forEach(function (p) { io.observe(p); });
  setStage(0);

  if (!vid || reduced || saveData) return;   // poster frame is the fallback

  /* ---- load on approach, and only play while on screen ---- */
  var loaded = false;
  new IntersectionObserver(function (entries) {
    var near = entries[0].isIntersecting;
    if (near && !loaded) {
      loaded = true;
      vid.src = SRC;
      vid.load();
    }
    if (!loaded) return;
    if (near) {
      var pr = vid.play();
      if (pr && pr.catch) pr.catch(function () {});  // autoplay refusal is fine
    } else if (!vid.paused) {
      vid.pause();                                   // no decoding off-screen
    }
  }, { rootMargin: '60% 0px 60% 0px' }).observe(root);

  vid.addEventListener('playing', function () { root.setAttribute('data-mode', 'live'); });
  vid.addEventListener('error', function () { root.removeAttribute('data-mode'); });

  document.addEventListener('visibilitychange', function () {
    if (!loaded) return;
    if (document.hidden) vid.pause();
    else { var pr = vid.play(); if (pr && pr.catch) pr.catch(function () {}); }
  });
})();
