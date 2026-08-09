/**
 * Ceramic coating scroll film — a Range Rover Sport that the visitor walks
 * around while four stages of the coating process are explained.
 *
 * Architecture (carried over from the Protection Lab / STRATUM builds, which
 * is the only part worth remembering): STAGES below is the entire film. The
 * camera is polar — azimuth / elevation / radius around a look-at — so travel
 * between stages arcs *around* the vehicle rather than driving through it.
 * Timing is measured off the DOM: each stage panel's height IS its duration,
 * so re-pacing the film is a CSS change, not a magic number here.
 *
 * Loading is poster-first. The section paints a still render immediately and
 * only fetches three.js + the 5 MB GLB when the visitor gets within a viewport
 * of it. Reduced-motion and Save-Data never load it at all — they keep the
 * still, which says the same thing.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-coating]');
  if (!root) return;

  var canvas = root.querySelector('[data-coating-canvas]');
  var panels = Array.prototype.slice.call(root.querySelectorAll('[data-stage]'));
  if (!canvas || !panels.length) return;

  var MODEL = canvas.getAttribute('data-model');

  /* ---- keyframes ----------------------------------------------------------
     az/el in radians, r in metres, look-at height in metres.
     `shift` pans in CAMERA space to compose the car against the copy, and its
     sign is counter-intuitive: a POSITIVE x moves the camera right, which
     pushes the vehicle LEFT on screen. Copy sits left here, so every stage
     wants a NEGATIVE x to hold the car clear of it.
     `env` is the scene environment intensity, normalised so the final
     coated stage is 1.0.                                                    */
  var STAGES = [
    { az: -0.62, el: 0.15, r: 13.0, y: 0.80, shift: [-2.30, -0.02], env: 0.58 },
    { az:  0.60, el: 0.09, r: 11.6, y: 0.78, shift: [-2.15,  0.04], env: 0.74 },
    { az:  1.80, el: 0.22, r: 11.2, y: 0.90, shift: [-2.20, -0.04], env: 0.88 },
    { az:  3.05, el: 0.12, r: 12.4, y: 0.82, shift: [-2.10,  0.02], env: 1.00 },
  ];

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var saveData = navigator.connection && navigator.connection.saveData;

  /* ---- stage copy state: runs with or without 3D ---- */
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
    entries.forEach(function (e) {
      if (e.isIntersecting) setStage(panels.indexOf(e.target));
    });
  }, { rootMargin: '-35% 0px -35% 0px', threshold: 0 });
  panels.forEach(function (p) { io.observe(p); });
  setStage(0);

  if (reduced || saveData) {
    root.setAttribute('data-mode', 'poster');
    return;
  }

  /* ---- lazy boot: only fetch the heavy parts on approach ---- */
  var booted = false;
  var near = new IntersectionObserver(function (entries) {
    if (entries[0].isIntersecting && !booted) { booted = true; near.disconnect(); boot(); }
  }, { rootMargin: '35% 0px 35% 0px' });
  near.observe(root);

  function boot() {
    root.setAttribute('data-mode', 'loading');
    Promise.all([
      import('/assets/js/vendor/three.module.js'),
      import('/assets/js/vendor/GLTFLoader.js'),
      import('/assets/js/vendor/meshopt_decoder.module.js'),
    ]).then(function (mods) {
      run(mods[0], mods[1].GLTFLoader, mods[2].MeshoptDecoder);
    }).catch(function () {
      root.setAttribute('data-mode', 'poster'); // the still is a fine fallback
    });
  }

  function run(THREE, GLTFLoader, MeshoptDecoder) {
    var renderer = new THREE.WebGLRenderer({
      canvas: canvas, antialias: true, alpha: true, powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);

    /* Environment drives nearly all the look on a car. Build one procedurally
       rather than shipping an HDR: a soft overhead bar plus a dark floor is
       what makes clearcoat read as clearcoat. */
    var pmrem = new THREE.PMREMGenerator(renderer);
    var envScene = new THREE.Scene();
    envScene.background = new THREE.Color(0x14161c);
    var bar = new THREE.Mesh(
      new THREE.BoxGeometry(22, 0.6, 7),
      new THREE.MeshBasicMaterial({ color: 0xffffff })
    );
    bar.position.set(0, 8, 0);
    envScene.add(bar);
    var side = new THREE.Mesh(
      new THREE.BoxGeometry(0.6, 6, 16),
      new THREE.MeshBasicMaterial({ color: 0xdfe6f2 })
    );
    side.position.set(9, 4, 0);
    envScene.add(side);
    var rim = new THREE.Mesh(
      new THREE.BoxGeometry(0.6, 4, 10),
      new THREE.MeshBasicMaterial({ color: 0xf5342d })
    );
    rim.position.set(-9, 2.6, 0);
    envScene.add(rim);
    var envRT = pmrem.fromScene(envScene, 0.05);
    scene.environment = envRT.texture;
    envScene.clear();
    pmrem.dispose();

    var key = new THREE.DirectionalLight(0xffffff, 3.0);
    key.position.set(4, 7, 5);
    scene.add(key);
    var fill = new THREE.DirectionalLight(0xf5342d, 0.7);
    fill.position.set(-6, 2.5, -4);
    scene.add(fill);

    var pivot = new THREE.Group();
    scene.add(pivot);

    /* The web build is gltfpack output: EXT_meshopt_compression is in
       extensionsRequired, so without this decoder GLTFLoader fails and calls
       neither onLoad nor a useful onError — the section just sits on the
       poster forever with a clean console. */
    var loader = new GLTFLoader();
    loader.setMeshoptDecoder(MeshoptDecoder);
    loader.load(MODEL, function (gltf) {
      var car = gltf.scene;

      // Centre on its own bounding box and sit it on the floor.
      var box = new THREE.Box3().setFromObject(car);
      var size = box.getSize(new THREE.Vector3());
      var mid = box.getCenter(new THREE.Vector3());
      car.position.set(-mid.x, -box.min.y, -mid.z);

      car.traverse(function (o) {
        if (!o.isMesh) return;
        o.castShadow = o.receiveShadow = false;
        var m = o.material;
        if (!m) return;
        /* Never set material.envMap: it overrides scene.environment and with
           it scene.environmentIntensity, so the stage light level stops
           working and the opening stage can never go dark. */
        if (m.isMeshStandardMaterial) {
          m.envMapIntensity = 1.0;
          if (/paint|body|car_paint/i.test(m.name || '')) {
            m.clearcoat = 1.0;
            m.clearcoatRoughness = 0.04;
            m.roughness = 0.28;
          }
        }
      });

      pivot.add(car);
      root.setAttribute('data-mode', 'live');
      window.__coatingReady = true;   // QA hook
      onResize();
      tick();

      // vehicle length feeds the radius scale so framing is model-agnostic
      pivot.userData.span = Math.max(size.x, size.z);
    }, undefined, function () {
      root.setAttribute('data-mode', 'poster');
    });

    /* ---- responsive framing ----
       fov is VERTICAL, so a portrait viewport crops horizontally: the same
       keyframe that frames the car on a laptop puts it well past the edges on
       a phone. Pull the radius back by aspect, and switch on VIEWPORT rather
       than touch capability — a tablet in landscape wants the desktop frame. */
    var aspect = 1;
    function onResize() {
      var r = root.getBoundingClientRect();
      var w = Math.max(1, r.width);
      var h = Math.max(1, window.innerHeight);
      aspect = w / h;
      renderer.setSize(w, h, false);
      camera.aspect = aspect;
      camera.updateProjectionMatrix();
    }
    window.addEventListener('resize', onResize, { passive: true });

    function radiusScale() {
      if (aspect >= 1.5) return 1;
      // below 3:2 the frame narrows fast; 0.62 is the portrait floor
      return Math.max(0.62, aspect / 1.5) * (aspect < 0.85 ? 1.42 : 1.16);
    }

    /* ---- scroll → interpolated keyframe ---- */
    var tmpA = { az: 0, el: 0, r: 0, y: 0, sx: 0, sy: 0, env: 0 };
    function sample() {
      var rect = root.getBoundingClientRect();
      var runway = root.offsetHeight - window.innerHeight;
      var p = runway > 0 ? Math.min(Math.max(-rect.top / runway, 0), 1) : 0;

      var f = p * (STAGES.length - 1);
      var i = Math.min(Math.floor(f), STAGES.length - 2);
      var t = f - i;
      // smoothstep keeps the arrival at each stage soft
      t = t * t * (3 - 2 * t);

      var a = STAGES[i], b = STAGES[i + 1];
      tmpA.az = a.az + (b.az - a.az) * t;
      tmpA.el = a.el + (b.el - a.el) * t;
      tmpA.r = (a.r + (b.r - a.r) * t) * radiusScale();
      tmpA.y = a.y + (b.y - a.y) * t;
      tmpA.sx = a.shift[0] + (b.shift[0] - a.shift[0]) * t;
      tmpA.sy = a.shift[1] + (b.shift[1] - a.shift[1]) * t;
      tmpA.env = a.env + (b.env - a.env) * t;
      return tmpA;
    }

    var cur = null;
    function tick() {
      requestAnimationFrame(tick);
      var rect = root.getBoundingClientRect();
      if (rect.bottom < -200 || rect.top > window.innerHeight + 200) return;

      var k = sample();
      if (!cur) cur = { az: k.az, el: k.el, r: k.r, y: k.y, sx: k.sx, sy: k.sy, env: k.env };
      var e = 0.12;
      cur.az += (k.az - cur.az) * e;
      cur.el += (k.el - cur.el) * e;
      cur.r += (k.r - cur.r) * e;
      cur.y += (k.y - cur.y) * e;
      cur.sx += (k.sx - cur.sx) * e;
      cur.sy += (k.sy - cur.sy) * e;
      cur.env += (k.env - cur.env) * e;

      camera.position.set(
        Math.cos(cur.el) * Math.sin(cur.az) * cur.r,
        Math.sin(cur.el) * cur.r + cur.y,
        Math.cos(cur.el) * Math.cos(cur.az) * cur.r
      );
      camera.lookAt(0, cur.y, 0);
      camera.translateX(cur.sx);
      camera.translateY(cur.sy);

      scene.environmentIntensity = cur.env;
      key.intensity = 2.2 + cur.env * 1.6;
      fill.intensity = 0.5 + cur.env * 0.8;

      renderer.render(scene, camera);
    }
  }
})();
