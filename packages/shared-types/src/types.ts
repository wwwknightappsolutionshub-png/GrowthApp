export type UUID = string;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ApiError {
  detail: string;
  code?: string;
}

export type TenantRole = "owner" | "staff";

export type LeadStatus = "new" | "in_crm" | "spam" | "duplicate";

export type DealStageType =
  | "New"
  | "Contacted"
  | "Quoted"
  | "Booked"
  | "Completed"
  | "Lost";

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "no_show";

export type QuoteStatus =
  | "draft"
  | "sent"
  | "accepted"
  | "declined"
  | "expired";

export type InvoiceStatus =
  | "draft"
  | "sent"
  | "paid"
  | "partially_paid"
  | "overdue"
  | "cancelled";

export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "canceled"
  | "paused";

export type AutomationTrigger =
  | "lead_created"
  | "stage_changed"
  | "booking_confirmed"
  | "job_completed"
  | "quote_sent"
  | "invoice_overdue"
  | "deal_no_activity";

export type MessageChannel = "sms" | "email";
export type MessageDirection = "inbound" | "outbound";

export type SocialPlatform = "facebook" | "instagram";
export type SocialPostStatus =
  | "draft"
  | "pending_approval"
  | "scheduled"
  | "published"
  | "failed";
