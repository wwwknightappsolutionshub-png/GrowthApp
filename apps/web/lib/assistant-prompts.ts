/** Module-specific prompt prefixes for AI assistant (separate UX per surface). */

export const GROWTH_TOPIC_PROMPTS = {
  lead_generation: `[Focus: Lead generation] Help me get more qualified leads this week. What should I do first on CustomerFlow AI (landing page, ads, referrals)?`,
  lead_conversion: `[Focus: Lead conversion] Review how I should convert my current pipeline faster. Which deals or leads need action today?`,
  retargeting: `[Focus: Retargeting] Suggest a retargeting plan for cold leads and past customers I have not heard from recently.`,
  retention: `[Focus: Retention] How do I improve retention and repeat bookings? Suggest follow-ups and nurture steps.`,
} as const

export const CRM_EDUCATOR_PROMPTS = {
  pipeline: `[CRM coach] Explain how to use the pipeline board effectively for my trade business.`,
  customers: `[CRM coach] How should I structure customer records for follow-ups and upsells?`,
  segments: `[CRM coach] When should I use segments vs tags in CRM?`,
} as const

export type GrowthTopic = keyof typeof GROWTH_TOPIC_PROMPTS
