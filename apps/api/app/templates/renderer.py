from pathlib import Path
from functools import lru_cache
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_email(template_name: str, context: dict) -> str:
    """Render an email HTML template. template_name e.g. 'emails/booking_confirmation.html'"""
    env = _get_env()
    template = env.get_template(template_name)
    return template.render(**context)


# ── Typed helpers ──────────────────────────────────────────────────────────


def render_booking_confirmation(
    *,
    customer_name: str,
    business_name: str,
    booking_date: str,
    start_time: str,
    service_description: str | None = None,
    staff_name: str | None = None,
    deposit_required_pence: int = 0,
    deposit_paid: bool = False,
    notes: str | None = None,
    business_phone: str | None = None,
    business_email: str | None = None,
) -> str:
    return render_email(
        "emails/booking_confirmation.html",
        {
            "subject": f"Booking Confirmed — {business_name}",
            "customer_name": customer_name,
            "business_name": business_name,
            "booking_date": booking_date,
            "start_time": start_time,
            "service_description": service_description,
            "staff_name": staff_name,
            "deposit_required_pence": deposit_required_pence,
            "deposit_paid": deposit_paid,
            "notes": notes,
            "business_phone": business_phone,
            "business_email": business_email,
        },
    )


def render_quote_sent(
    *,
    customer_name: str,
    business_name: str,
    quote_number: str,
    quote_title: str,
    quote_url: str,
    subtotal_pence: int,
    vat_pence: int,
    total_pence: int,
    valid_until: str | None = None,
    notes: str | None = None,
    line_items: list[dict] | None = None,
    business_phone: str | None = None,
) -> str:
    return render_email(
        "emails/quote_sent.html",
        {
            "subject": f"Your Quote from {business_name} — {quote_number}",
            "customer_name": customer_name,
            "business_name": business_name,
            "quote_number": quote_number,
            "quote_title": quote_title,
            "quote_url": quote_url,
            "subtotal_pence": subtotal_pence,
            "vat_pence": vat_pence,
            "total_pence": total_pence,
            "valid_until": valid_until,
            "notes": notes,
            "line_items": line_items or [],
            "business_phone": business_phone,
        },
    )


def render_review_request(
    *,
    customer_name: str,
    business_name: str,
    review_url: str,
    service_description: str | None = None,
    unsubscribe_url: str | None = None,
) -> str:
    return render_email(
        "emails/review_request.html",
        {
            "subject": f"How did we do? — {business_name} would love your feedback",
            "customer_name": customer_name,
            "business_name": business_name,
            "review_url": review_url,
            "service_description": service_description,
            "unsubscribe_url": unsubscribe_url,
        },
    )


def render_invoice_sent(
    *,
    customer_name: str,
    business_name: str,
    invoice_number: str,
    invoice_title: str,
    subtotal_pence: int,
    vat_pence: int,
    total_pence: int,
    due_date: str | None = None,
    notes: str | None = None,
    stripe_payment_link: str | None = None,
    business_phone: str | None = None,
    business_email: str | None = None,
) -> str:
    return render_email(
        "emails/invoice_sent.html",
        {
            "subject": f"Invoice {invoice_number} from {business_name}",
            "customer_name": customer_name,
            "business_name": business_name,
            "invoice_number": invoice_number,
            "invoice_title": invoice_title,
            "subtotal_pence": subtotal_pence,
            "vat_pence": vat_pence,
            "total_pence": total_pence,
            "due_date": due_date,
            "notes": notes,
            "stripe_payment_link": stripe_payment_link,
            "business_phone": business_phone,
            "business_email": business_email,
        },
    )


def render_welcome(
    *,
    full_name: str,
    email: str,
    business_name: str,
    dashboard_url: str,
    trial_ends: str | None = None,
) -> str:
    return render_email(
        "emails/welcome.html",
        {
            "subject": f"Welcome to CustomerFlow AI — {business_name}",
            "full_name": full_name,
            "email": email,
            "business_name": business_name,
            "dashboard_url": dashboard_url,
            "trial_ends": trial_ends,
        },
    )


def render_password_reset(
    *,
    full_name: str | None,
    email: str,
    reset_url: str,
    expires_in_minutes: int = 30,
    request_ip: str | None = None,
    request_at: str | None = None,
) -> str:
    return render_email(
        "emails/password_reset.html",
        {
            "subject": "Reset your CustomerFlow AI password",
            "full_name": full_name,
            "email": email,
            "reset_url": reset_url,
            "expires_in_minutes": expires_in_minutes,
            "request_ip": request_ip,
            "request_at": request_at,
        },
    )


def render_magic_link(
    *,
    full_name: str | None,
    email: str,
    magic_url: str,
    expires_in_minutes: int = 15,
) -> str:
    return render_email(
        "emails/magic_link.html",
        {
            "subject": "Your CustomerFlow AI sign-in link",
            "full_name": full_name,
            "email": email,
            "magic_url": magic_url,
            "expires_in_minutes": expires_in_minutes,
        },
    )


def render_booking_reminder(
    *,
    customer_name: str,
    business_name: str,
    booking_date: str,
    start_time: str,
    window_label: str = "24h",
    service_description: str | None = None,
    staff_name: str | None = None,
    location: str | None = None,
    notes: str | None = None,
    reschedule_url: str | None = None,
    business_phone: str | None = None,
) -> str:
    label = "in 1 hour" if window_label == "1h" else "tomorrow"
    return render_email(
        "emails/booking_reminder.html",
        {
            "subject": f"Reminder: your booking with {business_name} {label}",
            "customer_name": customer_name,
            "business_name": business_name,
            "booking_date": booking_date,
            "start_time": start_time,
            "window_label": window_label,
            "service_description": service_description,
            "staff_name": staff_name,
            "location": location,
            "notes": notes,
            "reschedule_url": reschedule_url,
            "business_phone": business_phone,
        },
    )


def render_quote_accepted(
    *,
    customer_name: str,
    business_name: str,
    quote_number: str,
    quote_title: str,
    total_pence: int,
    deposit_required: int | None = None,
    invoice_url: str | None = None,
    business_phone: str | None = None,
) -> str:
    return render_email(
        "emails/quote_accepted.html",
        {
            "subject": f"Quote {quote_number} accepted — {business_name}",
            "customer_name": customer_name,
            "business_name": business_name,
            "quote_number": quote_number,
            "quote_title": quote_title,
            "total_pence": total_pence,
            "deposit_required": deposit_required,
            "invoice_url": invoice_url,
            "business_phone": business_phone,
        },
    )


def render_quote_declined(
    *,
    customer_name: str,
    business_name: str,
    quote_number: str,
    decline_reason: str | None = None,
    business_phone: str | None = None,
) -> str:
    return render_email(
        "emails/quote_declined.html",
        {
            "subject": f"Quote {quote_number} update — {business_name}",
            "customer_name": customer_name,
            "business_name": business_name,
            "quote_number": quote_number,
            "decline_reason": decline_reason,
            "business_phone": business_phone,
        },
    )


def render_invoice_paid(
    *,
    customer_name: str,
    business_name: str,
    invoice_number: str,
    invoice_title: str | None,
    amount_paid_pence: int,
    paid_at: str,
    payment_method: str | None = None,
    receipt_url: str | None = None,
    review_url: str | None = None,
    business_email: str | None = None,
) -> str:
    return render_email(
        "emails/invoice_paid.html",
        {
            "subject": f"Payment received — invoice {invoice_number}",
            "customer_name": customer_name,
            "business_name": business_name,
            "invoice_number": invoice_number,
            "invoice_title": invoice_title,
            "amount_paid_pence": amount_paid_pence,
            "paid_at": paid_at,
            "payment_method": payment_method,
            "receipt_url": receipt_url,
            "review_url": review_url,
            "business_email": business_email,
        },
    )


def render_invoice_overdue(
    *,
    customer_name: str,
    business_name: str,
    invoice_number: str,
    amount_due_pence: int,
    due_date: str,
    days_overdue: int,
    pay_url: str | None = None,
    business_phone: str | None = None,
) -> str:
    return render_email(
        "emails/invoice_overdue.html",
        {
            "subject": f"Payment reminder — invoice {invoice_number}",
            "customer_name": customer_name,
            "business_name": business_name,
            "invoice_number": invoice_number,
            "amount_due_pence": amount_due_pence,
            "due_date": due_date,
            "days_overdue": days_overdue,
            "pay_url": pay_url,
            "business_phone": business_phone,
        },
    )


def render_trial_auto_leads_ending(
    *,
    full_name: str,
    business_name: str,
    days_left: int = 1,
    leads_per_day: int = 2,
    trial_days: int = 7,
    upgrade_url: str,
    leads_url: str,
) -> str:
    return render_email(
        "emails/trial_auto_leads_ending.html",
        {
            "subject": "Your free daily leads end tomorrow",
            "full_name": full_name,
            "business_name": business_name,
            "days_left": days_left,
            "leads_per_day": leads_per_day,
            "trial_days": trial_days,
            "upgrade_url": upgrade_url,
            "leads_url": leads_url,
        },
    )


def render_trial_expiry(
    *,
    full_name: str,
    business_name: str,
    trial_end_date: str,
    days_remaining: int,
    upgrade_url: str,
    recommended_plan: str | None = "Growth",
    recommended_price: str | None = "149",
    leads_captured: int | None = None,
    reviews_collected: int | None = None,
) -> str:
    return render_email(
        "emails/trial_expiry.html",
        {
            "subject": f"Your CustomerFlow AI trial ends in {days_remaining} day{'s' if days_remaining != 1 else ''}",
            "full_name": full_name,
            "business_name": business_name,
            "trial_end_date": trial_end_date,
            "days_remaining": days_remaining,
            "upgrade_url": upgrade_url,
            "recommended_plan": recommended_plan,
            "recommended_price": recommended_price,
            "leads_captured": leads_captured,
            "reviews_collected": reviews_collected,
        },
    )
