"""Super-admin soft-delete helpers for tenants and platform users."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.auth.models import RefreshToken, User
from app.modules.tenants.models import Tenant, TenantMember

ARCHIVED_SLUG_MARKER = "-deleted-"


def active_users_filter():
    """SQLAlchemy criterion: user has not been soft-deleted."""
    return User.deleted_at.is_(None)


def active_tenants_filter():
    """Exclude tenants archived by super-admin delete."""
    return ~Tenant.slug.contains(ARCHIVED_SLUG_MARKER)


async def _revoke_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


async def delete_tenant(
    db: AsyncSession, tenant_id: uuid.UUID, *, permanent: bool = False
) -> dict:
    """Archive a tenant, or permanently remove it and tenant-scoped data."""
    if permanent:
        return await permanently_delete_tenant(db, tenant_id)

    # Soft-delete: deactivate, free slug, revoke member sessions.
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Tenant")

    pool_slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
    if tenant.slug == pool_slug:
        raise BadRequestException("Cannot delete the system lead pool tenant")

    tenant.is_active = False
    if "-deleted-" not in tenant.slug:
        tenant.slug = f"{tenant.slug[:80]}-deleted-{uuid.uuid4().hex[:8]}"
    db.add(tenant)

    member_rows = (
        await db.execute(
            select(TenantMember.user_id).where(TenantMember.tenant_id == tenant_id)
        )
    ).scalars().all()
    for uid in member_rows:
        await _revoke_user_sessions(db, uid)

    await db.commit()
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "message": f"{tenant.name} has been deleted (archived). Members can no longer access this workspace.",
    }


async def _purge_tenant_data(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Delete tenant-scoped application data (order: dependents first)."""
    from app.modules.ai_assistant.models import AIAssistantMessage, AIAssistantThread
    from app.modules.audit.models import AuditLog
    from app.modules.auth.models import ApiKey
    from app.modules.automation.models import Automation, AutomationRun, AutomationStep, MessageTemplate
    from app.modules.auto_replies.models import AutoReply
    from app.modules.billing.models import BillingInvoice, Subscription
    from app.modules.booking.models import AvailabilitySlot, Booking, Staff
    from app.modules.booking.enterprise_models import (
        BookingAbandonedSession,
        BookingCalendarConnection,
        BookingCustomerCredit,
        BookingNotificationQueue,
        BookingPackage,
        BookingPromoCode,
        BookingResource,
        BookingService,
        BookingSettings,
        StaffBlackout,
        StaffShift,
    )
    from app.modules.crm.models import Customer, Deal, DealActivity
    from app.modules.crm.pipeline_models import (
        CrmActivity,
        CrmAssignment,
        CrmAttachment,
        CrmCustomFieldDefinition,
        CrmCustomFieldValue,
        CrmDuplicateCandidate,
        CrmImportJob,
        CrmPipeline,
        CrmSavedFilter,
        CrmScoreRule,
        CrmStage,
        CrmTag,
        CrmTagAssignment,
    )
    from app.modules.gdpr.models import GdprRequest
    from app.modules.integrations.models import GoogleBusinessReview, TenantGoogleConnection
    from app.modules.landing_pages.models import LandingPage
    from app.modules.lead_marketplace.trial_models import TrialLeadDelivery
    from app.modules.leads.models import Lead, LeadRequest, LeadSource
    from app.modules.marketer.models import (
        AudienceResearchReport,
        CompetitorIntelligenceReport,
        MarketerFunnelBlueprint,
        MarketerQuota,
    )
    from app.modules.messaging.models import Conversation, Message
    from app.modules.notifications.models import Notification, NotificationPreference, PushSubscription
    from app.modules.outreach.models import OutreachCampaign, OutreachEnrolment, OutreachSend
    from app.modules.quotes_invoices.models import (
        Invoice,
        InvoiceItem,
        Payment,
        Quote,
        QuoteItem,
        QuoteTemplate,
    )
    from app.modules.rbac.models import TenantPermissionOverride
    from app.modules.reputation.models import Review, ReviewRequest
    from app.modules.segments.models import CustomerSegment
    from app.modules.social.models import (
        SocialAccount,
        SocialApprovalQueue,
        SocialBrandIdentity,
        SocialContentDraft,
        SocialPost,
        SocialPostingPreferences,
        SocialSampleUploads,
        SocialScheduleQueue,
    )
    from app.modules.tasks.models import Task
    from app.modules.tenants.models import Location
    from app.services.ai.models import AIUsageEvent

    tid = tenant_id
    automation_ids = select(Automation.id).where(Automation.tenant_id == tid)
    await db.execute(delete(AutomationStep).where(AutomationStep.automation_id.in_(automation_ids)))

    ordered_models = [
        Message,
        AutoReply,
        Conversation,
        OutreachSend,
        OutreachEnrolment,
        OutreachCampaign,
        AIAssistantMessage,
        AIAssistantThread,
        CrmCustomFieldValue,
        CrmTagAssignment,
        CrmAttachment,
        CrmActivity,
        CrmAssignment,
        CrmSavedFilter,
        CrmImportJob,
        CrmDuplicateCandidate,
        CrmCustomFieldDefinition,
        CrmTag,
        CrmScoreRule,
        CrmStage,
        CrmPipeline,
        DealActivity,
        Deal,
        TrialLeadDelivery,
        Lead,
        LeadRequest,
        LeadSource,
        Customer,
        Payment,
        Invoice,
        Quote,
        QuoteTemplate,
        Task,
        BookingNotificationQueue,
        BookingAbandonedSession,
        BookingCustomerCredit,
        BookingCalendarConnection,
        Booking,
        AvailabilitySlot,
        StaffShift,
        StaffBlackout,
        Staff,
        BookingPromoCode,
        BookingPackage,
        BookingResource,
        BookingService,
        BookingSettings,
        AutomationRun,
        Automation,
        MessageTemplate,
        ReviewRequest,
        Review,
        SocialPost,
        SocialContentDraft,
        SocialScheduleQueue,
        SocialApprovalQueue,
        SocialSampleUploads,
        SocialPostingPreferences,
        SocialBrandIdentity,
        SocialAccount,
        CustomerSegment,
        LandingPage,
        CompetitorIntelligenceReport,
        AudienceResearchReport,
        MarketerFunnelBlueprint,
        MarketerQuota,
        Notification,
        NotificationPreference,
        PushSubscription,
        BillingInvoice,
        Subscription,
        GdprRequest,
        GoogleBusinessReview,
        TenantGoogleConnection,
        ApiKey,
        TenantPermissionOverride,
        AIUsageEvent,
        AuditLog,
        Location,
    ]
    for model in ordered_models:
        await db.execute(delete(model).where(model.tenant_id == tid))


async def _hard_remove_tenant(db: AsyncSession, tenant: Tenant) -> None:
    """Remove tenant data and row (no commit)."""
    member_rows = (
        await db.execute(
            select(TenantMember.user_id).where(TenantMember.tenant_id == tenant.id)
        )
    ).scalars().all()
    for uid in member_rows:
        await _revoke_user_sessions(db, uid)
    await _purge_tenant_data(db, tenant.id)
    await db.execute(delete(TenantMember).where(TenantMember.tenant_id == tenant.id))
    await db.delete(tenant)


async def permanently_delete_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Hard-delete a tenant workspace and all tenant-scoped data."""
    tenant = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if not tenant:
        raise NotFoundException("Tenant")

    pool_slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
    if tenant.slug == pool_slug:
        raise BadRequestException("Cannot delete the system lead pool tenant")

    name = tenant.name
    await _hard_remove_tenant(db, tenant)
    await db.commit()
    return {
        "id": str(tenant_id),
        "name": name,
        "message": f"{name} and all workspace data were permanently deleted.",
    }


async def permanently_delete_platform_user(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Hard-delete a platform user and owned/managed tenant workspaces."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise NotFoundException("User")
    if user.is_superadmin:
        raise BadRequestException("Cannot delete a super-admin account")

    pool_slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
    email = user.email
    user_type = user.user_type or "tenant"

    if user.user_type == "freelancer":
        tenants = (
            await db.execute(
                select(Tenant).where(Tenant.owner_user_id == user.id, Tenant.is_managed_client == True)
            )
        ).scalars().all()
    else:
        tenants = (
            await db.execute(
                select(Tenant)
                .join(TenantMember, TenantMember.tenant_id == Tenant.id)
                .where(
                    TenantMember.user_id == user.id,
                    TenantMember.role == "owner",
                    Tenant.is_managed_client == False,
                )
            )
        ).scalars().all()

    removed_tenants = 0
    for t in list(tenants):
        if t.slug == pool_slug:
            continue
        await _hard_remove_tenant(db, t)
        removed_tenants += 1

    from app.modules.auth.otp_models import PendingSignup
    from app.modules.billing.models import FreelancerBilling

    from app.modules.ai_assistant.models import AIAssistantThread
    from app.modules.auth.models import ApiKey, MagicLinkToken

    await db.execute(delete(FreelancerBilling).where(FreelancerBilling.user_id == user.id))
    await db.execute(delete(ApiKey).where(ApiKey.user_id == user.id))
    await db.execute(delete(MagicLinkToken).where(MagicLinkToken.email == email))
    await db.execute(delete(AIAssistantThread).where(AIAssistantThread.user_id == user.id))
    await db.execute(
        update(Tenant).where(Tenant.owner_user_id == user.id).values(owner_user_id=None)
    )
    await _revoke_user_sessions(db, user.id)
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.execute(delete(TenantMember).where(TenantMember.user_id == user.id))
    await db.execute(delete(PendingSignup).where(PendingSignup.email == email))
    await db.delete(user)
    await db.commit()

    kind = "freelancer" if user_type == "freelancer" else "user"
    return {
        "id": str(user_id),
        "email": email,
        "user_type": user_type,
        "removed_tenants": removed_tenants,
        "message": f"{kind.capitalize()} {email} permanently deleted.",
    }


async def delete_freelancer(
    db: AsyncSession, user_id: uuid.UUID, *, permanent: bool = False
) -> dict:
    """Soft-delete a freelancer account and archive managed client workspaces."""
    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not user:
        raise NotFoundException("Freelancer")
    if user.user_type != "freelancer":
        raise BadRequestException("Account is not a freelancer")
    if permanent:
        return await permanently_delete_platform_user(db, user_id)
    return await delete_platform_user(db, user_id)


async def delete_platform_user(
    db: AsyncSession, user_id: uuid.UUID, *, permanent: bool = False
) -> dict:
    if permanent:
        return await permanently_delete_platform_user(db, user_id)
    """Soft-delete a tenant or freelancer account."""
    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if not user:
        raise NotFoundException("User")
    if user.is_superadmin:
        raise BadRequestException("Cannot delete a super-admin account")

    now = datetime.now(timezone.utc)
    user.deleted_at = now
    db.add(user)
    await _revoke_user_sessions(db, user.id)

    archived_tenants = 0
    if user.user_type == "freelancer":
        managed = (
            await db.execute(
                select(Tenant).where(Tenant.owner_user_id == user.id, Tenant.is_managed_client == True)
            )
        ).scalars().all()
        for t in managed:
            t.is_active = False
            if "-deleted-" not in t.slug:
                t.slug = f"{t.slug[:80]}-deleted-{uuid.uuid4().hex[:8]}"
            db.add(t)
            archived_tenants += 1
    elif user.user_type == "tenant":
        owned = (
            await db.execute(
                select(Tenant)
                .join(TenantMember, TenantMember.tenant_id == Tenant.id)
                .where(
                    TenantMember.user_id == user.id,
                    TenantMember.role == "owner",
                    Tenant.is_managed_client == False,
                )
            )
        ).scalars().all()
        pool_slug = (settings.MARKETPLACE_POOL_TENANT_SLUG or "lead-pool-system").strip()
        for t in owned:
            if t.slug == pool_slug:
                continue
            t.is_active = False
            if "-deleted-" not in t.slug:
                t.slug = f"{t.slug[:80]}-deleted-{uuid.uuid4().hex[:8]}"
            db.add(t)
            archived_tenants += 1

    await db.commit()
    kind = "freelancer" if user.user_type == "freelancer" else "user"
    return {
        "id": str(user.id),
        "email": user.email,
        "user_type": user.user_type,
        "archived_tenants": archived_tenants,
        "message": f"{kind.capitalize()} {user.email} deleted. They can no longer sign in.",
    }
