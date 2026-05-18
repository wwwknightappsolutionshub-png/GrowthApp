"""WhatsApp CRM module.

Surfaces:

- A dedicated inbox view of all WhatsApp conversations for a tenant.
- AI assist endpoints (sentiment, summarise, suggested reply) that wrap the
  existing AI router with WhatsApp-specific prompts.
- Outbound send via the existing messaging service (channel='whatsapp').
"""
