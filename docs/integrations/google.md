# Google Business Profile — Tenant-Owned OAuth

CustomerFlow supports **tenant-owned Google OAuth**. Each tenant registers their own Google Cloud OAuth client. CustomerFlow only hosts the redirect URI and syncs data — it never needs Google app verification.

## Flow

1. Tenant creates a Google Cloud project and OAuth 2.0 **Web application** credentials.
2. In the dashboard: **Integrations → Google Business Profile**.
3. Paste **Client ID** and **Client Secret**.
4. Copy the **Redirect URI** shown (readonly) into Google Cloud authorized redirect URIs.
5. Click **Connect Google Business Profile** — OAuth runs against the tenant's app.
6. Tokens are encrypted at rest using `INTEGRATIONS_TOKEN_ENCRYPTION_KEY`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/integrations/google/register-credentials` | Save tenant Client ID + Secret |
| GET | `/api/v1/integrations/google/credentials` | Credential + connection status |
| GET | `/api/v1/integrations/google/auth-url` | OAuth authorization URL |
| GET | `/api/v1/integrations/google/oauth-callback` | OAuth redirect (public) |
| POST | `/api/v1/integrations/google/refresh-token` | Refresh access token |
| GET | `/api/v1/integrations/google/reviews/sync` | Sync reviews |
| GET | `/api/v1/integrations/google/messages/sync` | Sync GMB messages into inbox |
| GET | `/api/v1/integrations/google/posts/sync` | Sync local posts |
| GET | `/api/v1/integrations/google/photos/sync` | Sync media |
| GET | `/api/v1/integrations/google/analytics/sync` | Sync insights snapshot |

## Environment Variables

```env
INTEGRATIONS_TOKEN_ENCRYPTION_KEY=   # Required — Fernet-compatible key
PUBLIC_API_BASE_URL=https://customerflowai.online   # Used for redirect + webhook URLs
```

Platform-owned Google OAuth (`GOOGLE_CLIENT_ID`, etc.) remains available for legacy/server-managed connections.

## Sync Logs

All sync operations write to `tenant_google_sync_logs` with `data_type`: `reviews`, `messages`, `posts`, `photos`, `analytics`.

## Background Jobs

ARQ cron jobs (see `apps/api/app/modules/integrations/jobs/google_jobs.py`):

- Reviews — every 30 min (via existing `sync_all_google_reviews`)
- Messages — :10 and :40
- Posts — 01:00 and 13:00 UTC
- Photos — 02:00 and 14:00 UTC
- Analytics — 03:00 UTC

## Testing

```bash
cd apps/api && pytest tests/test_integrations_tenant_oauth.py -q
```
