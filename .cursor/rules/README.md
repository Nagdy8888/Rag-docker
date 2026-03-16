# .cursor/rules

Cursor workspace rules applied when working in this project.

## Rules

- **phased-development.mdc** — Enforces the 4-phase build plan: only work on the phase the user requests; do not skip ahead; refer to the plan file and complete docs per phase.

These rules ensure the RAG agent is built in order (Phase 1 → 2 → 3 → 4) and that documentation is completed for each phase.
