# Integration Webhooks

## Social Webhook Receiver

**Path:** `POST /api/v1/integrations/webhooks/social/{channel_id}?key={api_key}`

**Auth:**

1. Query param `key` must match the channel's `api_key`.
2. Optional: `X-CF-Signature` header = HMAC-SHA256 hex of raw request body using the channel secret (stored encrypted).

**Handler:** `apps/api/app/modules/integrations/webhooks/social_webhook_handler.py`

### Processing pipeline

1. Resolve channel by ID + API key.
2. Verify signature (if provided).
3. Validate payload (`SocialWebhookPayload`).
4. Log to `tenant_social_webhook_logs`.
5. Map via `inbound_mapper.ingest_social_webhook`:
   - Create/update CRM contact
   - Insert `conversations` + `messages`
   - Enqueue `trigger_automation_for_event`
6. Mark channel `status=connected`.

## Unified Inbox Channels

| Source | `conversations.channel` |
|--------|---------------------------|
| Google GMB | `google_gmb` |
| Facebook | `facebook` |
| Instagram | `instagram` |
| TikTok | `tiktok` |
| LinkedIn | `linkedin` |
| SMS / Email / WhatsApp | existing channels unchanged |

## CRM Automation Events

| Trigger | `event_type` |
|---------|----------------|
| Inbound social/GMB message | `message.received` |
| Social lead webhook | `lead.received` |

Payload includes `channel`, `customer_id`, `message_id`, `source`.

## Testing Webhooks Locally

```bash
# Provision channel (authenticated)
curl -X POST http://127.0.0.1:8000/api/v1/integrations/social/channels/facebook \
  -H "Authorization: Bearer $TOKEN"

# Send test webhook
curl -X POST "http://127.0.0.1:8000/api/v1/integrations/webhooks/social/{channel_id}?key={api_key}" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"message","platform":"facebook","sender_name":"Test","message":"Hello"}'
```

## Sync Logs

- Google: `tenant_google_sync_logs`
- Social: `tenant_social_webhook_logs`

Query by `tenant_id` for audit and QA.
