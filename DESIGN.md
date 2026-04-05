# RecruitGraph — Design System Reference

> Extracted from Stitch project `837786763612755729` (RecruitGraph).
> Philosophy: **"The Digital Architect"** — hyper-minimalist, zero-radius, tonal layering, no shadows.

---

## 1. Color Palette

### Backgrounds & Surfaces (Tonal Layering — no borders between sections)

| Token                     | Hex       | Usage                                      |
|---------------------------|-----------|----------------------------------------------|
| `background`              | `#131313` | Page canvas, base layer                      |
| `surface`                 | `#131313` | Default surface (same as background)         |
| `surface-dim`             | `#131313` | Dimmed variant                               |
| `surface-container-lowest`| `#0E0E0E` | Deepest recessed panels, sidebar dividers    |
| `surface-container-low`   | `#1B1B1B` | Secondary sections                           |
| `surface-container`       | `#1F1F1F` | Cards, elevated containers                   |
| `surface-container-high`  | `#2A2A2A` | Active/interactive modules                   |
| `surface-container-highest`| `#353535`| Tooltips, dropdowns, top-layer overlays      |
| `surface-bright`          | `#393939` | Hover/selection state background             |
| `surface-variant`         | `#353535` | Alternate surface                            |

### Text & Foreground

| Token                | Hex       | Usage                                 |
|----------------------|-----------|---------------------------------------|
| `on-surface`         | `#E2E2E2` | Primary text (headlines, active data) |
| `on-surface-variant` | `#CFC2D6` | Secondary text, muted labels          |
| `on-background`      | `#E2E2E2` | Text on background                    |
| `muted`              | `#666666` | Tertiary/disabled text                |
| `inverse-surface`    | `#E2E2E2` | Light text on dark inverse            |

### Accent — Purple (Primary action color)

| Token               | Hex       | Usage                              |
|----------------------|-----------|------------------------------------|
| `accent-purple`      | `#A855F7` | Primary buttons, neon strike       |
| `primary`            | `#DDB7FF` | Active states, surface tint        |
| `primary-container`  | `#B76DFF` | Highlighted data peaks, indicators |
| `primary-fixed`      | `#F0DBFF` | Fixed primary surface              |
| `primary-fixed-dim`  | `#DDB7FF` | Dimmed fixed primary               |

### Accent — Teal (used sparingly in graph nodes)

| Token         | Hex       | Usage                   |
|---------------|-----------|-------------------------|
| `accent-teal` | `#1D9E75` | Graph edges, connection lines |

### Accent — Green (success / positive metrics)

| Token          | Hex       | Usage                          |
|----------------|-----------|--------------------------------|
| `accent-green` | `#639922` | Positive change indicators     |

### Semantic

| Token  | Hex       | Usage                                |
|--------|-----------|--------------------------------------|
| `error`| `#FFB4AB` | Error text foreground                |
| `error-container` | `#93000A` | Error background           |
| `red`  | `#FF4444` | Destructive actions, critical badges |
| `amber`| `#FFAA00` | Warnings, medium-severity badges     |
| `green`| `#44BB66` | Success states, healthy badges       |

### Borders & Outlines

| Token            | Hex       | Usage                                         |
|------------------|-----------|-----------------------------------------------|
| `outline`        | `#988D9F` | Visible borders (rare)                        |
| `outline-variant`| `#4D4354` | Ghost borders at 20% opacity, input outlines  |
| `matte-silver`   | `#222222` | Command palette borders, input containers      |

---

## 2. Typography

### Font Families
- **Interface (headlines + body):** `Inter` — clean, functional sans-serif
- **Information (numbers, IDs, timestamps, labels):** `Space Grotesk` — technical monospace feel

### Type Scale

| Role        | Font          | Size  | Weight | Letter-spacing | Color Token          |
|-------------|---------------|-------|--------|----------------|----------------------|
| `display`   | Inter         | 48px  | 700    | -0.02em        | `on-surface`         |
| `headline-lg` | Inter       | 32px  | 700    | -0.02em        | `on-surface`         |
| `headline-md` | Inter       | 24px  | 600    | -0.02em        | `on-surface`         |
| `body-lg`   | Inter         | 18px  | 400    | 0              | `on-surface`         |
| `body-md`   | Inter         | 14px  | 400    | 0              | `on-surface-variant` |
| `body-sm`   | Inter         | 12px  | 400    | 0              | `on-surface-variant` |
| `label-lg`  | Space Grotesk | 16px  | 500    | 0              | `on-surface`         |
| `label-md`  | Space Grotesk | 14px  | 500    | 0.01em         | `on-surface`         |
| `label-sm`  | Space Grotesk | 12px  | 500    | 0.02em         | `on-surface-variant` |
| `caption`   | Space Grotesk | 10px  | 400    | 0.02em         | `muted`              |

---

## 3. Spacing System

- **Base unit:** `4px`
- **Scale:** `spacing-{n}` = `n × 4px`

| Token       | Value |
|-------------|-------|
| `spacing-1` | 4px   |
| `spacing-2` | 8px   |
| `spacing-3` | 12px  |
| `spacing-4` | 16px  |
| `spacing-5` | 20px  |
| `spacing-6` | 24px  |
| `spacing-8` | 32px  |
| `spacing-10`| 40px  |
| `spacing-12`| 48px  |
| `spacing-16`| 64px  |

---

## 4. Border Radius

| Token       | Value | Usage                          |
|-------------|-------|--------------------------------|
| `radius-none` | `0px` | **All containers, buttons, inputs, cards** |

> The design system enforces **zero-radius everywhere**. Sharp corners are a core identity trait.
> Exception: Avatar circles use `border-radius: 50%`.

---

## 5. Elevation & Depth

- **Zero Shadow Policy** — no `box-shadow` for hierarchy.
- Hierarchy conveyed solely via tonal layering (background color shifts).
- **Glassmorphism** (command palettes only): `backdrop-blur: 12px`, `opacity: 0.6`, on `surface-container-low`.
- Transitions: `0.1s–0.2s` linear or expo-out. Never bouncy.

---

## 6. Component Patterns (observed across screens)

### Cards
- Background: `surface-container` (`#1F1F1F`)
- No border, no shadow, no radius
- Internal padding: `spacing-4` to `spacing-6`
- Separation between cards: `spacing-4` vertical gap (no divider lines)

### Buttons
- **Primary:** `accent-purple` (`#A855F7`) bg, `#000000` text, `0px` radius. Hover: 1px `matte-silver` border.
- **Ghost/Tertiary:** Transparent bg, 1px `outline-variant` border. Text: `on-surface-variant`.

### Badges / Chips
- Font: `label-sm` (Space Grotesk 12px)
- Border: `outline-variant` at low opacity
- No filled background unless status is "Critical" (then `error-container`)
- Used for: tech tags, skill labels, severity indicators

### Node Chips (Graph Nodes)
- Small pill with Space Grotesk label
- Connected by SVG path lines using `accent-teal` or `outline-variant`
- Active node: `surface-tint` (`#DDB7FF`) glow or `primary-container` bg
- Bridge nodes: special holographic/wireframe treatment with purple glow

### Input / Command Palette
- Background: `#000000` (true black)
- Border: 1px solid `matte-silver` (`#222222`)
- Focus state: border shifts to `primary` (`#DDB7FF`) at 50% opacity
- Shortcut keys rendered in Space Grotesk inside `surface-container-high` chip

### Data Lists
- No horizontal dividers between rows
- Separation via `spacing-4` or `spacing-6`
- Selection state: bg shifts to `surface-bright` (`#393939`) + 2px purple indicator bar on left edge

### Avatar
- Circular (`border-radius: 50%`)
- Size variants: 24px, 32px, 40px
- Fallback: first-letter initial on `surface-container-high` bg

### Sidebar Navigation
- bg: `surface-container-lowest` (`#0E0E0E`)
- Active item: `surface-container` bg + `accent-purple` left indicator bar (2px)
- Items: icon + label in `body-md`, separated by `spacing-2`

---

## 7. Screen Inventory (from Stitch)

| Screen ID | Title                                 | Size       |
|-----------|---------------------------------------|------------|
| `db01...` | RecruitGraph Dashboard                | 2560×2048  |
| `7e7c...` | Network Path Visualization            | 2560×2300  |
| `d389...` | Tech Stack Analysis                   | 2560×2246  |
| `45dc...` | Bridge Node Graphic (hero/schematic)  | 1024×1024  |
| `a60c...` | Network Path Visualization (Rounded)  | 2560×2300  |
| `8bc3...` | Tech Stack Analysis (Rounded)         | 2560×2246  |
| `6dc3...` | RecruitGraph Dashboard (Rounded)      | 2560×2048  |
