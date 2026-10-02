/* Booking + quote forms -> GoHighLevel (sub-account "Renny - A - Formula").
 *
 * The forms used to POST straight to a GHL inbound-webhook trigger. That trigger
 * answers 200 even when its workflow is unpublished, so every lead was accepted
 * and thrown away (the sub-account held 0 contacts on 2 Oct 2026). This writes
 * the contact with the API instead, so the lead is saved whatever the workflow
 * is doing, and still pokes the webhook afterwards so the workflow's own steps
 * (opportunity, assignment, SMS alert) fire once it is published.
 * Same pattern as api/lead.js in the CDS repo.
 *
 * Env (Vercel project formulamobile):
 *   GHL_TOKEN        private integration token (pit-...)
 *   GHL_LOCATION_ID  sub-account id
 *   GHL_WEBHOOK      inbound webhook URL, optional
 *   GHL_ALERT_CONTACT_ID  optional override for the lead-alert contact below
 *
 * EMAIL ALERT: sent from here through GHL's conversations API, because workflow
 * steps cannot be edited over the API. That API only mails an address that
 * belongs to a contact, hence the internal contact "Website Lead Alerts
 * (internal)" whose email is info@formuladetailing.com.au (DND on SMS/calls,
 * email left open). The alerts thread under that contact in GHL's inbox. To add
 * a recipient, add the address to that contact's additional emails AND to
 * ALERT_EMAILS below. Don't delete that contact.
 *
 * GOTCHA: custom fields only save when addressed by BARE key ("service") or by
 * field id. The "contact.service" form the API hands you in customFields listings
 * is accepted, returns 200, and silently stores nothing.
 */
const GHL = 'https://services.leadconnectorhq.com';

// payload name -> the sub-account's field key, minus the "contact." prefix.
// "gclid" cannot be a custom field (GHL reserves it as a native key and drops
// the value), so it lands in the field named "Google Click ID".
const FIELD_MAP = {
  service: 'service',
  vehicle: 'vehicle',
  paint_condition: 'paint_condition',
  interior_condition: 'interior_condition',
  inquiry: 'comments',
  suburb: 'pndulum_suburb',
  postcode: 'postcode',
  source: 'lead_source',
  form_name: 'form_name',
  page: 'landing_page',
  submission_id: 'submission_id',
  first_landing_page: 'first_landing_page',
  referrer: 'referrer',
  utm_source: 'utm_source',
  utm_medium: 'utm_medium',
  utm_campaign: 'utm_campaign',
  utm_term: 'utm_term',
  utm_content: 'utm_content',
  gclid: 'google_click_id',
  gbraid: 'gbraid',
  wbraid: 'wbraid',
  fbclid: 'fbclid',
  msclkid: 'msclkid'
};

const ALERT_CONTACT_ID = process.env.GHL_ALERT_CONTACT_ID || 'ySw3jlPWrwQu75Ozvvgd';
// Each address must be the alert contact's primary or an additional email.
const ALERT_EMAILS = ['info@formuladetailing.com.au', 'dion@pndulumdigital.com'];

const str = (v) => (v === undefined || v === null ? '' : String(v)).trim();

const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Laid out for a phone's mail app: the facts Renny needs to call the lead back.
function alertEmail(body, { name, phone, email, contactId, locationId }) {
  const rows = [
    ['Name', name],
    ['Phone', phone && `<a href="tel:${esc(phone)}">${esc(phone)}</a>`, true],
    ['Email', email && `<a href="mailto:${esc(email)}">${esc(email)}</a>`, true],
    ['Service', str(body.service)],
    ['Vehicle', str(body.vehicle)],
    ['Suburb', [str(body.suburb), str(body.postcode)].filter(Boolean).join(' ')],
    ['Paint', str(body.paint_condition)],
    ['Interior', str(body.interior_condition)],
    ['Message', str(body.inquiry)],
    ['Source', [str(body.source), str(body.utm_source)].filter(Boolean).join(' / ')],
    ['Page', str(body.page)]
  ].filter(([, v]) => v);

  const table = rows.map(([k, v, raw]) =>
    `<tr><td style="padding:6px 14px 6px 0;color:#666;vertical-align:top;white-space:nowrap">${k}</td>` +
    `<td style="padding:6px 0;color:#111">${raw ? v : esc(v).replace(/\n/g, '<br>')}</td></tr>`).join('');

  const link = contactId
    ? `<p style="margin:20px 0 0"><a href="https://app.gohighlevel.com/v2/location/${locationId}/contacts/detail/${contactId}" ` +
      `style="background:#111;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none">Open in GHL</a></p>`
    : '';

  return {
    subject: `New website lead: ${name || phone || email}${str(body.service) ? ` - ${str(body.service)}` : ''}`,
    html: `<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.4">` +
      `<p style="margin:0 0 12px"><strong>New lead from the Formula Mobile Car Detailing website</strong></p>` +
      `<table style="border-collapse:collapse">${table}</table>${link}</div>`
  };
}

// The quote form sends firstname/lastname; the booking form sends one name.
function splitName(body) {
  if (str(body.firstname) || str(body.lastname)) {
    return { firstName: str(body.firstname), lastName: str(body.lastname) };
  }
  const full = str(body.name);
  if (!full) return { firstName: '', lastName: '' };
  const bits = full.split(/\s+/);
  return bits.length === 1
    ? { firstName: bits[0], lastName: '' }
    : { firstName: bits.slice(0, -1).join(' '), lastName: bits[bits.length - 1] };
}

async function postJson(url, headers, payload, ms = 8000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify(payload),
      signal: ctrl.signal
    });
    const text = await r.text();
    return { ok: r.ok, status: r.status, text };
  } finally {
    clearTimeout(timer);
  }
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { return res.status(400).json({ error: 'Bad JSON' }); }
  }
  if (!body || typeof body !== 'object') return res.status(400).json({ error: 'Bad request' });

  const email = str(body.email);
  const phone = str(body.phone);
  if (!email && !phone) return res.status(400).json({ error: 'Need an email or a phone number' });

  const token = process.env.GHL_TOKEN;
  const locationId = process.env.GHL_LOCATION_ID;
  const webhook = process.env.GHL_WEBHOOK;
  const auth = { Authorization: `Bearer ${token}`, Version: '2021-07-28', Accept: 'application/json' };
  const name = str(body.name) || [str(body.firstname), str(body.lastname)].filter(Boolean).join(' ');

  let saved = false;
  let contactId = null;

  if (token && locationId) {
    const { firstName, lastName } = splitName(body);
    const customFields = Object.keys(FIELD_MAP)
      .filter((k) => str(body[k]))
      .map((k) => ({ key: FIELD_MAP[k], field_value: str(body[k]).slice(0, 2000) }));

    // No tags here: upsert REPLACES the tag list, which would strip whatever
    // Renny has tagged a returning customer with. The tag is added below.
    const payload = {
      locationId,
      firstName,
      lastName,
      source: str(body.source) || 'website',
      customFields
    };
    if (email) payload.email = email;
    if (phone) payload.phone = phone;
    if (str(body.suburb)) payload.city = str(body.suburb);
    if (str(body.postcode)) payload.postalCode = str(body.postcode);

    try {
      const r = await postJson(`${GHL}/contacts/upsert`, auth, payload);
      if (r.ok) {
        saved = true;
        try { contactId = JSON.parse(r.text).contact.id; } catch { /* id is a nicety */ }
      } else {
        console.error('GHL upsert failed', r.status, r.text.slice(0, 500));
      }
    } catch (err) {
      console.error('GHL upsert threw', err && err.message);
    }
  } else {
    console.error('GHL_TOKEN or GHL_LOCATION_ID missing - lead not written to the CRM');
  }

  // The rest runs side by side; none of it may fail the request.
  const emailed = [];
  let hooked = false;
  const jobs = [];

  if (contactId) {
    jobs.push(postJson(`${GHL}/contacts/${contactId}/tags`, auth, { tags: ['website lead'] }, 6000)
      .then((t) => { if (!t.ok) console.error('GHL tag failed', t.status, t.text.slice(0, 300)); })
      .catch((err) => console.error('GHL tag threw', err && err.message)));
  }

  // Fire the workflow too. Harmless while it is a draft; once it is published
  // this is what creates the opportunity and sends the SMS alert.
  if (webhook) {
    jobs.push(postJson(webhook, {}, { ...body, full_name: name, lead_source: str(body.source) }, 5000)
      .then((w) => {
        if (w.ok) hooked = true;
        else console.error('GHL webhook failed', w.status, w.text.slice(0, 300));
      })
      .catch((err) => console.error('GHL webhook threw', err && err.message)));
  }

  // Email the alert list, one message each so one bad address can't sink the rest.
  if (token && locationId && ALERT_CONTACT_ID) {
    const msg = alertEmail(body, { name, phone, email, contactId, locationId });
    ALERT_EMAILS.forEach((to) => {
      jobs.push(postJson(`${GHL}/conversations/messages`, auth,
        { type: 'Email', contactId: ALERT_CONTACT_ID, emailTo: to, emailFrom: 'Formula Website <info@formuladetailing.com.au>', ...msg }, 6000)
        .then((a) => {
          if (a.ok) emailed.push(to);
          else console.error('GHL alert email failed', to, a.status, a.text.slice(0, 300));
        })
        .catch((err) => console.error('GHL alert email threw', to, err && err.message)));
    });
  }

  await Promise.all(jobs);

  // Always log the lead so it exists in the deployment logs even if GHL is down.
  console.log('LEAD', JSON.stringify({
    saved, hooked, emailed, contactId, email, phone, name,
    service: str(body.service), suburb: str(body.suburb), vehicle: str(body.vehicle)
  }));

  // The forms only report a conversion (and send the visitor to /thank-you/) on
  // a 2xx, so a lead nobody will ever see must not look like a success: the
  // form then keeps what was typed and offers the phone number instead.
  if (!saved && !emailed.length) return res.status(502).json({ ok: false, error: 'Lead not delivered' });

  return res.status(200).json({ ok: true, saved, id: contactId });
};
