export type AdaptiveGoal = 'grow' | 'automate' | 'reduce_workload'

export interface BusinessNicheConfig {
  id: string
  name: string
  hero: {
    title: string
    subtitle: string
  }
  painPoints: string[]
  goalMapping: Record<AdaptiveGoal, string>
  testimonial: string
  cta: {
    primary: string
    secondary: string
  }
}

export type AdaptivePainPoint = {
  id: string
  label: string
  description: string
}

export type AdaptiveNicheConfig = {
  id: string
  label: string
  hero: {
    eyebrow: string
    headline: string
    subheadline: string
    primaryCta: string
    secondaryCta: string
    image: string
    imageAlt: string
  }
  painPoints: AdaptivePainPoint[]
  goalBlocks: Record<AdaptiveGoal, { title: string; body: string }>
  testimonials: { quote: string; name: string; role: string }[]
  ctaText: string
  whyBlock: { title: string; body: string }
}

export type AdaptiveDemoSelection = {
  nicheId: string
  painPointIds: string[]
  goal: AdaptiveGoal
}

export const ADAPTIVE_UI_STORAGE_KEY = 'cf_adaptive_ui_demo_v1'
export const ADAPTIVE_UI_EVENT = 'cf:adaptive-ui-demo-updated'

export const GOAL_OPTIONS: { id: AdaptiveGoal; label: string }[] = [
  { id: 'grow', label: 'Grow' },
  { id: 'automate', label: 'Automate' },
  { id: 'reduce_workload', label: 'Reduce workload' },
]

export const ADAPTIVE_UI_NICHES: BusinessNicheConfig[] = [
  // -----------------------------------------------------
  // 1. ELECTRICIAN
  // -----------------------------------------------------
  {
    id: "electrician",
    name: "Electrician",
    hero: {
      title: "Win More High-Value Electrical Jobs Effortlessly",
      subtitle: "Customerflo helps electricians get steady work, automate quotes, and keep customers coming back."
    },
    painPoints: [
      "Inconsistent job requests",
      "Slow quote responses",
      "Hard to track customers & repeat work",
      "Too much admin"
    ],
    goalMapping: {
      grow: "Get a predictable flow of installation & repair leads every week.",
      automate: "Auto-send quotes, reminders, follow-ups, and repeat-maintenance prompts.",
      reduce_workload: "Cut admin time by 70% with smart scheduling and automated customer messaging."
    },
    testimonial: "‘Customerflo doubled my monthly installation jobs in 6 weeks.’ — ElectricRepair UK",
    cta: {
      primary: "Start Getting More Electrical Jobs",
      secondary: "See How Electricians Use Customerflo"
    }
  },

  // -----------------------------------------------------
  // 2. PLUMBER
  // -----------------------------------------------------
  {
    id: "plumber",
    name: "Plumber",
    hero: {
      title: "Never Run Out of Plumbing Jobs Again",
      subtitle: "Automated lead generation, smart scheduling, and repeat-customer retention."
    },
    painPoints: [
      "Too many peak/quiet seasons",
      "Emergency jobs lost due to slow replies",
      "Recurring boiler/maintenance not tracked"
    ],
    goalMapping: {
      grow: "Get a constant flow of emergency & installation leads.",
      automate: "Auto-book boiler servicing & follow-ups.",
      reduce_workload: "Let Customerflo handle scheduling, reminders & invoices."
    },
    testimonial: "‘My repeat boiler servicing revenue tripled.’ — LondonFix Plumbing",
    cta: {
      primary: "Increase Plumbing Income",
      secondary: "See Plumbing Success Stories"
    }
  },

  // -----------------------------------------------------
  // 3. CARPENTER / JOINER
  // -----------------------------------------------------
  {
    id: "carpenter",
    name: "Carpenter / Joiner",
    hero: {
      title: "Get More Custom Build & Installation Projects",
      subtitle: "Showcase your best work, win more quotes, and stay fully booked."
    },
    painPoints: [
      "Clients price-shop too much",
      "Difficult to showcase before/after",
      "Long quote cycles lose hot clients"
    ],
    goalMapping: {
      grow: "Attract more premium carpentry requests.",
      automate: "Auto-send quotes, reminders, and photo portfolios.",
      reduce_workload: "Automate follow-ups and client communication."
    },
    testimonial: "‘My custom-furniture bookings increased by 40%.’ — CraftBuild UK",
    cta: {
      primary: "Boost Carpentry Projects",
      secondary: "See Carpenter Templates"
    }
  },

  // -----------------------------------------------------
  // 4. ROOFER
  // -----------------------------------------------------
  {
    id: "roofer",
    name: "Roofer",
    hero: {
      title: "Win More Roof Repairs & Full Installs",
      subtitle: "Convert urgent roofing enquiries before competitors do."
    },
    painPoints: [
      "Slow replies cost urgent work",
      "Hard to track leads",
      "Inconsistent flow of high-ticket jobs"
    ],
    goalMapping: {
      grow: "Get more roof inspections & replacement leads.",
      automate: "Automatic quoting and job reminders.",
      reduce_workload: "Let Customerflo handle client communication."
    },
    testimonial: "‘Booked 3 extra roof installs per week!’ — Skyline Roofing",
    cta: {
      primary: "Increase Roofing Jobs",
      secondary: "See Roofer Demo"
    }
  },

  // -----------------------------------------------------
  // 5. CLEANER
  // -----------------------------------------------------
  {
    id: "cleaner",
    name: "Cleaner / Cleaning Company",
    hero: {
      title: "Grow Your Cleaning Business with Repeat Clients",
      subtitle: "Automated booking, scheduling, quote reminders & customer retention."
    },
    painPoints: [
      "Hard to get consistent clients",
      "No-show bookings",
      "Poor repeat-customer retention"
    ],
    goalMapping: {
      grow: "Fill your calendar with commercial & domestic cleaning jobs.",
      automate: "Automatic reminders, quotes & rescheduling.",
      reduce_workload: "Automated cleaning-rotation scheduling."
    },
    testimonial: "‘We scaled from 17 to 90 weekly clients.’ — FreshHome Cleaning",
    cta: {
      primary: "Grow Cleaning Clients",
      secondary: "See Cleaning Templates"
    }
  },

  // -----------------------------------------------------
  // 6. HANDYMAN
  // -----------------------------------------------------
  {
    id: "handyman",
    name: "Handyman",
    hero: {
      title: "Get More Local Handyman Jobs Daily",
      subtitle: "Your all-in-one lead generator, booking system & CRM."
    },
    painPoints: [
      "Low visibility",
      "Hard to manage calls/messages",
      "Inconsistent work"
    ],
    goalMapping: {
      grow: "Get more small/medium handyman job requests daily.",
      automate: "Automated confirmations and job reminders.",
      reduce_workload: "Stop juggling chats, calls & emails manually."
    },
    testimonial: "‘My booking rate increased by 65%.’ — LocalRepairMan UK",
    cta: {
      primary: "Start Getting Daily Jobs",
      secondary: "See Handyman Demo"
    }
  },

  // -----------------------------------------------------
  // 7. PAINTER / DECORATOR
  // -----------------------------------------------------
  {
    id: "painter",
    name: "Painter & Decorator",
    hero: {
      title: "Get More Painting and Decorating Projects",
      subtitle: "Beautiful templates, automated quotes, and high-quality job bookings."
    },
    painPoints: [
      "Hard to stand out",
      "Slow quote response",
      "Poor repeat-customer engagement"
    ],
    goalMapping: {
      grow: "Attract more interior & exterior painting jobs.",
      automate: "Automatic quoting and colour-consultation reminders.",
      reduce_workload: "Less admin, more painting."
    },
    testimonial: "‘My monthly revenue doubled.’ — PerfectFinish Decor",
    cta: {
      primary: "Grow Painting Bookings",
      secondary: "See Decorator Samples"
    }
  },

  // -----------------------------------------------------
  // 8. LANDSCAPER / GARDENER
  // -----------------------------------------------------
  {
    id: "landscaper",
    name: "Landscaper / Gardener",
    hero: {
      title: "Stay Fully Booked With Landscaping & Garden Jobs",
      subtitle: "Automated recurring bookings + customer reminders."
    },
    painPoints: [
      "Seasonal slowdowns",
      "Hard to manage recurring visits",
      "Low online visibility"
    ],
    goalMapping: {
      grow: "Get more landscaping & maintenance leads.",
      automate: "Auto-schedule recurring garden visits.",
      reduce_workload: "Automated customer communication."
    },
    testimonial: "‘We went from 4 to 18 recurring clients.’ — GreenLeaf UK",
    cta: {
      primary: "Increase Landscaping Jobs",
      secondary: "See Garden Templates"
    }
  },

  // -----------------------------------------------------
  // 9. HVAC / GAS ENGINEER
  // -----------------------------------------------------
  {
    id: "hvac",
    name: "Gas / Heating / HVAC Engineer",
    hero: {
      title: "Fill Your Calendar with Heating & Boiler Jobs",
      subtitle: "Automate servicing reminders & emergency call bookings."
    },
    painPoints: [
      "Boiler servicing not tracked",
      "Customers forget yearly servicing",
      "High competition"
    ],
    goalMapping: {
      grow: "Get more boiler installs & servicing jobs.",
      automate: "Auto-schedule annual servicing reminders.",
      reduce_workload: "Automated client communication."
    },
    testimonial: "‘Customerflo brought consistent boiler jobs.’ — HeatWorks UK",
    cta: {
      primary: "Boost HVAC Jobs",
      secondary: "See HVAC Demo"
    }
  },

  // -----------------------------------------------------
  // 10. PERSONAL TRAINER
  // -----------------------------------------------------
  {
    id: "trainer",
    name: "Personal Trainer",
    hero: {
      title: "Get New Clients & Automate Your PT Sessions",
      subtitle: "AI-powered content, scheduling, and client retention."
    },
    painPoints: [
      "Hard to get new clients",
      "Clients drop off",
      "No automation for reminders"
    ],
    goalMapping: {
      grow: "Get a steady stream of fitness clients.",
      automate: "Auto-send training reminders.",
      reduce_workload: "Focus on training, not admin."
    },
    testimonial: "‘My client retention improved massively.’ — TrainFit UK",
    cta: {
      primary: "Grow Your PT Business",
      secondary: "See PT Templates"
    }
  },

  // -----------------------------------------------------
  // 11. BEAUTY SALON
  // -----------------------------------------------------
  {
    id: "beauty",
    name: "Beauty Salon",
    hero: {
      title: "Increase Repeat Beauty Appointments",
      subtitle: "Automated bookings, reminders & client nurturing."
    },
    painPoints: [
      "No-shows",
      "Hard to retain clients",
      "Low visibility"
    ],
    goalMapping: {
      grow: "Get more beauty bookings.",
      automate: "Auto-reminders reduce no-shows.",
      reduce_workload: "Automate marketing messages."
    },
    testimonial: "‘Customerflo changed everything.’ — GlamStudio UK",
    cta: {
      primary: "Grow Beauty Clients",
      secondary: "See Beauty Templates"
    }
  },

  // -----------------------------------------------------
  // 12. BARBER
  // -----------------------------------------------------
  {
    id: "barber",
    name: "Barber Shop",
    hero: {
      title: "Fill Your Barber Chairs Week After Week",
      subtitle: "Automated reminders, membership offers, and booking system."
    },
    painPoints: [
      "Walk-ins too unpredictable",
      "No client tracking",
      "Hard to promote offers"
    ],
    goalMapping: {
      grow: "Attract more walk-in and booking clients.",
      automate: "Automatic appointment reminders.",
      reduce_workload: "Let Customerflo run your marketing."
    },
    testimonial: "‘We increased weekly clients by 30%.’ — FadeMasters UK",
    cta: {
      primary: "Boost Barber Bookings",
      secondary: "See Barber Templates"
    }
  },

  // -----------------------------------------------------
  // 13. MASSAGE THERAPIST
  // -----------------------------------------------------
  {
    id: "massage",
    name: "Massage Therapist",
    hero: {
      title: "Get More Regular Massage Clients",
      subtitle: "Automate rebooking, reminders & packages."
    },
    painPoints: [
      "Clients rarely rebook",
      "Hard to track history",
      "Low visibility"
    ],
    goalMapping: {
      grow: "Attract more wellness clients.",
      automate: "Automatic rebooking reminders.",
      reduce_workload: "Automate session follow-ups."
    },
    testimonial: "‘My rebooking rate jumped to 70%.’ — RelaxTherapy UK",
    cta: {
      primary: "Grow Massage Clients",
      secondary: "See Massage Templates"
    }
  },

  // -----------------------------------------------------
  // 14. REMOVAL COMPANY
  // -----------------------------------------------------
  {
    id: "removal",
    name: "Removal Company",
    hero: {
      title: "Get More Moving & Removal Jobs",
      subtitle: "Automated quoting, reminders, and lead management."
    },
    painPoints: [
      "Leads go cold quickly",
      "Hard to manage quotes",
      "Slow follow-ups lose clients"
    ],
    goalMapping: {
      grow: "Get more local removal leads.",
      automate: "Send quotes & reminders automatically.",
      reduce_workload: "Spend less time chasing clients."
    },
    testimonial: "‘We scaled to 3 trucks fast.’ — MoveFast UK",
    cta: {
      primary: "Grow Removal Bookings",
      secondary: "See Removal Templates"
    }
  },

  // -----------------------------------------------------
  // 15. ACCOUNTANT / BOOKKEEPER
  // -----------------------------------------------------
  {
    id: "accountant",
    name: "Accountant / Bookkeeper",
    hero: {
      title: "Automate Client Intake & Grow Your Accounting Firm",
      subtitle: "Lead capture, onboarding, reminders & document flows."
    },
    painPoints: [
      "Too much manual onboarding",
      "Clients forget deadlines",
      "Low client retention"
    ],
    goalMapping: {
      grow: "Get more accounting clients monthly.",
      automate: "Tax deadline reminders & onboarding flows.",
      reduce_workload: "Replace email chains with automation."
    },
    testimonial: "‘Client onboarding is 3x faster.’ — SmartBooks UK",
    cta: {
      primary: "Grow Your Accounting Firm",
      secondary: "See Demo"
    }
  },

  // -----------------------------------------------------
  // 16. REAL ESTATE AGENT
  // -----------------------------------------------------
  {
    id: "estate_agent",
    name: "Estate Agent",
    hero: {
      title: "Generate More Property Leads & Automate Viewings",
      subtitle: "Lead nurturing, SMS reminders & follow-ups."
    },
    painPoints: [
      "Leads go cold quickly",
      "Missed viewing reminders",
      "High admin workload"
    ],
    goalMapping: {
      grow: "Increase buyer & seller enquiries.",
      automate: "Auto-send viewing reminders.",
      reduce_workload: "Automate follow-up sequences."
    },
    testimonial: "‘We doubled our viewing attendance.’ — MetroEstate UK",
    cta: {
      primary: "Increase Property Leads",
      secondary: "See Estate Templates"
    }
  },

  // -----------------------------------------------------
  // 17. CAR DETAILER / VALETING
  // -----------------------------------------------------
  {
    id: "cardetailer",
    name: "Car Detailer / Valet",
    hero: {
      title: "Get More Car Detailing Bookings",
      subtitle: "Automation for reminders, upsells & retention."
    },
    painPoints: [
      "Few repeat customers",
      "Poor online visibility",
      "Hard to track appointments"
    ],
    goalMapping: {
      grow: "Get more detailing & valet bookings.",
      automate: "Auto-send wash reminders.",
      reduce_workload: "Less admin, more detailing."
    },
    testimonial: "‘We now have 80+ repeat clients.’ — ShineAuto UK",
    cta: {
      primary: "Grow Detailing Bookings",
      secondary: "See Templates"
    }
  },

  // -----------------------------------------------------
  // 18. PHOTOGRAPHER
  // -----------------------------------------------------
  {
    id: "photographer",
    name: "Photographer",
    hero: {
      title: "Book More Photography Clients",
      subtitle: "Automate enquiries, reminders & client conversations."
    },
    painPoints: [
      "Inconsistent bookings",
      "Hard to manage enquiries",
      "Clients slow to respond"
    ],
    goalMapping: {
      grow: "Get more session & event bookings.",
      automate: "Auto-send reminders & follow-up messages.",
      reduce_workload: "Automate client communications."
    },
    testimonial: "‘My bookings increased by 50%.’ — PixelShot UK",
    cta: {
      primary: "Grow Photography Clients",
      secondary: "See Photographer Templates"
    }
  },

  // -----------------------------------------------------
  // 19. DRIVING INSTRUCTOR
  // -----------------------------------------------------
  {
    id: "driving_instructor",
    name: "Driving Instructor",
    hero: {
      title: "Get More Students & Automate Lesson Management",
      subtitle: "Let Customerflo handle bookings & reminders."
    },
    painPoints: [
      "Hard to get new students",
      "Missed lesson reminders",
      "Lots of admin"
    ],
    goalMapping: {
      grow: "Get more new learner enquiries.",
      automate: "Auto-send lesson reminders.",
      reduce_workload: "Automate your scheduling."
    },
    testimonial: "‘My lessons are booked weeks ahead.’ — DriveSmart UK",
    cta: {
      primary: "Grow Your Student List",
      secondary: "See Templates"
    }
  },

  // -----------------------------------------------------
  // 20. DOG GROOMER
  // -----------------------------------------------------
  {
    id: "dog_groomer",
    name: "Dog Groomer",
    hero: {
      title: "Get More Grooming Appointments & Repeat Clients",
      subtitle: "Automated reminders, follow-ups & appointment flow."
    },
    painPoints: [
      "No-shows",
      "Few repeat clients",
      "Hard to manage bookings"
    ],
    goalMapping: {
      grow: "Get more grooming clients monthly.",
      automate: "Auto-send grooming cycle reminders.",
      reduce_workload: "Automate booking confirmation & follow-up."
    },
    testimonial: "‘Now fully booked weeks ahead.’ — FurFresh UK",
    cta: {
      primary: "Grow Grooming Appointments",
      secondary: "See Dog Groomer Demo"
    }
  }
]

const fallbackImage =
  'https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=1200&q=70'

const nicheHeroImages: Record<string, { image: string; imageAlt: string }> = {
  electrician: {
    image:
      'https://images.unsplash.com/photo-1621905252507-b35492cc74b4?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Electrician working on an electrical control panel',
  },
  plumber: {
    image:
      'https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Plumber repairing pipework under a sink',
  },
  carpenter: {
    image:
      'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Carpenter working with timber in a workshop',
  },
  roofer: {
    image:
      'https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Roofing and construction work on a building',
  },
  cleaner: {
    image:
      'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Professional cleaner cleaning a bright room',
  },
  handyman: {
    image:
      'https://images.unsplash.com/photo-1581244277943-fe4a9c777189?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Handyman using tools for a home repair job',
  },
  painter: {
    image:
      'https://images.unsplash.com/photo-1562259949-e8e7689d7828?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Painter decorating an interior wall',
  },
  landscaper: {
    image:
      'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Gardener caring for plants and landscaping',
  },
  hvac: {
    image:
      'https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Heating and HVAC engineer servicing equipment',
  },
  trainer: {
    image:
      'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Personal trainer coaching a client in the gym',
  },
  beauty: {
    image:
      'https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Beauty salon professional styling a client',
  },
  barber: {
    image:
      'https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Barber cutting hair in a barber shop',
  },
  massage: {
    image:
      'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Massage therapist providing a wellness treatment',
  },
  removal: {
    image:
      'https://images.unsplash.com/photo-1600518464441-9154a4dea21b?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Removal company moving packed boxes',
  },
  accountant: {
    image:
      'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Accountant reviewing financial documents and reports',
  },
  estate_agent: {
    image:
      'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Estate agent showing a home to property clients',
  },
  cardetailer: {
    image:
      'https://images.unsplash.com/photo-1607860108855-64acf2078ed9?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Car detailer cleaning and polishing a vehicle',
  },
  photographer: {
    image:
      'https://images.unsplash.com/photo-1452587925148-ce544e77e70d?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Photographer taking professional photos with a camera',
  },
  driving_instructor: {
    image:
      'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Driving instructor business represented by a car on the road',
  },
  dog_groomer: {
    image:
      'https://images.unsplash.com/photo-1516734212186-a967f81ad0d7?auto=format&fit=crop&w=1200&q=80',
    imageAlt: 'Dog groomer caring for a dog during grooming',
  },
}

function parseTestimonial(raw: string, fallbackRole: string) {
  const [quotePart, attributionPart] = raw.split('—').map((part) => part.trim())
  return {
    quote: quotePart || raw,
    name: attributionPart || 'Customerflo customer',
    role: fallbackRole,
  }
}

export const ADAPTIVE_NICHES: AdaptiveNicheConfig[] = ADAPTIVE_UI_NICHES.map((niche) => ({
  id: niche.id,
  label: niche.name,
  hero: {
    eyebrow: `Customerflo for ${niche.name}`,
    headline: niche.hero.title,
    subheadline: niche.hero.subtitle,
    primaryCta: niche.cta.primary,
    secondaryCta: niche.cta.secondary,
    image: nicheHeroImages[niche.id]?.image ?? fallbackImage,
    imageAlt: nicheHeroImages[niche.id]?.imageAlt ?? `${niche.name} using Customerflo`,
  },
  painPoints: niche.painPoints.map((painPoint, index) => ({
    id: `${niche.id}-pain-${index + 1}`,
    label: painPoint,
    description: `Customerflo helps solve "${painPoint.toLowerCase()}" with connected CRM, automation, reminders and customer follow-up.`,
  })),
  goalBlocks: {
    grow: { title: 'Grow', body: niche.goalMapping.grow },
    automate: { title: 'Automate', body: niche.goalMapping.automate },
    reduce_workload: { title: 'Reduce workload', body: niche.goalMapping.reduce_workload },
  },
  testimonials: [parseTestimonial(niche.testimonial, niche.name)],
  ctaText: niche.cta.primary,
  whyBlock: {
    title: `Why Customerflo solves ${niche.name.toLowerCase()} pain`,
    body: 'Customerflo connects lead capture, CRM, automation, reminders, reviews and customer messaging so the whole workflow stays in one place.',
  },
}))

export function getAdaptiveNiche(id: string | null | undefined): AdaptiveNicheConfig | null {
  if (!id) return null
  return ADAPTIVE_NICHES.find((nicheConfig) => nicheConfig.id === id) ?? null
}
