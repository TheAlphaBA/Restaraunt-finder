---
name: Gastronomic Discovery Engine
colors:
  surface: '#fff7ff'
  surface-dim: '#e3d5eb'
  surface-bright: '#fff7ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fbf0ff'
  surface-container: '#f7e9ff'
  surface-container-high: '#f1e3f9'
  surface-container-highest: '#ebdef4'
  on-surface: '#201828'
  on-surface-variant: '#49454e'
  inverse-surface: '#352d3d'
  inverse-on-surface: '#f9ecff'
  outline: '#7a757f'
  outline-variant: '#cbc4cf'
  surface-tint: '#665784'
  primary: '#534471'
  on-primary: '#ffffff'
  primary-container: '#6b5c8a'
  on-primary-container: '#e9dbff'
  inverse-primary: '#d0bef2'
  secondary: '#a43073'
  on-secondary: '#ffffff'
  secondary-container: '#fc79bd'
  on-secondary-container: '#76014e'
  tertiary: '#53456e'
  on-tertiary: '#ffffff'
  tertiary-container: '#6b5d87'
  on-tertiary-container: '#e9dbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d0bef2'
  on-primary-fixed: '#21133d'
  on-primary-fixed-variant: '#4d3f6b'
  secondary-fixed: '#ffd8e7'
  secondary-fixed-dim: '#ffafd3'
  on-secondary-fixed: '#3d0026'
  on-secondary-fixed-variant: '#85145a'
  tertiary-fixed: '#eaddff'
  tertiary-fixed-dim: '#d0bfef'
  on-tertiary-fixed: '#21143a'
  on-tertiary-fixed-variant: '#4d4068'
  background: '#fff7ff'
  on-background: '#201828'
  surface-variant: '#ebdef4'
typography:
  headline-xl:
    fontFamily: Bricolage Grotesque
    fontSize: 3.5rem
    fontWeight: '800'
    lineHeight: 3.75rem
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Bricolage Grotesque
    fontSize: 2.25rem
    fontWeight: '800'
    lineHeight: 2.5rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 2.5rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.025em
  headline-lg-mobile:
    fontFamily: Bricolage Grotesque
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Bricolage Grotesque
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: 2.125rem
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Bricolage Grotesque
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.625rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: 1.75rem
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
  label-lg:
    fontFamily: Hanken Grotesk
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.25rem
    letterSpacing: 0.01em
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 0.6875rem
    fontWeight: '700'
    lineHeight: 0.875rem
    letterSpacing: 0.04em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an avant-garde, sensory-forward visual language for an AI-powered culinary recommendation engine. It bridges computational precision (fast LLM inference, granular food metadata) with warm, organic, and delightful lifestyle discovery.

The aesthetic fuses modern minimalism with tactile neo-editorial warmth. Rather than defaulting to sterile analytics or traditional red-tinted food app paradigms, the atmosphere leverages soft lavender mist, luminous card elevations, and radiant berry-tinted active states. Typography pairs the eccentric, hyper-expressive curves of the display font with the clean, ultra-legible structural cadence of the body font. The interface conveys intuitive intelligence, refined taste, and effortlessly conversational food exploration.

## Colors

The palette is engineered around airy chromatic layers that maintain high readability while delivering immersive character.

- **Primary Background (`#FAFAFA`)**: An ultra-clean canvas providing natural breathing room for card-based discovery feeds.
- **Surface Cards & Containers (`#F3EFFE`)**: Luminous, lavender-tinted surfaces that cradle content blocks, filters, and dynamic AI result modules.
- **Primary Hue (`#6B5C8A`)**: Deep plum-slate utilized for structural sub-elements, labels, interactive borders, and secondary metadata.
- **Action & Accent Gradient (`#F472B6` to `#E879A0`)**: Vibrant electric rose and strawberry-pink for primary AI actions, match percentages, selected filters, and active states.
- **Tertiary Accent (`#C9B8E8`)**: Soft lilac tint for structural borders, card strokes, and subtle state feedback. Divider accents use `#E4D9F7`.
- **Text & Contrast Hierarchy**: Deep charcoal (`#2D2535`) preserves crisp contrast on light backgrounds for headers and body, while softened plum (`#6B5C8A`) provides elegant subordinate hierarchy for metadata, ratings context, and timestamps.
- **Functional Semantics**: Soft Amber (`#FEF3C7` background / `#D97706` text) for moderate ratings, dietary alerts, and advisory badges; Soft Rose (`#FEE2E2` background / `#E11D48` text) for exclusions, high-friction errors, and unavailable venues.

## Typography

The typography unites experimental expressiveness with razor-sharp computational legibility. 

- **Display & Headings**: Set in display font with tight tracking and distinct optical flare. Hero headings and section banners support an inline gradient treatment blending deep royal purple into radiant electric pink (`#9333EA` to `#EC4899`) applied across hero titles and AI insight headlines.
- **Body & Continuous Reading**: Powered by the modern body font, calibrated for comfortable scannability in dense culinary profiles, AI prompt answers, and ingredient inventories.
- **Badges & Labels**: Medium-to-bold weights ensure critical dietary flags (e.g., "Artisanal", "Late-Night", "Halal", "4.8★") remain distinct even at diminished viewport scales.

## Layout & Spacing

The interface operates on a disciplined 8pt grid with flexible responsive constraints to accommodate both rapid dashboard filters and wide editorial browsing.

- **Desktop (1024px and up)**: 12-column fluid grid configured with an integrated persistent lateral drawer (280px–340px) dedicated to AI parameter controls, price dials, and cuisine matrices. Content region maintains 24px gutters with 40px outer edge boundaries.
- **Tablet (768px - 1023px)**: 8-column layout. The parameter panel transforms into an off-canvas slide-out sheet; restaurant recommendation grids reflow from 3 columns down to 2 columns.
- **Mobile (under 768px)**: 4-column fluid layout with 16px margins and gutters. Single-column restaurant feed with floating bottom action anchors for quick prompt queries and instant filter toggles.
- **Internal Component Spacing**: Micro-rhythms strictly leverage `space-xs` (4px) and `space-sm` (8px) for badge insets and chip tags, `space-md` (16px) for form groupings, and `space-lg` (24px) for card body padding.

## Elevation & Depth

Visual hierarchy uses luminous chromatic layering rather than harsh directional dropshadows. Surfaces build depth through ambient lavender reflections and delicate bounding outlines:

- **Level 0 (Base Canvas)**: Flat `#FAFAFA` ground plane.
- **Level 1 (Card & Sidebar Tier)**: `#F3EFFE` tinted plane bounded by a 1px border of `#E4D9F7` and supported by an ambient low-opacity shadow: `0 4px 20px -2px rgba(107, 92, 138, 0.06)`.
- **Level 2 (Hovered Cards & Dynamic AI Recommendations)**: Subtle upward translation paired with a composite spread shadow: `0 12px 28px -4px rgba(107, 92, 138, 0.12), 0 2px 6px -1px rgba(244, 114, 182, 0.15)`.
- **Level 3 (Modals, Context Menus, and Active Streamlit Filters)**: Elevated floating surfaces framed with `#C9B8E8` borders, layered over a soft blurred backdrop (`backdrop-filter: blur(8px)`) using `0 24px 48px -8px rgba(45, 37, 53, 0.18)`.

## Shapes

The design system embraces an ultra-soft, rounded visual language (Level 3 pill-shaped standard), offering an inviting, approachable culinary software experience.

- **Primary Actions & Badges**: Fully pill-shaped (`border-radius: 9999px`) for search triggers, cuisine chips, match metrics, and quick-filter buttons.
- **Cards & Data Panels**: `rounded-lg` (2rem / 32px) on desktop to create organic, cushioned containers that soften data-heavy restaurant metrics.
- **Form Controls & Modals**: Outer bounding boxes feature `rounded-md` (1rem / 16px) to maintain structured optical balance against circular chips.

## Components

### Buttons
- **Primary AI Action**: Pill-shaped button styled with a vibrant linear gradient background (`#F472B6` to `#E879A0`), solid white text, semibold weight, and subtle outer glow on hover (`0 0 16px rgba(244, 114, 182, 0.45)`). Active click states depress slightly (98% scale).
- **Secondary / Ghost**: Transparent or white background with a 1.5px border of `#C9B8E8`, text colored `#6B5C8A`. Transitions to `#F3EFFE` surface fill on pointer hover.

### Chips & Filters
- **Dietary & Cuisine Chips**: Pill-shaped containers (`height: 36px`, `padding: 0 16px`). Inactive state: `#FFFFFF` fill with 1px `#E4D9F7` outline and `#2D2535` text. Active/Selected state: `#6B5C8A` solid fill with `#FFFFFF` text or pink gradient stroke with lavender highlight.

### Input Fields & Search Bars
- **AI Natural Language Input**: Height 56px, fully rounded capsule. Outer boundary enclosed in 1.5px `#C9B8E8` with `#FFFFFF` interior fill. On focus, transitions to an illuminated pink-violet rim (`outline: 2px solid #F472B6`) with a gentle soft-purple ambient shadow. Interior prompt icons set in `#6B5C8A`.

### Restaurant Result Cards
- Constructed with `#F3EFFE` surface fill, `rounded-lg` perimeter, and 1px `#E4D9F7` stroke.
- Features top metadata slot with match-affinity score badge (solid gradient `#F472B6` to `#E879A0`, white pill text), venue title in display font (`headline-sm`), price/cuisine indicators in `#6B5C8A`, and an embedded bulleted AI summary snippet highlighting why the dish matches the query.

### Checkboxes & Radio Controls
- Circular and smooth rounded squares (`rounded: 6px` for checkboxes, full circle for radios). Border 1.5px `#C9B8E8`. When checked, surfaces fill with `#6B5C8A` or action gradient with crisp white checkmark/dot indicators.

### Additional Domain Components
- **LLM Reasoning Pill**: Collapsible accordion with lavender tint highlighting tokens extracted by Groq (e.g., "Ambience: Cozy", "Dietary: Vegan-Friendly", "Latency: 28ms").
- **Cost-For-Two Tier Gauge**: Micro segmented bar using pill-shaped track markers transitioning from neutral grey to vivid violet-pink.