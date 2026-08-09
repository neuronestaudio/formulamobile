/**
 * Booking wizard — adopts the 4-step flow from
 * premiermobiledetailing.com.au/booking (Service → Location → Vehicle →
 * Details), wired to Formula's services and to the Glossedout lead-gen layer.
 *
 * Submit discipline is the same as lead-form.js and for the same reason:
 * `generate_lead` fires only after the CRM webhook returns 2xx, so a reported
 * conversion always corresponds to a lead the CRM actually holds.
 *
 * Progressive enhancement: with JS off, every step is visible at once and the
 * form still posts natively — a wizard that hides four fifths of itself and
 * then fails to run is worse than a long form.
 */
(function () {
  'use strict';

  var form = document.querySelector('[data-booking]');
  if (!form) return;

  var cfg = window.FORMULA_CFG || {};
  var WEBHOOK = cfg.ghlWebhook || '';
  var PHONE = cfg.phoneDisplay || '';
  var TIMEOUT_MS = 15000;

  var steps = Array.prototype.slice.call(form.querySelectorAll('[data-step]'));
  var dots = Array.prototype.slice.call(document.querySelectorAll('[data-dot]'));
  var backBtn = form.querySelector('[data-back]');
  var nextBtn = form.querySelector('[data-next-step]');
  var submitBtn = form.querySelector('[data-submit]');
  var errBox = form.querySelector('[data-form-error]');
  var live = form.querySelector('[data-live]');

  var at = 0;
  var inFlight = false;

  form.classList.add('is-wizard'); // only now do we hide the other steps

  function show(i) {
    at = Math.min(Math.max(i, 0), steps.length - 1);
    steps.forEach(function (s, k) { s.hidden = k !== at; });
    dots.forEach(function (d, k) {
      d.setAttribute('data-state', k < at ? 'done' : k === at ? 'now' : 'todo');
    });

    if (backBtn) backBtn.hidden = at === 0;
    var last = at === steps.length - 1;
    if (nextBtn) nextBtn.hidden = last;
    if (submitBtn) submitBtn.hidden = !last;

    if (live) live.textContent = 'Step ' + (at + 1) + ' of ' + steps.length;

    // move focus to the new step so keyboard and screen-reader users follow
    var focusable = steps[at].querySelector('input, select, textarea, button, [tabindex]');
    if (focusable) { try { focusable.focus({ preventScroll: true }); } catch (e) { focusable.focus(); } }

    var top = form.getBoundingClientRect().top + window.scrollY - 110;
    window.scrollTo({ top: top, behavior: reduced() ? 'auto' : 'smooth' });
  }

  function reduced() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /** Validate only the visible step — reportValidity() on the whole form would
      trip over required fields the visitor hasn't reached yet. */
  function stepValid() {
    var fields = steps[at].querySelectorAll('input, select, textarea');
    for (var i = 0; i < fields.length; i++) {
      if (!fields[i].checkValidity()) {
        fields[i].reportValidity();
        return false;
      }
    }
    // every tile group on this step needs a choice — the vehicle step has two
    var groups = steps[at].querySelectorAll('[data-requires-choice]');
    for (var g = 0; g < groups.length; g++) {
      if (!groups[g].querySelector('input:checked')) {
        showError('Pick an option to continue.');
        groups[g].scrollIntoView({ block: 'center', behavior: reduced() ? 'auto' : 'smooth' });
        return false;
      }
    }
    return true;
  }

  function showError(msg) {
    if (!errBox) return;
    errBox.textContent = msg;
    errBox.hidden = false;
  }
  function clearError() { if (errBox) errBox.hidden = true; }

  /* ---- tiles: clicking anywhere on the card selects its radio ---- */
  form.addEventListener('change', function (e) {
    if (e.target.matches('input[type="radio"]')) {
      clearError();
      var name = e.target.name;
      form.querySelectorAll('input[name="' + name + '"]').forEach(function (r) {
        var tile = r.closest('.bk__tile');
        if (tile) tile.classList.toggle('is-on', r.checked);
      });
    }
  });

  if (nextBtn) {
    nextBtn.addEventListener('click', function () {
      clearError();
      if (stepValid()) show(at + 1);
    });
  }
  if (backBtn) {
    backBtn.addEventListener('click', function () { clearError(); show(at - 1); });
  }

  // Enter should advance a step, not submit from step 1
  form.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && at < steps.length - 1) {
      e.preventDefault();
      if (stepValid()) show(at + 1);
    }
  });

  /* ---- submit ---- */
  form.addEventListener('submit', function (e) {
    if (!WEBHOOK) return; // no CRM configured: fall through to the native post
    e.preventDefault();
    if (inFlight) return;
    if (!stepValid()) return;

    inFlight = true;
    clearError();
    var label = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending…'; }

    var A = window.FormulaAttribution;
    var attrib = A ? A.get() : {};
    var submissionId = A ? A.createSubmissionId() : String(Date.now());

    var fd = new FormData(form);
    var payload = {
      name: (fd.get('name') || '').trim(),
      phone: (fd.get('phone') || '').trim(),
      email: (fd.get('email') || '').trim(),
      service: fd.get('service') || '',
      location_type: fd.get('location_type') || '',
      suburb: (fd.get('suburb') || '').trim(),
      postcode: (fd.get('postcode') || '').trim(),
      vehicle: (fd.get('vehicle') || '').trim(),
      paint_condition: fd.get('paint_condition') || '',
      interior_condition: fd.get('interior_condition') || '',
      inquiry: (fd.get('comments') || '').trim(),
      source: 'Website Booking Form',
      page: window.location.pathname,
      submission_id: submissionId,
    };

    if (A) {
      A.PARAM_FIELDS.concat(A.EXTRA_FIELDS).forEach(function (f) {
        payload[f] = attrib[f] || '';
      });
    }

    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);

    fetch(WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
      .then(function (res) {
        clearTimeout(timer);
        if (!res.ok) return fail(label);

        if (window.FormulaTracking) {
          window.FormulaTracking.push('booking_form_submit', {
            form_name: 'booking',
            service_context: payload.service || 'unspecified',
            page_path: window.location.pathname,
          });
          window.FormulaTracking.push('generate_lead', { currency: 'AUD', value: 0 });
          if (cfg.gadsConversion) {
            window.FormulaTracking.fireGadsConversion(cfg.gadsConversion);
          }
        }
        // latch stays set: the page is navigating, so the events fire once
        window.location.href = '/thank-you/';
      })
      .catch(function () { clearTimeout(timer); fail(label); });
  });

  function fail(label) {
    showError(
      "We couldn't send that just now — everything you entered is still here. " +
        'Press the button to try again' + (PHONE ? ', or call us on ' + PHONE + '.' : '.')
    );
    inFlight = false;
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = label; }
  }

  show(0);
})();
