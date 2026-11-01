# Attempts

## 2026-10-31 16:00 - Steps 0-3 in one run

**Hypothesis:** Context setup, tag, inventory and deletion are mechanical and can run without stops (user allowed it).
**Result:** worked
**Details:** Tag pushed (`5df6239` -> `fe69e60`). Commits `5115fa3`, `15b0452`, `ca50697`. Ignored build output
(`backend/build`, `backend/.gradle`, `inference/.venv`, `inference/generated`, caches) deleted from disk so the
`new-backend/` move could land on a clean `backend/`. `graphify update .` run; graph not committed.
**Next:** User review, then step 4.

## 2026-10-31 16:30 - Steps 4-6 in the working tree

**Hypothesis:** Scaffolds can land as planned; user reviews before each is committed separately.
**Result:** worked
**Details:** `just check` at the root green (algorithms 4 tests, backend 3 tests); `/health` answered under uvicorn.
Deviations: no throwaway check (DECISIONS.md), `httpx2` instead of `httpx`, settings only hold `check_concurrency`
(DB, photo and weights settings arrive with steps 7/8), `.env.example` keeps the `DB_*` split used by compose.
`uv init` READMEs are empty placeholders until step 11.
**Next:** Commit steps 4, 5, 6 separately after review, then step 7.
