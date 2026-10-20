# Low-Level Design Practice

These projects are small, runnable programs for low-level design (LLD) interview
practice. Aim to demonstrate sound design through correct implementations that
can be written and explained within limited interview time.

## Priorities

- **Correctness:** Preserve invariants, validate inputs, and handle meaningful
  edge cases. A toy program should still behave correctly within its stated scope.
- **Design:** Make responsibilities, interfaces, ownership, and state transitions
  clear. Implement relevant design patterns enough to demonstrate their purpose
  and tradeoffs; avoid patterns that add ceremony without solving a real problem.
- **Concurrency:** Where shared mutable state or background work is involved,
  make synchronization, atomic operations, and lifecycle management explicit.
  Handle races and shutdown correctly; do not add threads to unrelated exercises.
- **Brevity:** Keep line counts low through narrow scope and simple code, while
  preserving readability and the design concepts being practiced.

## User preferences

- Prefer a nested function for a helper used by only one function or method.
  Define it near the top of its caller to keep its scope local and give the
  operation a clear name. Keep it separate when nesting would hurt readability
  or other callers need it.

## Scope and Validation

Implement the core use case and only the supporting behavior needed to exercise
the design. Favor a complete, explainable example over extra features, generic
frameworks, or production infrastructure. State simplifying assumptions explicitly.

Use focused tests or runnable assertions to demonstrate core behavior, boundary
conditions, and relevant concurrency guarantees. Keep explanations close to the
code and explain why a design choice fits the problem and what tradeoff it makes.

## Project Notes

When writing or updating a project's design notes, read these examples first:

- [Parking lot](<Parking Lot/parking lot.md>)
- [Rate limiter](<Rate Limiter/rate_limiter.md>)

Use short, plain English and concrete class/method names. Prefer compact lists
and tables. Avoid rhetorical questions, dramatic framing, and long explanations.
Read the implementation before documenting it; describe actual behavior.

Use this template, omitting sections that do not apply. Include only GoF patterns,
SOLID principles, and concurrency concerns clearly demonstrated by the code;
do not fill every category just to complete a checklist.

```markdown
# <Project> design

<Two short sentences: who coordinates, who owns state, what gets delegated.>

![<Project> UML class diagram](<project>-uml.svg)

## Reading the UML

1. **Start with <aggregate or entry point>:** its responsibility and owned state.
2. **Follow its collaborators:** what gets delegated and why; explain how a
   relevant pattern allows changes without changing the coordinator.
3. **Connect the data:** who owns it, how it supports those responsibilities,
   and how results return to the caller.

## Happy path

1. <Caller enters through a concrete method.>
2. <Trace successful calls, state changes, and relevant lock boundaries.>
3. <Finish with the result returned to the caller.>

## Design BOW

- **<Key idea>:** <Brief algorithm, ownership, or design detail.>

## GoF patterns

| Pattern | Where | Purpose |
| --- | --- | --- |
| <Pattern> | <Classes/methods> | <Problem it solves here> |

## SOLID principles

| Principle | Where / how |
| --- | --- |
| <Relevant principle> | <Concrete evidence in this implementation> |

## Concurrency

| Concern | Implementation |
| --- | --- |
| <Race or consistency issue> | <Protection, scope, and tradeoff> |

## common mistakes

- <Specific mistake and its correction, one or two lines each.>
```

Group the UML reading steps by responsibility, starting from the aggregate or
entry point and branching to related behavior and data. Explain the connections;
do not give a spatial tour of boxes. Keep the happy path separate: it traces one
successful operation end to end. Avoid redundant ASCII diagrams and setup snippets
when the UML and walkthrough already explain the design. Link an existing UML;
use the `make-uml` skill when creating or updating one.
