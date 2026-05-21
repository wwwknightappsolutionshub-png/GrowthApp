/**
 * CustomerFlow AI — embeddable booking widget
 * Usage: <script src="https://your-domain/embed/booking-widget.js" data-tenant="your-slug"></script>
 */
(function () {
  var script = document.currentScript
  var tenant = script && script.getAttribute('data-tenant')
  if (!tenant) {
    console.error('[CustomerFlow Booking] data-tenant attribute required')
    return
  }
  var apiBase = script.getAttribute('data-api') || ''
  var color = script.getAttribute('data-color') || '#166534'
  var container = document.createElement('div')
  container.id = 'cf-booking-widget'
  container.style.cssText =
    'font-family:system-ui,sans-serif;border:1px solid #e5e7eb;border-radius:12px;padding:16px;max-width:400px;'
  script.parentNode.insertBefore(container, script.nextSibling)

  var bookUrl = (script.getAttribute('data-book-url') || '').replace(/\/$/, '') ||
    (window.location.origin + '/book/' + tenant)

  container.innerHTML =
    '<p style="margin:0 0 12px;font-weight:600;color:#111">Book an appointment</p>' +
    '<a href="' + bookUrl + '" target="_blank" rel="noopener" style="display:block;text-align:center;' +
    'background:' + color + ';color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none;font-weight:600">' +
    'Book online</a>'

  fetch(apiBase + '/api/v1/public/booking/' + encodeURIComponent(tenant) + '/widget')
    .then(function (r) { return r.json() })
    .then(function (cfg) {
      if (cfg.widget_primary_color) {
        var link = container.querySelector('a')
        if (link) link.style.background = cfg.widget_primary_color
      }
    })
    .catch(function () {})
})()
