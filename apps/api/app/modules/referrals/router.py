"""Referral API — mounted at app prefix `/api` → `/api/referrals/*`."""
from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    SuperAdmin,
    bearer_scheme,
    get_current_user,
    get_current_tenant,
)
from app.core.exceptions import BadRequestException, ForbiddenException
from app.modules.auth.models import User
from app.modules.referrals import schemas as rs
from app.modules.referrals import service as referral_svc

router = APIRouter(prefix="/referrals", tags=["Referrals"])
_ACCESS_COOKIE = "access_token"


def _program_from_orm(p: Any) -> rs.ProgramResponse:
    return rs.ProgramResponse(
        id=p.id,
        type=p.type,
        owner_id=p.owner_id,
        reward_amount=float(p.reward_amount),
        reward_type=p.reward_type,
        reward_delivery_method=p.reward_delivery_method,
        rules=dict(p.rules or {}),
        status=p.status,
        created_at=p.created_at,
    )


def _link_from_orm(link: Any) -> rs.LinkResponse:
    return rs.LinkResponse(
        id=link.id,
        user_id=link.user_id,
        program_id=link.program_id,
        ref_code=link.ref_code,
        ref_link=link.ref_link,
        qr_code_url=link.qr_code_url,
        created_at=link.created_at,
    )


def _payout_from_orm(row: Any) -> rs.PayoutResponse:
    return rs.PayoutResponse(
        id=row.id,
        event_id=row.event_id,
        referrer_user_id=row.referrer_user_id,
        amount=float(row.amount),
        payout_method=row.payout_method,
        payout_status=row.payout_status,
        created_at=row.created_at,
    )


@router.post("/programs/create", response_model=rs.ProgramResponse)
async def post_programs_create(
    body: rs.ProgramCreateBody,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    if body.type == "global_saas":
        if not user.is_superadmin:
            raise ForbiddenException("Super-admin access required")
        p = await referral_svc.create_program(
            db,
            owner_id=None,
            type_=body.type,
            reward_amount=body.reward_amount,
            reward_type=body.reward_type,
            reward_delivery_method=body.reward_delivery_method,
            rules=body.rules,
        )
        return _program_from_orm(p)
    u, tenant, role = await get_current_tenant(credentials, db, cookie_token)
    if role != "owner":
        raise ForbiddenException("Owner access required")
    merged = dict(body.rules or {})
    merged["tenant_id"] = str(tenant.id)
    p = await referral_svc.create_program(
        db,
        owner_id=u.id,
        type_=body.type,
        reward_amount=body.reward_amount,
        reward_type=body.reward_type,
        reward_delivery_method=body.reward_delivery_method,
        rules=merged,
    )
    return _program_from_orm(p)


@router.get("/programs/{program_id}", response_model=rs.ProgramResponse)
async def get_program_route(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    p = await referral_svc.get_program(db, program_id)
    if user.is_superadmin:
        return _program_from_orm(p)
    if p.owner_id == user.id:
        return _program_from_orm(p)
    if p.type == "tradesman" and (p.rules or {}).get("tenant_id"):
        u, tenant, role = await get_current_tenant(credentials, db, cookie_token)
        if str(tenant.id) == str(p.rules.get("tenant_id")) and role == "owner":
            return _program_from_orm(p)
    raise ForbiddenException("Cannot view this program")


@router.post("/programs/{program_id}/submit_for_approval", response_model=rs.ProgramResponse)
async def post_submit_for_approval(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    p = await referral_svc.submit_for_approval(db, program_id, actor_user_id=user.id)
    return _program_from_orm(p)


@router.post("/programs/{program_id}/approve", response_model=rs.ProgramResponse)
async def post_program_approve(
    program_id: UUID,
    body: rs.ApproveBody,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(SuperAdmin),
):
    p = await referral_svc.approve_program(
        db, program_id, reward_amount=body.reward_amount, reason=body.reason
    )
    return _program_from_orm(p)


@router.post("/programs/{program_id}/reject", response_model=rs.ProgramResponse)
async def post_program_reject(
    program_id: UUID,
    body: rs.RejectBody,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(SuperAdmin),
):
    p = await referral_svc.reject_program(db, program_id, body.reason)
    return _program_from_orm(p)


@router.post("/links/generate", response_model=rs.LinkResponse)
async def post_links_generate(
    body: rs.LinkGenerateBody,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    await referral_svc.ensure_can_generate_link(
        db,
        program_id=body.program_id,
        acting_user_id=user.id,
        credentials=credentials,
        cookie_token=cookie_token,
    )
    link = await referral_svc.generate_link(db, program_id=body.program_id, user_id=user.id)
    return _link_from_orm(link)


@router.get("/links/{user_id}", response_model=list[rs.LinkResponse])
async def get_links_for_user_route(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    if user.id != user_id and not user.is_superadmin:
        raise ForbiddenException("Cannot list links for another user")
    rows = await referral_svc.list_links_for_user(db, user_id)
    return [_link_from_orm(x) for x in rows]


@router.post("/events/log", response_model=rs.EventLogResponse)
async def post_events_log(body: rs.EventLogBody, db: AsyncSession = Depends(get_db)):
    ev = await referral_svc.log_event_clicked(db, ref_code=body.ref_code)
    return rs.EventLogResponse(id=ev.id, status=ev.status)


@router.post("/events/update_status", response_model=rs.EventLogResponse)
async def post_events_update_status(
    body: rs.EventUpdateStatusBody,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    await get_current_user(credentials, db, cookie_token)
    ev = await referral_svc.update_event_status(db, event_id=body.event_id, new_status=body.status)
    return rs.EventLogResponse(id=ev.id, status=ev.status)


@router.post("/events/reward", response_model=rs.EventLogResponse)
async def post_events_reward(
    body: rs.EventRewardBody,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(SuperAdmin),
):
    ev, _p = await referral_svc.issue_reward(db, event_id=body.event_id)
    return rs.EventLogResponse(id=ev.id, status=ev.status)


@router.get("/referrer/{referrer_id}/dashboard", response_model=rs.ReferrerDashboardResponse)
async def get_referrer_dashboard(
    referrer_id: UUID,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    if user.id != referrer_id and not user.is_superadmin:
        raise ForbiddenException("Cannot view this dashboard")
    data = await referral_svc.referrer_dashboard(db, referrer_id=referrer_id)
    return rs.ReferrerDashboardResponse(**data)


@router.post("/payouts/request", response_model=rs.PayoutResponse)
async def post_payouts_request(
    body: rs.PayoutRequestBody,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    if body.event_id is None:
        raise BadRequestException("event_id is required")
    row = await referral_svc.request_payout(
        db,
        referrer_user_id=user.id,
        amount=body.amount,
        payout_method=body.payout_method,
        event_id=body.event_id,
    )
    return _payout_from_orm(row)


@router.get("/payouts/{payout_id}", response_model=rs.PayoutResponse)
async def get_payout_route(
    payout_id: UUID,
    db: AsyncSession = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    cookie_token: Annotated[str | None, Cookie(alias=_ACCESS_COOKIE)] = None,
):
    user = await get_current_user(credentials, db, cookie_token)
    row = await referral_svc.get_payout(db, payout_id)
    if row.referrer_user_id != user.id and not user.is_superadmin:
        raise ForbiddenException("Cannot view this payout")
    return _payout_from_orm(row)
