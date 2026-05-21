"""ARQ Worker configuration."""
from arq import cron

from app.workers.queue import get_redis_settings
from app.workers.tasks.messaging import (
    send_sms_task,
    send_email_task,
    send_whatsapp_task,
    process_inbound_sms,
    process_inbound_whatsapp,
    handle_missed_call,
)
from app.workers.tasks.automation import trigger_automation_for_event, run_automation_step
from app.workers.tasks.reputation import send_review_request
from app.workers.tasks.social import generate_social_post, publish_social_post
from app.workers.tasks.billing import sync_stripe_subscription
from app.workers.tasks.reports import weekly_performance_report
from app.workers.tasks.gdpr import gdpr_export, gdpr_erase
from app.workers.tasks.tasks import send_task_reminder, sweep_overdue_task_reminders
from app.workers.tasks.ai import backfill_lead_scores_task, score_lead_task
from app.workers.tasks.outreach import process_outreach_dispatch
from app.workers.tasks.ai_scraper import run_ai_scraper_task
from app.workers.tasks.ai_scraper_scheduler import enqueue_due_scraper_tasks
from app.services.ai_scraper.task_runner import run_crawler_task
from app.workers.tasks.ai_social import run_ai_social_scheduler
from app.workers.tasks.google_integrations import sync_all_google_reviews
from app.workers.tasks.trial_leads import assign_daily_trial_leads, send_trial_lead_ending_reminders
from app.workers.tasks.booking_notifications import process_booking_notification_queue


class WorkerSettings:
    redis_settings = get_redis_settings()
    functions = [
        send_sms_task,
        send_email_task,
        send_whatsapp_task,
        process_inbound_sms,
        process_inbound_whatsapp,
        handle_missed_call,
        trigger_automation_for_event,
        run_automation_step,
        send_review_request,
        generate_social_post,
        publish_social_post,
        sync_stripe_subscription,
        weekly_performance_report,
        gdpr_export,
        gdpr_erase,
        send_task_reminder,
        sweep_overdue_task_reminders,
        score_lead_task,
        backfill_lead_scores_task,
        process_outreach_dispatch,
        run_ai_scraper_task,
        run_crawler_task,
        enqueue_due_scraper_tasks,
        run_ai_social_scheduler,
        assign_daily_trial_leads,
        send_trial_lead_ending_reminders,
        process_booking_notification_queue,
    ]
    # Cron jobs:
    #   * Every 5 minutes: sweep for missed task reminders.
    #   * Every 5 minutes: dispatch due outreach steps.
    #   * Top of every hour: backfill unscored leads (50 per tenant per hour).
    #   * Every 1 minute: AI Social scheduler — publish due drafts.
    cron_jobs = [
        cron(sweep_overdue_task_reminders, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(process_outreach_dispatch, minute={2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57}),
        cron(backfill_lead_scores_task, minute={0}),
        cron(run_ai_social_scheduler, minute=set(range(60))),
        cron(enqueue_due_scraper_tasks, minute={0, 15, 30, 45}),
        cron(sync_all_google_reviews, minute={5, 35}),
        cron(assign_daily_trial_leads, hour={6}, minute={0}),
        cron(send_trial_lead_ending_reminders, hour={9}, minute={0}),
        cron(process_booking_notification_queue, minute={0, 10, 20, 30, 40, 50}),
    ]
    max_jobs = 10
    job_timeout = 300
    keep_result = 86400
    retry_jobs = True
    max_tries = 3
    health_check_interval = 30
