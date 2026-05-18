# CustomerFlow AI Worker

The background worker shares the API codebase. There is **no separate image**:
the `worker` service in `infra/docker-compose.yml` is built from
`apps/api/Dockerfile` with the entrypoint overridden to run ARQ.

```yaml
worker:
  build:
    context: ../apps/api
    dockerfile: Dockerfile
  command: ["uv", "run", "arq", "app.workers.worker_settings.WorkerSettings"]
```

Jobs handled (see `apps/api/app/workers/worker_settings.py`):

- `send_sms_task`
- `send_email_task`
- `process_inbound_sms`
- `handle_missed_call`
- `trigger_automation_for_event`
- `run_automation_step`
- `send_review_request`
- `generate_social_post`
- `publish_social_post`
- `sync_stripe_subscription`
- `weekly_performance_report`
- `gdpr_export`
- `gdpr_erase`
