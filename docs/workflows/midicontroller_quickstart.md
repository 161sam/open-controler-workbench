# MIDI Controller Quickstart

## Goal

Build a plausible first MIDI control surface without leaving the normal GeneratorWorkbench flow.

## Recommended Start

1. Use `Select Domain` and choose `MIDI Controller`.
2. In the Create panel, start with one of these templates:
   - `Finger Drum Pad Grid` for pad-first performance controllers
   - `Channel Strip` for a mixer-style lane
   - `Display And Navigation Module` for menu-driven devices
3. Apply a built-in preset if it matches your intent, then create the controller.

## First Useful Result

- `Finger Drum Pad Grid`: create the base pad matrix, then add `Place OLED Display` or `Place Utility Button` if you want transport or mode feedback.
- `Channel Strip`: keep the fader as the anchor, then place extra buttons or encoders around the strip.
- `Display And Navigation Module`: start with display plus push encoders, then refine spacing with move, snapping, and inline editing.

## Typical Next Steps

1. Add the most-used controls from the toolbar groups in this order:
   - `Performance Surface`
   - `Mixing`
   - `Navigation & Feedback`
   - `Buttons & Utility`
2. Move and align components directly in the 3D view.
3. Check panel spacing and keepouts.
4. Continue toward KiCad-oriented export once the control layout feels right.
