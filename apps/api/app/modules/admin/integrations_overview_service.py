"""Cross-tenant integrations snapshot for super-admin monitoring."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.deletion import active_tenants_filter
from app.modules.integrations.models import (
    GoogleBusinessReview,
    TenantGoogleConnection,
    TenantGoogleCredentials,
    TenantGoogleSyncLog,
    TenantSocialChannel,
    TenantSocialWebhookLog,
)
from app.modules.tenants.models import Tenant


def _onboarding(raw: dict | None) -> dict[str, bool]:
    data = raw or {}
    return {
        "google_connected": bool(data.get("google_connected")),
        "social_connected": bool(data.get("social_connected")),
        "skipped": bool(data.get("skipped")),
    }


def _health_flags(
    *,
    onboarding: dict[str, bool],
    platform_connected: bool,
    platform_has_oauth: bool,
    platform_has_location: bool,
    credentials_status: str | None,
    credentials_expires_at: datetime | None,
    channels: list[dict],
    last_sync_status: str | None,
    webhook_failures_7d: int,
    now: datetime,
) -> list[str]:
    flags: list[str] = []
    if onboarding["google_connected"] and not platform_connected and credentials_status != "connected":
        flags.append("onboarding_google_mismatch")
    if onboarding["social_connected"] and not any(c["status"] == "connected" for c in channels):
        flags.append("onboarding_social_mismatch")
    if platform_has_oauth and not platform_has_location:
        flags.append("google_platform_no_location")
    if credentials_status == "expired":
        flags.append("google_credentials_expired")
    elif credentials_status == "connected" and credentials_expires_at:
        if credentials_expires_at <= now + timedelta(hours=24):
            flags.append("google_token_expiring")
    if any(c["status"] == "pending" for c in channels):
        flags.append("social_pending")
    if last_sync_status == "failed":
        flags.append("google_sync_failed")
    if webhook_failures_7d > 0:
        flags.append("social_webhook_failures")
    return flags


async def snapshot_integrations_overview(db: AsyncSession) -> dict:
    """Return platform totals plus one row per non-archived tenant."""
    now = datetime.now(timezone.utc)
    failures_cutoff_7d = now - timedelta(days=7)
    failures_cutoff_24h = now - timedelta(hours=24)

    tenants = (
        await db.execute(
            select(Tenant)
            .where(active_tenants_filter())
            .order_by(Tenant.name)
        )
    ).scalars().all()
    if not tenants:
        return {
            "totals": {
                "tenants_total": 0,
                "tenants_with_google_platform": 0,
                "tenants_with_google_credentials": 0,
                "tenants_with_any_social_channel": 0,
                "tenants_with_connected_social": 0,
                "onboarding_skipped": 0,
                "google_sync_failures_24h": 0,
                "social_webhook_failures_24h": 0,
            },
            "tenants": [],
        }

    tid_list = [t.id for t in tenants]

    google_by_tenant: dict[uuid.UUID, TenantGoogleConnection] = {
        row.tenant_id: row
        for row in (
            await db.execute(
                select(TenantGoogleConnection).where(TenantGoogleConnection.tenant_id.in_(tid_list))
            )
        ).scalars()
    }
    creds_by_tenant: dict[uuid.UUID, TenantGoogleCredentials] = {
        row.tenant_id: row
        for row in (
            await db.execute(
                select(TenantGoogleCredentials).where(TenantGoogleCredentials.tenant_id.in_(tid_list))
            )
        ).scalars()
    }

    channels_by_tenant: dict[uuid.UUID, list[TenantSocialChannel]] = defaultdict(list)
    for ch in (
        await db.execute(
            select(TenantSocialChannel)
            .where(TenantSocialChannel.tenant_id.in_(tid_list))
            .order_by(TenantSocialChannel.channel_type)
        )
    ).scalars():
        channels_by_tenant[ch.tenant_id].append(ch)

    review_counts: dict[uuid.UUID, int] = {
        tid: int(count)
        for tid, count in (
            await db.execute(
                select(GoogleBusinessReview.tenant_id, func.count(GoogleBusinessReview.id))
                .where(GoogleBusinessReview.tenant_id.in_(tid_list))
                .group_by(GoogleBusinessReview.tenant_id)
            )
        ).all()
    }

    latest_sync: dict[uuid.UUID, TenantGoogleSyncLog] = {}
    for log in (
        await db.execute(
            select(TenantGoogleSyncLog)
            .where(TenantGoogleSyncLog.tenant_id.in_(tid_list))
            .order_by(TenantGoogleSyncLog.synced_at.desc())
        )
    ).scalars():
        if log.tenant_id not in latest_sync:
            latest_sync[log.tenant_id] = log

    latest_webhook: dict[uuid.UUID, TenantSocialWebhookLog] = {}
    for log in (
        await db.execute(
            select(TenantSocialWebhookLog)
            .where(TenantSocialWebhookLog.tenant_id.in_(tid_list))
            .order_by(TenantSocialWebhookLog.processed_at.desc())
        )
    ).scalars():
        if log.tenant_id not in latest_webhook:
            latest_webhook[log.tenant_id] = log

    last_webhook_by_channel: dict[tuple[uuid.UUID, str], datetime] = {}
    for tid, channel_type, processed_at in (
        await db.execute(
            select(
                TenantSocialWebhookLog.tenant_id,
                TenantSocialWebhookLog.channel_type,
                func.max(TenantSocialWebhookLog.processed_at),
            )
            .where(TenantSocialWebhookLog.tenant_id.in_(tid_list))
            .group_by(TenantSocialWebhookLog.tenant_id, TenantSocialWebhookLog.channel_type)
        )
    ).all():
        last_webhook_by_channel[(tid, channel_type)] = processed_at

    webhook_failures_7d: dict[uuid.UUID, int] = {
        tid: int(count)
        for tid, count in (
            await db.execute(
                select(TenantSocialWebhookLog.tenant_id, func.count(TenantSocialWebhookLog.id))
                .where(
                    TenantSocialWebhookLog.tenant_id.in_(tid_list),
                    TenantSocialWebhookLog.processed_at >= failures_cutoff_7d,
                    TenantSocialWebhookLog.status.in_(("failed", "rejected")),
                )
                .group_by(TenantSocialWebhookLog.tenant_id)
            )
        ).all()
    }

    google_sync_failures_24h = int(
        (
            await db.execute(
                select(func.count(TenantGoogleSyncLog.id)).where(
                    TenantGoogleSyncLog.synced_at >= failures_cutoff_24h,
                    TenantGoogleSyncLog.status == "failed",
                )
            )
        ).scalar()
        or 0
    )
    social_webhook_failures_24h = int(
        (
            await db.execute(
                select(func.count(TenantSocialWebhookLog.id)).where(
                    TenantSocialWebhookLog.processed_at >= failures_cutoff_24h,
                    TenantSocialWebhookLog.status.in_(("failed", "rejected")),
                )
            )
        ).scalar()
        or 0
    )

    totals = {
        "tenants_total": len(tenants),
        "tenants_with_google_platform": 0,
        "tenants_with_google_credentials": 0,
        "tenants_with_any_social_channel": 0,
        "tenants_with_connected_social": 0,
        "onboarding_skipped": 0,
        "google_sync_failures_24h": google_sync_failures_24h,
        "social_webhook_failures_24h": social_webhook_failures_24h,
    }

    rows: list[dict] = []
    for tenant in tenants:
        onboarding = _onboarding(tenant.integrations_onboarding)
        if onboarding["skipped"]:
            totals["onboarding_skipped"] += 1

        conn = google_by_tenant.get(tenant.id)
        platform_has_location = bool(conn and conn.google_location_name)
        platform_connected = platform_has_location
        platform_has_oauth = conn is not None

        creds = creds_by_tenant.get(tenant.id)
        credentials_registered = creds is not None
        credentials_status = creds.status if creds else None
        credentials_expires_at = creds.expires_at if creds else None

        if platform_connected:
            totals["tenants_with_google_platform"] += 1
        if credentials_registered:
            totals["tenants_with_google_credentials"] += 1

        channels = channels_by_tenant.get(tenant.id, [])
        if channels:
            totals["tenants_with_any_social_channel"] += 1
        connected_channels = [c for c in channels if c.status == "connected"]
        if connected_channels:
            totals["tenants_with_connected_social"] += 1

        platform_summaries = [
            {
                "channel_type": ch.channel_type,
                "status": ch.status,
                "connected_at": ch.connected_at,
                "last_webhook_at": last_webhook_by_channel.get((tenant.id, ch.channel_type)),
            }
            for ch in channels
        ]

        sync_log = latest_sync.get(tenant.id)
        webhook_log = latest_webhook.get(tenant.id)
        failures_7d = webhook_failures_7d.get(tenant.id, 0)

        rows.append({
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "tenant_slug": tenant.slug,
            "is_active": tenant.is_active,
            "integrations_onboarding": onboarding,
            "google": {
                "platform_connected": platform_connected,
                "platform_location_title": conn.location_title if conn else None,
                "platform_last_sync_at": conn.last_sync_at if conn else None,
                "credentials_registered": credentials_registered,
                "credentials_status": credentials_status,
                "credentials_expires_at": credentials_expires_at,
                "review_count": review_counts.get(tenant.id, 0),
                "last_sync_at": sync_log.synced_at if sync_log else None,
                "last_sync_type": sync_log.data_type if sync_log else None,
                "last_sync_status": sync_log.status if sync_log else None,
            },
            "social": {
                "channels_provisioned": len(channels),
                "channels_connected": len(connected_channels),
                "platforms": platform_summaries,
                "last_webhook_at": webhook_log.processed_at if webhook_log else None,
                "last_webhook_status": webhook_log.status if webhook_log else None,
                "webhook_failures_7d": failures_7d,
            },
            "health_flags": _health_flags(
                onboarding=onboarding,
                platform_connected=platform_connected,
                platform_has_oauth=platform_has_oauth,
                platform_has_location=platform_has_location,
                credentials_status=credentials_status,
                credentials_expires_at=credentials_expires_at,
                channels=platform_summaries,
                last_sync_status=sync_log.status if sync_log else None,
                webhook_failures_7d=failures_7d,
                now=now,
            ),
        })

    return {"totals": totals, "tenants": rows}
