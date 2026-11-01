# Rewrite progress

Update after every step. Stop for the user's manual review after each step. Steps are numbered as in `.context/python-rewrite/notes/rewrite-plan.md`.

Step 0 (context setup): done, issue folder `.context/python-rewrite/`.

| Step | Status | Notes |
|---|---|---|
| 1 Preserve (tag) | done | annotated tag `legacy/java-backend` on `fe69e60`, pushed to origin |
| 2 Inventory | done | Verified column filled; test cases in `port-fixtures.md` |
| 3 Delete and rename | done | `15b0452` removal, `ca50697` new backend instructions; Draft PR not opened yet (ask user) |
| 4 Scaffold algorithms | done | core models, Check protocol, empty registry, 4 tests; `a84263a` (includes docs/api.md int version) |
| 5 Scaffold backend | done | create_app, /health, CheckRunner + ERROR isolation test; `d0ed994` (README + AGENTS.md split) |
| 6 Root files | done | .gitignore, .env.example, root justfile; no CODEOWNERS (user); `eb518be` |
| 7 Port existing checks | done | GTIN `d9f9afc`, barcode `d361825`, OCR `4da4d71`; inferred rule removed `ef960b8` |
| 8 Backend features | done | reworked to CARAT_MVP: EAV tables, {attributes} bodies, photos in S3 (RustFS), rest/ + domain/ + bootstrap layout, settings.toml + DB_*/S3_* env; 21 backend tests pass; `55ff5aa` |
| 9 Frontend wiring | skipped | user: frontend team wires it from docs/api.md; frontend code untouched |
| 10 Docker and CI | done | backend/Dockerfile (uv builder, 1.59 GB, CPU torch), compose db + s3 (RustFS) + migrate + backend, settings.docker.toml, algorithms/backend-tests.yml, release matrix [backend], review instructions; compose e2e both checks PASS; `5ac7dac` docker, `d2819ce` CI |
| 11 Docs | done | root README rewritten, docs/how-to-add-a-check.md (Russian, example test verified), agent files trimmed, writing-style rule (no single-char arrows, em/en dashes) in root AGENTS.md + REVIEW.md |
| 12 Final check | todo | |
