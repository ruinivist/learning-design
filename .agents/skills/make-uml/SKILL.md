---
name: make-uml
description: Create or update UML SVG diagrams for this repository, following its notation guide and pen-and-paper visual style. Use for class, sequence, component, or deployment diagrams.
---

# Make UML

Create readable, standard UML as editable SVG, suitable for learning and copying
by hand. Prefer SVG over Mermaid unless the user requests another format.

## Source of truth

When working under `Projects/`, also read `Projects/AGENTS.md` for project-area
instructions before making changes.

Read `Systems/UML.md` from the repository root each time this skill is used.
Follow its current notation and personal color conventions; updates there take
precedence over the defaults below. Inspect its linked notation SVGs when the
requested diagram needs a more detailed example.

The visual defaults below are distilled from
`Projects/Rate Limiter/rate-limiter-uml.svg`. They are part of this skill; that
file is an optional layout example, not something that must be reread each time.

## Visual style

- Use a white canvas, white boxes, black text and connectors, and square corners.
  Avoid gradients, shadows, decorative icons, and large colored fills.
- Use `DejaVu Sans, sans-serif`. At the reference's 1500-unit canvas width,
  use roughly 31-unit bold titles, 25-unit bold class names, 20-unit members and
  labels, and 18–19-unit multiplicities. Scale consistently for other sizes.
- Center the diagram title and place a compact color legend below it. Center
  class names; left-align attributes and operations with about 18 units of
  inner padding and 30 units between text baselines.
- Draw box outlines, compartment dividers, and connectors at about 2 units.
  Use black open arrowheads and white-filled, black-outlined hollow triangles;
  keep their shapes clearly distinct. Use a visible dash pattern, such as `9 7`,
  for dashed connectors.
- Color names rather than entire boxes: blue `#1856a6` for logic, green
  `#18713a` for data/state, purple `#7435a0` for contracts. For messaging and
  problems, use the orange and red roles specified in `Systems/UML.md`.
  Keep arrows and UML symbols black. Color sequence participant headings
  consistently with their roles. Color must not carry UML meaning by itself.
- Give boxes generous whitespace and aligned rows or columns. Prefer right-angle
  connector routes through empty space. Keep labels off lines and arrowheads;
  size boxes to fit their longest signatures rather than shrinking text.
- Use white folded-corner notes with black borders for short architectural
  explanations, attached with dashed lines. Add a compact symbol legend when
  it helps the reader interpret unfamiliar relationships.

## Model and deliver

Read the relevant implementation or design notes before choosing entities and
relationships. Use class diagrams for structure, sequence diagrams for call
order, component diagrams for software boundaries, and deployment diagrams
for runtime placement.

For class diagrams, use name, attribute, and operation compartments as needed;
show visibility, types, `«abstract»`, and `{readOnly}` where applicable. Put
inheritance triangles at the parent, composition diamonds at the owner, and
multiplicities beside the relevant ends. Do not infer composition solely from
an object holding a reference. Distinguish dependencies from associations and
sequence replies from asynchronous messages using the current UML guide.

Write the SVG beside the relevant project or note, following existing filenames
such as `rate-limiter-uml.svg`. Include an SVG namespace, a fitting `viewBox`,
and an accessible title with `role="img"` and `aria-labelledby`. Escape XML text.
Link it from the relevant Markdown when requested or needed to expose the diagram.

Validate XML and marker references. Render and inspect the SVG when a renderer
is available, checking clipping, overlapping text, and connector endpoints.
Report if visual inspection could not be performed.
