# Social Integrations — Zapier / Make / N8N

CustomerFlow does **not** own OAuth for Facebook, Instagram, TikTok, or LinkedIn. Tenants connect via **Zapier**, **Make**, or **N8N** using webhooks.

## Setup (per platform)

1. Dashboard: **Integrations → Social (Zapier / Make)**.
2. Click **Connect {Platform} via Zapier**.
3. Copy:
   - **Webhook URL**
   - **API Key**
   - **Zapier key** / **Make key** (reference labels for your automation)
4. In Zapier/Make, create a trigger on the social platform and add a **Webhooks by Zapier → POST** (or Make equivalent) action pointing at the Webhook URL.

## Inbound Payload Schema

POST JSON to the webhook URL with query param `?key={api_key}`.

Optional header: `X-CF-Signature` — HMAC-SHA256 hex of raw body using the channel API secret.

```json
{
  "event_type": "message",
  "platform": "facebook",
  "sender_name": "Jane Doe",
  "sender_email": "jane@example.com",
  "sender_phone": "+447700900123",
  "message": "Hi, I have a question",
  "external_id": "fb-thread-123",
  "tags": ["inbox", "facebook"]
}
```

### event_type values

| Value | Behavior |
|-------|----------|
| `message` | Unified inbox + CRM contact |
| `comment` | Inbox thread |
| `lead` | CRM contact + automation `lead.received` |
| `mention` | Inbox thread |
| `post_status` | Logged only (publish confirmation) |

## Outbound Posting

POST (authenticated tenant session):

```
POST /api/v1/integrations/social/post
{
  "platform": "facebook",
  "content": "New offer this week!",
  "media_url": "https://example.com/image.jpg"
}
```

CustomerFlow forwards a webhook-style payload to the tenant's configured hook URL for Zapier/Make to publish.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/integrations/social/channels` | List channels |
| POST | `/api/v1/integrations/social/channels/{platform}` | Provision channel |
| POST | `/api/v1/integrations/social/post` | Outbound post |
| POST | `/api/v1/integrations/webhooks/social/{channel_id}?key=` | Inbound webhook (public) |

Supported platforms: `facebook`, `instagram`, `tiktok`, `linkedin`.

## Logs

Inbound and outbound events are stored in `tenant_social_webhook_logs`.

## Testing

See `apps/api/tests/test_integrations_tenant_oauth.py` — `test_social_webhook_creates_inbox_message`.
