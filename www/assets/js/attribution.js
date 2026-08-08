/**
 * First-touch advertising attribution.
 *
 * Vanilla port of src/lib/attribution.ts from
 * github.com/neuronestaudio/Glossedout — same semantics, no build step.
 *
 * First-touch, not last-touch: the record is written on the first visit and
 * thereafter only *gap-filled*. A field that already holds a value is never
 * overwritten, and `first_landing_page` is never replaced at all. A later visit
 * on an untagged URL therefore cannot erase what an earlier tagged visit
 * recorded — which is the usual way naive implementations lose attribution.
 *
 * Everything here is best-effort. Private browsing, disabled storage, quota
 * limits and malformed URLs all resolve to empty strings rather than throwing:
 * losing attribution is an inconvenience, losing the lead is not acceptable.
 */
(function (root) {
  'use strict';

  var STORAGE_KEY = 'formula_attribution';

  /**
   * URL-derived fields, in the order they are sent to the CRM.
   *
   * All four click IDs the ad platforms currently issue, not just the one whose
   * channel happens to be running today. They cost an empty string each while a
   * channel is dormant, and capturing one late is not recoverable: a visitor who
   * lands before the field exists already has a record, so gap-fill will never
   * backfill them. `gclid` in particular is what makes an offline conversion
   * import back into Google Ads possible at all.
   *
   * `gbraid` / `wbraid` are the iOS privacy-era replacements Google sends
   * instead of `gclid` (app-to-web and web-to-web) — one campaign can return all
   * three across different visitors.
   */
  var PARAM_FIELDS = [
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_content',
    'utm_term',
    'gclid',
    'gbraid',
    'wbraid',
    'fbclid',
    'msclkid',
  ];

  /* Non-param fields captured alongside them. `referrer` is in the reference
     architecture diagram but is NOT in the Glossedout implementation — added
     here because an untagged organic or referral visit is otherwise
     indistinguishable from direct. */
  var EXTRA_FIELDS = ['first_landing_page', 'referrer'];

  function emptyRecord() {
    var r = {};
    var i;
    for (i = 0; i < PARAM_FIELDS.length; i++) r[PARAM_FIELDS[i]] = '';
    for (i = 0; i < EXTRA_FIELDS.length; i++) r[EXTRA_FIELDS[i]] = '';
    return r;
  }

  /**
   * Coerce anything read out of storage into a known-good shape.
   *
   * Starting from emptyRecord() and copying only the fields actually present is
   * what makes adding a field safe: a record written by an earlier, shorter
   * version of PARAM_FIELDS loads with the new fields empty, leaving them
   * eligible for gap-fill on the visitor's next tagged visit rather than stuck.
   */
  function normalise(value) {
    var record = emptyRecord();
    if (!value || typeof value !== 'object') return record;
    var all = PARAM_FIELDS.concat(EXTRA_FIELDS);
    for (var i = 0; i < all.length; i++) {
      if (typeof value[all[i]] === 'string') record[all[i]] = value[all[i]];
    }
    return record;
  }

  function read() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return normalise(JSON.parse(raw));
    } catch (e) {
      return null;
    }
  }

  function write(record) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(record));
    } catch (e) {
      /* storage unavailable or full — proceed without persisting */
    }
  }

  /**
   * Read attribution parameters from the current URL and persist them.
   * Call once per page load, at startup.
   */
  function captureAttribution() {
    try {
      var params = new URLSearchParams(window.location.search);
      var incoming = emptyRecord();
      var i;
      for (i = 0; i < PARAM_FIELDS.length; i++) {
        incoming[PARAM_FIELDS[i]] = params.get(PARAM_FIELDS[i]) || '';
      }
      incoming.first_landing_page = window.location.href;

      /* Only an EXTERNAL referrer is worth recording. Internal navigation would
         otherwise overwrite the real source with our own domain on visit two. */
      var ref = document.referrer || '';
      if (ref) {
        try {
          if (new URL(ref).hostname === window.location.hostname) ref = '';
        } catch (e) {
          ref = '';
        }
      }
      incoming.referrer = ref;

      var existing = read();

      // No record yet: this visit is the first touch.
      if (!existing) {
        write(incoming);
        return;
      }

      // Gap-fill only. Existing non-empty values win, always.
      var merged = {};
      var all = PARAM_FIELDS.concat(EXTRA_FIELDS);
      for (i = 0; i < all.length; i++) merged[all[i]] = existing[all[i]];
      for (i = 0; i < PARAM_FIELDS.length; i++) {
        if (!merged[PARAM_FIELDS[i]] && incoming[PARAM_FIELDS[i]]) {
          merged[PARAM_FIELDS[i]] = incoming[PARAM_FIELDS[i]];
        }
      }
      if (!merged.first_landing_page) merged.first_landing_page = incoming.first_landing_page;
      if (!merged.referrer) merged.referrer = incoming.referrer;
      write(merged);
    } catch (e) {
      /* malformed URL or blocked storage — attribution is simply not recorded */
    }
  }

  /**
   * The stored attribution record, or a record of empty strings if there is
   * none. Never throws and never returns undefined fields, so the caller can
   * spread it into a payload without guarding.
   */
  function getStoredAttribution() {
    return read() || emptyRecord();
  }

  /**
   * Opaque identifier for a single submission attempt. Random and not derived
   * from anything the visitor entered, so it is safe to store and log.
   * `crypto.randomUUID` needs a secure context; the fallback covers plain-http
   * development hosts and older browsers.
   */
  function createSubmissionId() {
    try {
      if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
      }
    } catch (e) {
      /* fall through to the non-crypto fallback */
    }
    return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 12);
  }

  root.FormulaAttribution = {
    PARAM_FIELDS: PARAM_FIELDS,
    EXTRA_FIELDS: EXTRA_FIELDS,
    capture: captureAttribution,
    get: getStoredAttribution,
    createSubmissionId: createSubmissionId,
  };

  // Capture immediately. This file is loaded in <head> on every page.
  captureAttribution();
})(window);
