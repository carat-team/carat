# Handoff

**Last updated:** 2026-10-31 by Claude Code

## Current state

Steps 0-2 of [rewrite-plan.md](notes/rewrite-plan.md) are done (context folder, legacy tag pushed, inventory).
Per-step status: [rewrite-progress.md](notes/rewrite-progress.md).

## Last thing tried

Inventory of the merged port sources at `legacy/java-backend`, recorded in [port-fixtures.md](notes/port-fixtures.md).

## Next step

Step 3: delete the Java `backend/`, `inference/`, `proto/`, `.github/workflows/backend-tests.yml`, then move
`new-backend/` to `backend/`.

## Warning

- Stop for user review after every step; the user allowed steps 0-3 in one go, then stop before step 4.
- `docs/gRPC.md` and `docs/ai-*` were already deleted in `9f6d8da`.
- Context edits are committed once more at the end of the rewrite, not per step.
