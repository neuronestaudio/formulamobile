/**
 * Homepage hero: a carbon-fibre logo splash that dissolves into the carousel.
 *
 * Deliberately NOT a scroll trap. The splash resolves on a timer, and any of
 * scroll / click / key / touch skips it immediately — a brand moment that has
 * to be waited out is an obstacle, not an entrance.
 *
 * It also plays once per session. On the second pageview the visitor lands
 * straight on the carousel, because a logo animation is charming the first
 * time and an obstacle the fourth.
 */
(function () {
  'use strict';

  var hero = document.querySelector('[data-hero]');
  if (!hero) return;

  var splash = hero.querySelector('[data-hero-splash]');
  if (!splash) return;

  var KEY = 'formula_hero_seen';
  var HOLD = 2100; // ms the logo holds before it dissolves

  function reduced() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function seen() {
    try { return sessionStorage.getItem(KEY) === '1'; } catch (e) { return false; }
  }
  function markSeen() {
    try { sessionStorage.setItem(KEY, '1'); } catch (e) { /* private mode */ }
  }

  var done = false;
  function resolve() {
    if (done) return;
    done = true;
    markSeen();
    hero.classList.add('is-resolved');
    // drop it from the a11y tree and hit-testing once it has faded
    setTimeout(function () { splash.hidden = true; }, 1200);
    window.removeEventListener('scroll', resolve);
    window.removeEventListener('wheel', resolve);
    window.removeEventListener('keydown', resolve);
    window.removeEventListener('touchstart', resolve);
    splash.removeEventListener('click', resolve);
  }

  // Already seen this session, or motion is unwelcome: skip straight through.
  if (seen() || reduced()) {
    hero.classList.add('is-instant', 'is-resolved');
    splash.hidden = true;
    return;
  }

  hero.classList.add('is-playing');

  window.addEventListener('scroll', resolve, { passive: true, once: true });
  window.addEventListener('wheel', resolve, { passive: true, once: true });
  window.addEventListener('keydown', resolve, { once: true });
  window.addEventListener('touchstart', resolve, { passive: true, once: true });
  splash.addEventListener('click', resolve);

  setTimeout(resolve, HOLD);
})();
