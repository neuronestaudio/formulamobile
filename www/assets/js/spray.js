/**
 * Interactive spray on headings.
 *
 * Hovering a title lays down a soft mist that follows the cursor and BUILDS
 * the longer you dwell — a coating going on. Leave, and it fades back off.
 *
 * Drawn on one canvas per heading rather than as DOM nodes: a dwell effect
 * emits continuously, and hundreds of divs would thrash layout. The canvas is
 * created lazily on first hover, so a page of headings costs nothing until one
 * is actually used.
 *
 * Pointer-fine only. On touch there is no hover state to build with, and
 * reduced-motion opts out entirely.
 */
(function () {
  'use strict';

  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var SEL = 'h1, h2, .coat__word, .sm__h, .rsn__t';
  var MAX = 0.62;          // ceiling on how dark the mist gets
  var GROW = 0.055;        // per frame while dwelling
  var FADE = 0.028;        // per frame once the cursor leaves

  document.querySelectorAll(SEL).forEach(function (el) {
    if (!el.textContent.trim()) return;

    var canvas = null, ctx = null, raf = 0;
    var pts = [], strength = 0, inside = false, mx = 0, my = 0;

    function mount() {
      canvas = document.createElement('canvas');
      canvas.className = 'spray';
      var cs = getComputedStyle(el);
      if (cs.position === 'static') el.style.position = 'relative';
      el.appendChild(canvas);
      ctx = canvas.getContext('2d');
      size();
    }

    function size() {
      var r = el.getBoundingClientRect();
      var d = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(r.width * d));
      canvas.height = Math.max(1, Math.round(r.height * d));
      canvas.style.width = r.width + 'px';
      canvas.style.height = r.height + 'px';
      ctx.setTransform(d, 0, 0, d, 0, 0);
    }

    function draw() {
      var r = el.getBoundingClientRect();
      ctx.clearRect(0, 0, r.width, r.height);

      // dwell builds the mist, leaving bleeds it off
      strength += inside ? GROW : -FADE;
      strength = Math.max(0, Math.min(MAX, strength));

      if (inside && pts.length < 90 && Math.random() < 0.85) {
        pts.push({
          x: mx + (Math.random() - 0.5) * 46,
          y: my + (Math.random() - 0.5) * 26,
          r: 8 + Math.random() * 26,
          a: 0.10 + Math.random() * 0.16,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.25 - 0.06,
        });
      }

      for (var i = pts.length - 1; i >= 0; i--) {
        var p = pts[i];
        p.x += p.vx; p.y += p.vy; p.r += 0.16;
        p.a *= inside ? 0.988 : 0.94;
        if (p.a < 0.004) { pts.splice(i, 1); continue; }
        var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
        g.addColorStop(0, 'rgba(245,52,45,' + (p.a * strength / MAX).toFixed(3) + ')');
        g.addColorStop(1, 'rgba(245,52,45,0)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.284); ctx.fill();
      }

      if (inside || pts.length || strength > 0.001) {
        raf = requestAnimationFrame(draw);
      } else {
        raf = 0;
        ctx.clearRect(0, 0, r.width, r.height);
      }
    }

    el.addEventListener('pointerenter', function () {
      if (!canvas) mount(); else size();
      inside = true;
      if (!raf) raf = requestAnimationFrame(draw);
    });

    el.addEventListener('pointermove', function (e) {
      var r = el.getBoundingClientRect();
      mx = e.clientX - r.left;
      my = e.clientY - r.top;
    });

    el.addEventListener('pointerleave', function () { inside = false; });
  });
})();
