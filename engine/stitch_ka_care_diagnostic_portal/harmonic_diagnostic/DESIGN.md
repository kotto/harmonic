---
name: Harmonic Diagnostic
colors:
  surface: '#16130d'
  surface-dim: '#16130d'
  surface-bright: '#3d3831'
  surface-container-lowest: '#110e08'
  surface-container-low: '#1f1b15'
  surface-container: '#231f19'
  surface-container-high: '#2e2923'
  surface-container-highest: '#39342d'
  on-surface: '#eae1d7'
  on-surface-variant: '#d2c5b2'
  inverse-surface: '#eae1d7'
  inverse-on-surface: '#343029'
  outline: '#9b8f7e'
  outline-variant: '#4e4637'
  surface-tint: '#eec068'
  primary: '#f2c36b'
  on-primary: '#412d00'
  primary-container: '#d4a853'
  on-primary-container: '#573d00'
  inverse-primary: '#7b5804'
  secondary: '#c8c6c5'
  on-secondary: '#313030'
  secondary-container: '#474746'
  on-secondary-container: '#b7b5b4'
  tertiary: '#afcbff'
  on-tertiary: '#023061'
  tertiary-container: '#8fb0e9'
  on-tertiary-container: '#1d4274'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdea6'
  primary-fixed-dim: '#eec068'
  on-primary-fixed: '#271900'
  on-primary-fixed-variant: '#5d4200'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474746'
  tertiary-fixed: '#d6e3ff'
  tertiary-fixed-dim: '#a8c8ff'
  on-tertiary-fixed: '#001b3d'
  on-tertiary-fixed-variant: '#234779'
  background: '#16130d'
  on-background: '#eae1d7'
  surface-variant: '#39342d'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  gutter: 16px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style

This design system is engineered for a high-end medical diagnostic environment where precision meets holistic resonance. The brand personality is authoritative yet serene, positioning advanced healthcare as a harmonious alignment of data and wellness.

The visual direction follows a **Modern Corporate** foundation infused with **Glassmorphism** and **Tactile** accents. It leverages deep blacks and metallic golds to evoke a sense of "prestige medicine." The core metaphor is "Resonance"—represented through subtle glows, radial gradients, and light-bleed effects that mimic medical imaging and sonic waves. The UI should feel like a premium, dark-mode cockpit for health professionals.

## Colors

The palette is strictly dark-mode to reduce eye strain in clinical environments and highlight critical data points.

- **Background & Surface:** The base is a pure charcoal black (`#0d0d0d`). Surfaces use `#1a1a1a` to create clear containment.
- **Resonance Gold:** The primary accent (`#d4a853`) is used for active states, branding, and high-value metrics. It should often be accompanied by a 15% opacity glow of the same hue.
- **Functional Semantics:** Red and Green are reserved for critical health alerts and successful diagnostic matches respectively.
- **Grradients:** Use "Harmonic Gradients" which transition from a transparent center to a soft `#d4a853` periphery for section highlights.

## Typography

This design system utilizes **Inter** exclusively to maintain a utilitarian and clinical aesthetic that balances the decorative "harmonic" elements.

- **Headlines:** Use tighter letter-spacing and bold weights to ground the interface.
- **Labels:** Use uppercase with increased letter-spacing for data descriptors and medical categories to ensure high scannability.
- **Hierarchy:** Ensure a clear distinction between diagnostic data (Body-LG) and secondary metadata (Label-SM).

## Layout & Spacing

The layout uses a **Fluid Grid** model to accommodate high-density medical data across various monitor sizes.

- **Grid:** A 12-column grid system on desktop, collapsing to 4 columns on mobile. 
- **Rhythm:** An 8px linear scale governs all padding and margins. 
- **Density:** Use generous "stack-lg" spacing between major diagnostic sections to allow the UI to breathe, but utilize "stack-sm" within data tables to maximize information density.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Subtle Glows** rather than traditional shadows.

- **Tier 1 (Base):** `#0d0d0d` - The canvas.
- **Tier 2 (Cards):** `#1a1a1a` - Containers for specific patient data or diagnostic modules.
- **Tier 3 (Overlay):** `#262626` - Modals and tooltips.
- **Resonance Border:** Elements of high importance feature a 1px border with a `0.1` alpha gold tint and a 4px outer blur to simulate a soft "harmonic" emission.

## Shapes

The shape language is **Soft** but disciplined. Use 4px (0.25rem) for standard UI controls like inputs and buttons to maintain a professional, medical look. Larger containers such as patient summary cards use 8px (0.5rem) to feel more approachable and modern. Avoid "pill" shapes unless used for status indicators (chips).

## Components

- **Buttons:** Primary buttons use a solid Gold (`#d4a853`) fill with black text. Secondary buttons use a transparent background with a 1px Gold border and a subtle hover glow.
- **Data Cards:** Cards should feature a top-aligned gradient stroke (Gold to Transparent) to indicate "resonance."
- **Inputs:** Dark backgrounds (`#121212`) with a subtle bottom-only border. On focus, the border transitions to Gold with a soft 2px outer shadow.
- **Chips:** Status indicators use low-opacity fills (e.g., 10% Success Green) with high-intensity text to ensure legibility without overwhelming the dark background.
- **Waveform Visualizer:** A proprietary component for this design system, using SVG paths with a gold-to-transparent linear gradient to represent pulse or harmonic data.