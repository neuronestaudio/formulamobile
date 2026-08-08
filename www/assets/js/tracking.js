/**
 * Website measurement layer.
 *
 * Vanilla port of src/lib/gtm.ts from github.com/neuronestaudio/Glossedout.
 *
 * Everything pushes to a single `dataLayer`. GTM is the hub that fans events
 * out to GA4, Google Ads and the Meta Pixel — nothing here talks to a vendor
 * directly, so a tag can be added or swapped in GTM without a site deploy.
 *
 * The one conversion event, `generate_lead`, is NOT fired here. It fires in the
 * form handler and only after the CRM webhook returns 2xx, so a reported
 * conversion always corresponds to a lead the CRM actually holds.
 */
(function (root) {
  'use strict';

  function pushGtmEvent(event, payload) {
    try {
      root.dataLayer = root.dataLayer || [];
      var obj = { event: event };
      if (payload) {
        for (var k in payload) {
          if (Object.prototype.hasOwnProperty.call(payload, k)) obj[k] = payload[k];
        }
      }
      root.dataLayer.push(obj);
    } catch (e) {
      /* measurement must never break the page */
    }
  }

  /** Fire a Google Ads conversion directly via gtag, for setups not using GTM. */
  function fireGadsConversion(sendTo) {
    if (!sendTo) return;
    try {
      if (typeof root.gtag === 'function') {
        root.gtag('event', 'conversion', { send_to: sendTo });
      }
    } catch (e) {
      /* no-op */
    }
  }

  /* ---- phone CTA clicks ----
     For a business whose primary conversion is a phone call, an untracked
     tel: click is an invisible conversion. */
  function initPhoneCtaTracking() {
    if (root.__formulaPhoneTrackingBound) return;

    document.addEventListener('click', function (event) {
      var target = event.target;
      var anchor = target && target.closest ? target.closest('a[href^="tel:"]') : null;
      if (!anchor) return;

      var telHref = anchor.getAttribute('href') || '';
      var ctaText =
        (anchor.textContent || '').trim() || anchor.getAttribute('aria-label') || 'phone_cta';

      pushGtmEvent('phone_call_cta_click', {
        phone_number: telHref.replace('tel:', '').trim(),
        cta_text: ctaText,
        cta_href: telHref,
        page_path: root.location.pathname,
        page_title: document.title,
      });
      // GA4 recommended event
      pushGtmEvent('contact', { method: 'phone' });
    });

    root.__formulaPhoneTrackingBound = true;
  }

  /* ---- email clicks ---- */
  function initEmailCtaTracking() {
    if (root.__formulaEmailTrackingBound) return;
    document.addEventListener('click', function (event) {
      var target = event.target;
      var anchor = target && target.closest ? target.closest('a[href^="mailto:"]') : null;
      if (!anchor) return;
      pushGtmEvent('contact', { method: 'email' });
    });
    root.__formulaEmailTrackingBound = true;
  }

  /* ---- scroll depth ---- */
  function initScrollDepthTracking() {
    var thresholds = [25, 50, 75, 90];
    var fired = {};

    function onScroll() {
      var total = document.documentElement.scrollHeight;
      if (!total) return;
      var pct = Math.round(((root.scrollY + root.innerHeight) / total) * 100);
      for (var i = 0; i < thresholds.length; i++) {
        var t = thresholds[i];
        if (pct >= t && !fired[t]) {
          fired[t] = true;
          pushGtmEvent('scroll_depth', {
            scroll_depth_threshold: t,
            page_path: root.location.pathname,
          });
        }
      }
    }

    root.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---- high-intent dwell ---- */
  function initTimeOnPageTracking() {
    setTimeout(function () {
      pushGtmEvent('high_intent_time_on_page', { page_path: root.location.pathname });
    }, 60000);
  }

  /* ---- key service pages ----
     Derived from the URL shape rather than a hardcoded list, so new service and
     suburb pages are covered the moment they are generated. */
  function trackKeyPageVisit() {
    var p = root.location.pathname;
    if (/^\/services\/[^/]+\/$/.test(p)) {
      pushGtmEvent('key_service_page_view', { page_path: p, page_type: 'service' });
    } else if (/^\/mobile-car-detailing\/[^/]+\/$/.test(p)) {
      pushGtmEvent('key_service_page_view', { page_path: p, page_type: 'suburb' });
    }
  }

  root.FormulaTracking = {
    push: pushGtmEvent,
    fireGadsConversion: fireGadsConversion,
  };

  function init() {
    initPhoneCtaTracking();
    initEmailCtaTracking();
    initScrollDepthTracking();
    initTimeOnPageTracking();
    trackKeyPageVisit();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window);
