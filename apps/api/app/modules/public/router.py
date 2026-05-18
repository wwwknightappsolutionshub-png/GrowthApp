from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import limiter
from app.modules.auth.schemas import MessageResponse
from app.modules.tenants.models import Tenant

router = APIRouter(prefix="/public", tags=["Public"])


@router.post("/leads/{tenant_slug}", response_model=MessageResponse, status_code=201)
@limiter.limit("10/minute")
async def capture_lead(
    tenant_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Public lead capture endpoint. Rate-limited per IP."""
    from app.modules.leads.schemas import LeadCreate
    from app.modules.leads import service as leads_service

    body = await request.json()
    data = LeadCreate(**body)

    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True))
    tenant = result.scalar_one_or_none()
    if not tenant:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Tenant")

    ip = request.client.host if request.client else None
    lead = await leads_service.create_lead_public(db=db, tenant=tenant, data=data, ip_address=ip)
    return MessageResponse(message="Thank you! We will be in touch shortly.")


@router.get("/widget/reviews/{tenant_slug}")
async def get_review_widget_data(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    """Returns review data for embeddable JS widget."""
    from app.modules.reputation import service as rep_service
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.is_active == True))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"reviews": [], "avg_rating": 0, "total": 0}
    return await rep_service.get_widget_data(db=db, tenant_id=tenant.id)


@router.get("/review/{token}")
async def get_review_page(token: str, db: AsyncSession = Depends(get_db)):
    """Get review request data for the review page."""
    from app.modules.reputation import service as rep_service
    return await rep_service.get_review_request_by_token(db=db, token=token)


@router.post("/review/{token}")
async def submit_review(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Submit a star rating from the review request link."""
    from app.modules.reputation import service as rep_service
    body = await request.json()
    rating = body.get("rating")
    feedback = body.get("feedback")
    result = await rep_service.submit_review_rating(db=db, token=token, rating=rating, feedback=feedback)
    return result


@router.get("/quote/{public_token}")
async def get_public_quote(public_token: str, db: AsyncSession = Depends(get_db)):
    from app.modules.quotes_invoices import service as qi_service
    return await qi_service.get_public_quote(db=db, public_token=public_token)


@router.post("/quote/{public_token}/respond")
async def respond_to_quote(public_token: str, request: Request, db: AsyncSession = Depends(get_db)):
    from app.modules.quotes_invoices import service as qi_service
    body = await request.json()
    return await qi_service.respond_to_quote(db=db, public_token=public_token, accepted=body.get("accepted", True))


@router.get("/booking/{tenant_slug}/availability")
async def get_availability(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    from app.modules.booking import service as booking_service
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"slots": []}
    return await booking_service.get_available_slots(db=db, tenant_id=tenant.id)


@router.post("/booking/{tenant_slug}")
async def create_public_booking(tenant_slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    from app.modules.booking.schemas import PublicBookingCreate
    from app.modules.booking import service as booking_service
    body = await request.json()
    data = PublicBookingCreate(**body)
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Tenant")
    return await booking_service.create_public_booking(db=db, tenant=tenant, data=data)


@router.get("/landing/{tenant_slug}/{page_slug}")
async def get_public_landing_page(
    tenant_slug: str, page_slug: str, db: AsyncSession = Depends(get_db)
):
    """Return the published landing page JSON for a tenant/slug."""
    from app.modules.landing_pages import service as lp_service

    page = await lp_service.get_public_page(db, tenant_slug, page_slug)
    return {
        "slug": page.slug,
        "title": page.title,
        "meta_description": page.meta_description,
        "cover_image_url": page.cover_image_url,
        "theme": page.theme or {},
        "sections": page.sections or [],
    }


@router.get("/widget.js", response_class=PlainTextResponse)
async def widget_js(request: Request):
    """Tenant-agnostic loader script.

    Embed on any site:
      <script src="https://api.example.com/api/v1/public/widget.js" defer
              data-tenant="acme-plumbers"
              data-mode="lead"></script>

    The script reads `data-tenant` + `data-mode` from its own <script> tag,
    posts to /public/leads/{tenant} for the lead form, and renders a small
    floating widget. Pure vanilla JS — no React on the host page.
    """
    api_base = settings.PUBLIC_API_BASE_URL or "/api/v1"
    js = _WIDGET_JS.replace("__API_BASE__", api_base)
    headers = {
        "Content-Type": "application/javascript; charset=utf-8",
        "Cache-Control": "public, max-age=300",
        "Access-Control-Allow-Origin": "*",
    }
    return PlainTextResponse(js, headers=headers)


# Inline because we want a single self-contained vanilla JS asset.
_WIDGET_JS = r"""
/*! CustomerFlow AI widget */
(function () {
  if (window.__cfAiWidgetLoaded) return; window.__cfAiWidgetLoaded = true;
  var script = document.currentScript || (function () {
    var s = document.getElementsByTagName('script');
    return s[s.length - 1];
  })();
  var tenant = (script && script.getAttribute('data-tenant')) || '';
  var mode = (script && script.getAttribute('data-mode')) || 'lead';
  var primary = (script && script.getAttribute('data-color')) || '#2563EB';
  var label = (script && script.getAttribute('data-label')) || 'Get a free quote';
  if (!tenant) { console.error('[CustomerFlow] data-tenant attribute is required'); return; }
  var API = '__API_BASE__';

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'style') n.style.cssText = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }

  var styles = '\
.cf-fab{position:fixed;right:20px;bottom:20px;background:' + primary + ';color:#fff;font:600 14px system-ui,sans-serif;border:none;border-radius:999px;padding:14px 20px;box-shadow:0 6px 22px rgba(0,0,0,.18);cursor:pointer;z-index:2147483647;}\
.cf-fab:hover{filter:brightness(.95);}\
.cf-overlay{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:2147483647;font-family:system-ui,sans-serif;}\
.cf-modal{background:#fff;color:#111;border-radius:14px;max-width:420px;width:calc(100% - 32px);padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.3);}\
.cf-modal h3{margin:0 0 6px;font-size:18px;}\
.cf-modal p{margin:0 0 14px;font-size:13px;color:#555;}\
.cf-modal label{display:block;font-size:12px;color:#444;margin:8px 0 4px;}\
.cf-modal input,.cf-modal textarea{width:100%;padding:10px;border:1px solid #d4d4d8;border-radius:8px;font:14px system-ui,sans-serif;box-sizing:border-box;}\
.cf-modal textarea{resize:vertical;min-height:80px;}\
.cf-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px;}\
.cf-btn{font:600 13px system-ui;padding:10px 16px;border-radius:8px;cursor:pointer;}\
.cf-btn-primary{background:' + primary + ';color:#fff;border:none;}\
.cf-btn-secondary{background:transparent;border:none;color:#555;}\
.cf-ok{color:#16a34a;font-size:13px;text-align:center;padding:24px 0;}\
.cf-err{color:#dc2626;font-size:12px;margin-top:8px;}\
.cf-foot{text-align:center;font-size:10px;color:#999;margin-top:14px;}\
';
  document.head.appendChild(el('style', {}, [styles]));

  var btn = el('button', { 'class': 'cf-fab', 'type': 'button' });
  btn.textContent = label;
  document.body.appendChild(btn);

  btn.addEventListener('click', function () {
    var overlay = el('div', { 'class': 'cf-overlay' });
    var status = el('div');
    var firstName = el('input', { 'type': 'text', 'name': 'first_name', 'required': 'required', 'placeholder': 'Your name' });
    var phone = el('input', { 'type': 'tel', 'name': 'phone', 'required': 'required', 'placeholder': '07…' });
    var email = el('input', { 'type': 'email', 'name': 'email', 'placeholder': 'name@example.com' });
    var message = el('textarea', { 'name': 'message', 'placeholder': 'What do you need help with?' });
    var err = el('div', { 'class': 'cf-err' });
    var submit = el('button', { 'class': 'cf-btn cf-btn-primary', 'type': 'submit' });
    submit.textContent = 'Send enquiry';
    var cancel = el('button', { 'class': 'cf-btn cf-btn-secondary', 'type': 'button' });
    cancel.textContent = 'Cancel';

    var form = el('form', {}, [
      el('label', {}, ['Name']), firstName,
      el('label', {}, ['Phone']), phone,
      el('label', {}, ['Email (optional)']), email,
      el('label', {}, ['Message (optional)']), message,
      err,
      el('div', { 'class': 'cf-actions' }, [cancel, submit]),
    ]);

    var modal = el('div', { 'class': 'cf-modal' }, [
      el('h3', {}, ['Request a quote']),
      el('p', {}, ['Pop your details in and we will get back to you shortly.']),
      status,
      form,
      el('div', { 'class': 'cf-foot' }, ['Powered by CustomerFlow AI']),
    ]);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    function close() { try { document.body.removeChild(overlay); } catch (e) {} }
    cancel.addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      err.textContent = '';
      submit.disabled = true; submit.textContent = 'Sending…';
      var body = {
        first_name: firstName.value.trim(),
        phone: phone.value.trim(),
        email: email.value.trim() || null,
        message: message.value.trim() || null,
        source: 'embed_widget',
      };
      fetch(API + '/public/leads/' + encodeURIComponent(tenant), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(function (r) {
        if (!r.ok) return r.json().then(function (j) { throw new Error(j.detail || 'Failed'); });
        return r.json();
      }).then(function () {
        status.className = 'cf-ok';
        status.textContent = '✓ Thanks — we will be in touch shortly.';
        try { modal.removeChild(form); } catch (e) {}
        setTimeout(close, 2200);
      }).catch(function (e) {
        err.textContent = e.message || 'Something went wrong, please try again.';
        submit.disabled = false; submit.textContent = 'Send enquiry';
      });
    });
  });
})();
"""
