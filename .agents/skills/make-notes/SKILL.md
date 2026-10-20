---
name: make-notes
description: Create or revise full design notes for the repository's project exercises, explaining responsibilities, behavior, design choices, and concurrency. Use for project design documentation, not general technical notes, incremental breakdowns, or code-only changes.
---

# Make notes

Write full design notes that help a reader understand and explain a project's implementation.

## Read before writing

Read applicable repository instructions and the relevant implementation. Describe actual behavior, including ownership, state changes, and failure handling.

Read these examples for the intended level of detail:

- [Parking lot](<../../../Projects/Parking Lot/parking lot.md>)
- [Rate limiter](<../../../Projects/Rate Limiter/rate_limiter.md>)

Borrow their approach, not their project-specific classes or policies.

## Explain the design

Use short, plain English and concrete class and method names. Prefer compact lists and tables. Avoid rhetorical questions, dramatic framing, and long explanations. Apply `prose` while drafting, then `humanizer` while editing.

Group the UML reading steps by responsibility. Start with the aggregate or entry point, then explain its collaborators and the data they share. Explain ownership and why behavior is delegated; avoid a spatial tour of boxes. Explain a pattern where it solves a concrete problem.

Keep the happy path separate: trace one successful operation from the caller through state changes and relevant lock boundaries to the returned result.

Include only GoF patterns, SOLID principles, and concurrency concerns demonstrated by the implementation. Omit sections that do not apply rather than filling every category. State relevant tradeoffs and assumptions.

Link an existing UML diagram. Use [make-uml](../make-uml/SKILL.md) when creating or updating diagrams. Avoid redundant ASCII diagrams and setup snippets when the UML and walkthrough already explain the design.

Use [make-breakdown](../make-breakdown/SKILL.md) for a separate incremental recall guide when requested; this skill produces the full design note.

## Note structure

Keep the note beside its implementation and preserve its existing filename when revising it. Use this structure, omitting sections that do not apply:

```markdown
# <Project> design

<Two short sentences: who coordinates, who owns state, what gets delegated.>

![<Project> UML class diagram](<project>-uml.svg)

## Reading the UML

1. Start with the aggregate or entry point: its responsibility and owned state.
2. Follow its collaborators: what gets delegated and why.
3. Connect the data: ownership, how it supports those responsibilities, and how results return.

## Happy path

1. Start with a concrete caller operation.
2. Trace successful calls, state changes, and relevant lock boundaries.
3. Finish with the result returned to the caller.

## Design choices

- Explain an algorithm, ownership decision, or implementation detail and its tradeoff.

## Design patterns

| Pattern | Where | Purpose |
| --- | --- | --- |
| <Pattern> | <Classes/methods> | <Problem it solves here> |

## Design principles

| Principle | Where / how |
| --- | --- |
| <Relevant principle> | <Concrete evidence in this implementation> |

## Concurrency

| Concern | Implementation |
| --- | --- |
| <Race or consistency issue> | <Protection, scope, and tradeoff> |

## Common mistakes

- Describe a specific mistake and its correction in one or two lines.
```

## Check the result

Check that concrete names, call order, ownership, and concurrency claims agree with the implementation. Check relative links and diagram references. Follow `make-uml` validation requirements for any changed diagrams.
