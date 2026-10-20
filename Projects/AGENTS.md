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

## Project notes

Use [make-notes](../.agents/skills/make-notes/SKILL.md) when creating or revising a project's full design notes. The skill defines the note structure, examples, and diagram guidance.
