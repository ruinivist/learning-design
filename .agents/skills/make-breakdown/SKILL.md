---
name: make-breakdown
description: Create or revise a concise sum-of-parts breakdown of a design problem, with focused UML SVGs that build understanding and recall. Requires an existing full design note; refuse when that prerequisite is missing.
---

# Make breakdown

Write a companion to a full design note that helps the reader reconstruct the solution one responsibility at a time. Each part should explain why the next piece is needed and how it connects to what already exists.

## Require the full note first

Locate and read the problem's existing full design note before creating or changing any breakdown files or diagrams. A qualifying note explains the model, responsibilities, and core behavior. A problem statement, code alone, a stub, or an existing breakdown does not satisfy this prerequisite. The filename need not follow a particular convention.

If no qualifying note exists, refuse to make the breakdown. State which problem lacks full notes and that the full design note must be written first. Do not create that note automatically, invent the missing design, or leave partial breakdown artifacts. If several notes could apply and the intended one is unclear, ask the user to identify it before writing.

Read applicable repository instructions and the relevant implementation, when present. Use the full note as the design context and the code to check concrete names and behavior. Resolve material contradictions before writing rather than choosing silently.

## Build a recall sequence

- Open with a link to the full note and a compact table of parts and what each adds.
- Choose parts around responsibilities that build on earlier parts. Let the problem determine their number and names; avoid a file-by-file or class-by-class tour.
- Establish core structure, ownership, and state before adding behavior. Split these into separate passes when it helps.
- For each later part, name the need it addresses, reuse the earlier objects, and introduce only the fields, relationships, or behavior needed to close that gap.
- Keep explanations short. Use concrete class and method names, with a few ordered steps where call order matters. Explain patterns at the point they solve a problem.
- Preserve invariants and failure ordering needed to understand each part. Leave the complete walkthrough, concurrency discussion, exhaustive fields, and pattern catalogs in the full note.
- End after the last useful part. Omit closing recaps, repeated ownership tables, and a second walkthrough joining everything together.

When revising a breakdown, preserve its useful part structure and remove repetition within it.

## Draw each part

Use [make-uml](../make-uml/SKILL.md) for editable SVGs. Give each part a focused diagram; split a part's diagram when structure and behavior or separate steps need different views.

Show only the classes and members relevant to that step. Repeat a class across diagrams with different selected members as the design grows. Simplified signatures and omitted implementation details are fine; preserve relationship meaning, ownership, and behavior. State once that the diagrams show selected members.

Save the breakdown beside the full note as `<problem>-breakdown.md`, with descriptive SVG filenames such as `<problem>-core-structure.svg`. Link each SVG where its part is introduced. Keep the full note and implementation unchanged unless the user also requests edits to them.

## Write and check

Apply `prose` while drafting, then `humanizer` while editing. Keep the finished note terse enough to use for recall. Replace duplicated field lists or interface sketches with the relevant diagram.

Check relative links and confirm the prose and diagrams agree. Follow make-uml's XML validation and rendered inspection requirements, reporting any inspection that could not be performed.

For the intended level of detail, read [the parking lot breakdown](<../../../Projects/Parking Lot/parking-lot-breakdown.md>) alongside [its full note](<../../../Projects/Parking Lot/parking lot.md>). Borrow the incremental approach, not its three-part outline or parking-specific classes.
