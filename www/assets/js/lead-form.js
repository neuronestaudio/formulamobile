/**
 * Quote form → GHL inbound webhook.
 *
 * Vanilla port of the submit path in src/components/QuoteForm.tsx from
 * github.com/neuronestaudio/Glossedout. The disciplines worth keeping:
 *
 *  - `generate_lead` fires ONLY after the webhook returns 2xx. A conversion
 *    reported to Google Ads or Meta always corresponds to a lead the CRM
 *    actually holds; a network failure reports nothing rather than a phantom.
 *  - Every failure path leaves the visitor's input untouched so they can just
 *    press the button again, and names the phone number as the way out.
 *  - An in-flight latch means double-clicks cannot produce two contacts.
 *  - AbortController rather than AbortSignal.timeout, for wider browser support.
 *
 * Progressive enhancement: with JS disabled the form keeps its native
 * action/method, and the phone number is on every page regardless.
 */
(function () {
  'use strict';

  var form = document.querySelector('[data-lead-form]');
  if (!form) return;

  var cfg = window.FORMULA_CFG || {};
  var WEBHOOK = cfg.ghlWebhook || '';
  var REQUEST_TIMEOUT_MS = 15000;
  var PHONE = cfg.phoneDisplay || '';

  var btn = form.querySelector('[type="submit"]');
  var errBox = form.querySelector('[data-form-error]');
  var inFlight = false;

  function showError(msg) {
    if (errBox) {
      errBox.textContent = msg;
      errBox.hidden = false;
    }
    inFlight = false;
    if (btn) {
      btn.disabled = false;
      btn.textContent = btn.getAttribute('data-label') || 'Send enquiry';
    }
  }

  function failWithRetry() {
    showError(
      "We couldn't send your request just now — your details are still here. " +
        'Please press the button to try again' +
        (PHONE ? ', or call us on ' + PHONE + '.' : '.')
    );
  }

  form.addEventListener('submit', function (e) {
    // No webhook configured: fall through to the native form post so the build
    // is never silently swallowing leads into a dead fetch.
    if (!WEBHOOK) return;

    e.preventDefault();
    if (inFlight) return;

    // Let the browser's own validation speak first.
    if (typeof form.reportValidity === 'function' && !form.reportValidity()) return;

    inFlight = true;
    if (errBox) errBox.hidden = true;
    if (btn) {
      if (!btn.getAttribute('data-label')) btn.setAttribute('data-label', btn.textContent);
      btn.disabled = true;
      btn.textContent = 'Sending…';
    }

    var attrib = window.FormulaAttribution
      ? window.FormulaAttribution.get()
      : {};
    var submissionId = window.FormulaAttribution
      ? window.FormulaAttribution.createSubmissionId()
      : String(Date.now());

    var fd = new FormData(form);
    var payload = {
      name: ((fd.get('firstname') || '') + ' ' + (fd.get('lastname') || '')).trim(),
      firstname: (fd.get('firstname') || '').trim(),
      lastname: (fd.get('lastname') || '').trim(),
      email: (fd.get('email') || '').trim(),
      phone: (fd.get('phone') || '').trim(),
      suburb: (fd.get('suburb') || '').trim(),
      service: fd.get('service') || '',
      vehicle: (fd.get('vehicle') || '').trim(),
      inquiry: (fd.get('comments') || '').trim(),
      source: 'Website Quote Form',
      page: window.location.pathname,
      submission_id: submissionId,
    };

    // Attribution fields, flattened onto the payload exactly as GHL expects.
    var fields = (window.FormulaAttribution
      ? window.FormulaAttribution.PARAM_FIELDS.concat(window.FormulaAttribution.EXTRA_FIELDS)
      : []);
    for (var i = 0; i < fields.length; i++) {
      payload[fields[i]] = attrib[fields[i]] || '';
    }

    var controller = new AbortController();
    var timer = setTimeout(function () {
      controller.abort();
    }, REQUEST_TIMEOUT_MS);

    fetch(WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
      .then(function (res) {
        clearTimeout(timer);
        if (!res.ok) {
          failWithRetry();
          return;
        }

        // GHL returned 2xx — the lead is captured, so the conversion is real.
        if (window.FormulaTracking) {
          window.FormulaTracking.push('quote_form_submit', {
            form_name: 'get_a_quote',
            service_context: payload.service || 'general',
            page_path: window.location.pathname,
            page_title: document.title,
          });
          window.FormulaTracking.push('generate_lead', { currency: 'AUD', value: 0 });
          if (cfg.gadsConversion) {
            window.FormulaTracking.fireGadsConversion(cfg.gadsConversion);
          }
        }

        /* inFlight stays latched and the button stays disabled. The page is
           about to navigate, and leaving them set is what guarantees the events
           above fire exactly once — a second submit can't slip through the gap
           before navigation completes. */
        window.location.href = '/thank-you/';
      })
      .catch(function () {
        clearTimeout(timer);
        failWithRetry();
      });
  });
})();
