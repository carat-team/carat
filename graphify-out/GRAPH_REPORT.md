# Graph Report - pr-migrations  (2026-11-03)

## Corpus Check
- 236 files · ~59,283 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: (none) 20, .ipynb 4, .log 3)

## Summary
- 1804 nodes · 2734 edges · 257 communities (111 shown, 146 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 144 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7f24a202`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- perfume_detection.py
- NVMe endpoint-readiness investigation
- Container
- Шкала состояний проекта
- checker.py
- Rules
- model_selection_prod.py
- ProductRegistrationStep.tsx
- «Духи / нет»
- check
- REVIEW.md
- compilerOptions
- Attempts
- analyze.api.ts
- pohuy/SKILL.md
- Recovery algorithm analysis
- permissions
- Backend Container
- ХУЕНИТИВЫ — ИНСТРУКЦИЯ ДЛЯ АГЕНТА
- compilerOptions
- Словарь: расширение
- Stop Slop
- new_issue.sh
- CheckResult
- python-rewrite/ISSUE.md
- Decisions
- steps
- Findings
- with
- devDependencies
- frontend/AGENTS.md
- build_negatives.py
- Handoff
- <Issue title>
- Decisions
- perfume_detection.py
- Changelog
- services/photos.py
- Product
- Backend
- typing
- Firmware setup controls handoff
- Онтология предметной области
- carat-algorithms
- validator.py
- Carat analysis architecture
- Debug boot logging optimization
- rest/errors.py
- siglip_experiment.py
- final_evaluation.py
- barcode/test_check.py
- Structures to Avoid
- Attempts
- Decisions
- Findings
- Issue catalogue
- product.ts
- Riser and slot observations
- Huenitiv wordplay rules
- environment
- CheckStatus
- backend
- package.json
- model/README.md
- templates/CONNECTIONS.md
- Durable decision record
- Managed issue record
- FW-1427/CONNECTIONS.md
- follow-up-prompt.md
- x-backend-env
- Frontend Engineering Guidance
- ui/index.ts
- migrate
- vite-env.d.ts
- tsconfig.json
- scripts
- Caveman concise response voice
- Attempt record template
- Issue relationship record
- Confirmed technical finding record
- Issue handoff record
- core context files
- Button
- release.yml
- with
- investigate-first/SKILL.md
- .claude/CLAUDE.md
- Attempts
- tests/conftest.py
- algorithms/AGENTS.md
- PCI bus rebalance investigation attempts
- FW-1427 issue connections
- FW-1427 engineering handoff
- ML Research Workspace
- Machine Learning Dependency Stack
- Context Manager skill invocation
- Managed issue catalogue
- Deferred endpoint-recovery solution report
- 48-drive parallel topology
- 96-drive requirement
- neighboring-stack slack
- safe fallback
- bus allocation versus endpoint readiness
- dual-socket cascaded NVMe shelves
- FW-1427
- FW-1427 ticket discussion
- PCI BDF estimate
- setup bus reservation
- ATTEMPTS.md
- CONNECTIONS.md
- context-manager file schemas
- DECISIONS.md
- FINDINGS.md
- HANDOFF.md
- ISSUE.md
- cross-issue references
- File schemas
- volume/check.py
- db
- jobs
- steps
- s3
- constants.ts
- build-latest
- App.tsx
- pathlib
- Product
- compute_scores
- services
- interface
- interface
- healthcheck
- build-release
- lint-staged
- run_volume
- Investigate First Agent Interface
- FW-1427 PCIe NVMe enumeration issue
- Claude skill invocation guidance
- eslint.config.js
- vite.config.ts
- Model Research Workspace
- Issue-scoped persistent engineering context
- 48-drive cascade failure
- bus-window redistribution
- issue folder naming
- Evidence-ranked hypotheses
- Pohuy domain ontology
- Project-state severity scale
- Russian engineering idiom dictionary
- Pohuy Russian Engineering Voice
- Stop Slop release history
- Stop Slop skill overview
- Before-and-after prose examples
- Stop Slop core instructions
- Stop Slop prose editing
- Backend Java and Spring conventions
- Backend request analysis flow
- Frontend Claude Guidance
- Frontend README
- Backend JUnit Tests Workflow
- Claude Mention-triggered Workflow
- Claude Pull Request Review Workflow
- Release Image Build and Draft Workflow
- Carat AI-content analysis product
- schemas/products.py
- test_photos_api.py
- FW-1427/ISSUE.md
- Findings
- Bus-rebalance solution report
- FW-1427/FINDINGS.md
- Handoff
- PCI bus-allocation findings
- PCIe/NVMe discovery progress
- Recovery failure investigation — 2026-07-24
- Reliable discovery of cascaded external NVMe shelves
- settings.py
- load_settings
- bootstrap.py
- app.py
- Handoff
- Как добавить проверку
- ADR 0002. Store product photos in S3-compatible object storage
- Algorithms
- REST API бэкенда
- Blocking (must be fixed before merge)
- Carat
- Требования заказчика (Честный Знак)
- React + TypeScript + Vite
- test_check_service.py
- ProductCard
- get_checks
- core/__init__.py
- routers/checks.py

## God Nodes (most connected - your core abstractions)
1. `CheckResult` - 29 edges
2. `ProductRepository` - 27 edges
3. `ProductCard` - 26 edges
4. `Product` - 22 edges
5. `compilerOptions` - 21 edges
6. `check_volume()` - 19 edges
7. `Decisions` - 19 edges
8. `CheckStatus` - 18 edges
9. `compilerOptions` - 18 edges
10. `check_quantity()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `3. Напишите проверку` --references--> `ProductCard`  [INFERRED]
  docs/how-to-add-a-check.md → algorithms/src/carat_algorithms/core/card.py
- `2026-10-31 - Registry must import checks lazily` --references--> `get_checks()`  [INFERRED]
  .context/python-rewrite/FINDINGS.md → algorithms/src/carat_algorithms/core/registry.py
- `5. Зарегистрируйте проверку` --references--> `get_checks()`  [INFERRED]
  docs/how-to-add-a-check.md → algorithms/src/carat_algorithms/core/registry.py
- `Merged into `dev` and worth keeping` --references--> `CheckResult`  [INFERRED]
  .context/python-rewrite/notes/port-table.md → algorithms/src/carat_algorithms/core/result.py
- `2026-10-31 - algorithm_version is an integer` --references--> `number()`  [INFERRED]
  .context/python-rewrite/DECISIONS.md → algorithms/src/carat_algorithms/text/volume/parsing.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Context manager issue artifacts** — _agents_skills_context_manager_assets_templates_issue_managed_issue_record, _agents_skills_context_manager_assets_templates_findings_confirmed_technical_finding_record, _agents_skills_context_manager_assets_templates_attempts_attempt_record_template, _agents_skills_context_manager_assets_templates_decisions_durable_decision_record, _agents_skills_context_manager_assets_templates_connections_issue_relationship_record, _agents_skills_context_manager_assets_templates_handoff_issue_handoff_record [EXTRACTED 1.00]
- **Carat Docker Compose Service Topology** — docker_compose_docker_compose_deployment, docker_compose_backend_container, docker_compose_inference_container, docker_compose_postgresql_container, docker_compose_redis_container [EXTRACTED 1.00]
- **FW-1427 PCI allocation and recovery** — _agents_skills_context_manager_examples_fw_1427_issue_fw_1427_pcie_nvme_enumeration_issue, _agents_skills_context_manager_examples_fw_1427_notes_pci_bus_allocation_findings_per_stack_pci_bus_allocation_window, _agents_skills_context_manager_examples_fw_1427_notes_bus_rebalance_solution_report_topology_aware_pci_bus_rebalance, _agents_skills_context_manager_examples_fw_1427_notes_nvme_timing_investigation_deferred_endpoint_recovery_before_mmio_assignment [EXTRACTED 1.00]

## Communities (257 total, 146 thin omitted)

### Community 0 - "perfume_detection.py"
Cohesion: 0.17
Nodes (10): _barcode_groups(), evaluate(), load_images(), load_images_from_paths(), _load_one(), load_records(), make_splits(), print_eval() (+2 more)

### Community 1 - "NVMe endpoint-readiness investigation"
Cohesion: 0.22
Nodes (9): BAR classification, Common pattern, Failure signature A — identity absent, Failure signature B — identity valid, BAR invalid, Identity classification, Measurement, NVMe endpoint-readiness investigation, Observation boundary (+1 more)

### Community 2 - "Container"
Cohesion: 0.32
Nodes (8): wouter@^3.13.0, Container(), ProductPageFooter(), ProductPageFooterProps, ProductStepper(), PRODUCT_STEPS, ProductPage(), wouter

### Community 4 - "Шкала состояний проекта"
Cohesion: 0.08
Nodes (25): 10. Катастрофа — теряем данные, 1. Триумф — взлетело лучше, чем ждали, 2. Норма — работает как должно, 3. Мелочь — вопрос на пять минут, 4. Странность — непонятное поведение, 5. Возня — работа идёт, но через сопротивление, 6. Застой — ничего не движется, 7. Деградация — сыплется на глазах (+17 more)

### Community 5 - "checker.py"
Cohesion: 0.07
Nodes (19): check_quantity(), check_volume(), QuantityProfile, ambiguous_number(), calculation_message(), declared_number(), extract_amounts(), extract_explicit_total() (+11 more)

### Community 6 - "Rules"
Cohesion: 0.09
Nodes (20): caveman, Example output, How to invoke, See also, What it does, 1. Answer first, 2. Kill ceremony, 3. Short word (+12 more)

### Community 7 - "model_selection_prod.py"
Cohesion: 0.05
Nodes (14): MultitypePictureDetector, predict_text_prod(), prepare_text_prod(), RoBERTaDetectorProd, MultitypePictureDetector_test, PictureDetector, DeepfakeDataset, get_images_paths() (+6 more)

### Community 8 - "ProductRegistrationStep.tsx"
Cohesion: 0.18
Nodes (13): ContainerProps, Input(), InputProps, Select(), SelectOption, SelectProps, MOCK_DATA, OKPD2_OPTIONS (+5 more)

### Community 9 - "«Духи / нет»"
Cohesion: 0.12
Nodes (15): Веса, Внешний тест из одного источника (214 духов + 600 не-духов Myntra), Вывод, Выводы, Главная оговорка: артефакт источника, Данные, Данные, Духи / нет (+7 more)

### Community 10 - "check"
Cohesion: 0.05
Nodes (41): defaults, env, name, runs-on, services, steps, run, POSTGRES_DB (+33 more)

### Community 11 - "REVIEW.md"
Cohesion: 0.29
Nodes (5): Do not report, Frontend, How to review, Non-blocking, PR title and description

### Community 12 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+14 more)

### Community 13 - "Attempts"
Cohesion: 0.18
Nodes (10): 2026-05-21 - Increase root-port extra-bus reservation, 2026-06-08 - Force a 2:6 bus ratio between sockets, 2026-06-08 - Override the ratio in source corresponding to a packaged binary, 2026-06-26 - Override the reinstalled policy from a notification callback, 2026-07-17 - Enable two PCI segments and rebalance stack windows, 2026-07-20 - Add bounded identity and BAR retries during enumeration, 2026-07-21 - Retry controller-register reads in the NVMe driver, 2026-07-24 - Gate on link state and issue one leaf-port secondary-bus reset (+2 more)

### Community 14 - "analyze.api.ts"
Cohesion: 0.24
Nodes (4): analyzeApi, ExampleRequestData, ExampleRequestResponse, apiClient

### Community 15 - "pohuy/SKILL.md"
Cohesion: 0.20
Nodes (9): Auto-Clarity (мат выключается), Boundaries, Persistence, Активация, Правила, Словарь (рабочий минимум), Уровни, Хуенитивы (+1 more)

### Community 16 - "Recovery algorithm analysis"
Cohesion: 0.22
Nodes (8): Implementation boundaries, Placement, Policy budgets, Quarantine, Recovery algorithm analysis, Reset boundaries, Scope gate, State machine

### Community 17 - "permissions"
Cohesion: 0.07
Nodes (28): if, permissions, runs-on, steps, types, types, jobs, claude (+20 more)

### Community 18 - "Backend Container"
Cohesion: 0.70
Nodes (5): Backend Container, Docker Compose Deployment, Inference Container, PostgreSQL Container, Redis Container

### Community 19 - "ХУЕНИТИВЫ — ИНСТРУКЦИЯ ДЛЯ АГЕНТА"
Cohesion: 0.22
Nodes (8): Дозировка, Защита ядра, Как хуенитивить, Приставки, Стык и проверка, Ударение, ХУЕНИТИВЫ — ИНСТРУКЦИЯ ДЛЯ АГЕНТА, Эталоны

### Community 20 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+11 more)

### Community 21 - "Словарь: расширение"
Cohesion: 0.22
Nodes (8): Агенты и субагенты, Действия, Образность: восклицания, звукопись, присказки, Оценки и количества, Словарь: расширение, Состояния и статусы, Сущности, Чего в словаре нет — и не будет

### Community 22 - "Stop Slop"
Cohesion: 0.22
Nodes (8): Author, License, Quick start, Scoring, Skill Structure, Stop Slop, What it catches, What this is

### Community 23 - "new_issue.sh"
Cohesion: 0.14
Nodes (16): catalogue_path, context_dir, core_files, die(), issue_dir, now, require_value(), resolve_script_dir() (+8 more)

### Community 24 - "CheckResult"
Cohesion: 0.33
Nodes (3): GtinFormatCheck, test_explanation_names_the_gtin_and_the_problem(), test_gtin_format()

### Community 25 - "python-rewrite/ISSUE.md"
Cohesion: 0.08
Nodes (19): ADR 0001. Rewrite the project in Python and extract the algorithms library, Alternatives considered, Consequences, Context, Decision, Issue catalogue, Issues, Connections (+11 more)

### Community 27 - "Decisions"
Cohesion: 0.10
Nodes (19): 2026-10-31 - algorithm_version is an integer, 2026-10-31 - Backend depends on carat-algorithms[vision], 2026-10-31 - Backend installs every algorithms extra, 2026-10-31 - Legacy tag on dev head, 2026-10-31 - No "inferred" marker, no guillemets, 2026-10-31 - No throwaway check in the algorithms scaffold, 2026-10-31 - One commit per ported check, 2026-10-31 - Ported label checks report validity only (+11 more)

### Community 28 - "steps"
Cohesion: 0.08
Nodes (23): defaults, name, runs-on, steps, run, jobs, check, name (+15 more)

### Community 29 - "Findings"
Cohesion: 0.05
Nodes (29): downscaled_size(), _EasyOcrReader, OcrReader, TextBlock, FakeEasyOcr, test_creating_a_reader_does_not_load_the_model(), test_downscaled_size(), test_read_text_downscales_and_drops_low_confidence() (+21 more)

### Community 30 - "with"
Cohesion: 0.08
Nodes (23): permissions, runs-on, steps, jobs, claude-review, name, on, pull_request (+15 more)

### Community 31 - "devDependencies"
Cohesion: 0.09
Nodes (23): devDependencies, @babel/core@^7.29.0, babel-plugin-react-compiler@^1.0.0, eslint-config-prettier@10.1.8, husky@^9.1.7, lint-staged@^17.6.0, prettier@3.8.1, @types/babel__core@^7.20.5 (+15 more)

### Community 32 - "frontend/AGENTS.md"
Cohesion: 0.29
Nodes (6): Build and run, Checks before pushing, frontend/AGENTS.md, Layout, Rules, Stack

### Community 34 - "build_negatives.py"
Cohesion: 0.18
Nodes (6): main(), ParquetRows, listing_text(), main(), read_listings(), select()

### Community 36 - "Handoff"
Cohesion: 0.33
Nodes (5): Current state, Handoff, Last thing tried, Next step, Warning

### Community 37 - "<Issue title>"
Cohesion: 0.33
Nodes (5): Acceptance criteria, <Issue title>, Links, Scope, Summary

### Community 38 - "Decisions"
Cohesion: 0.33
Nodes (5): 2026-05-21 - Investigate platform bus allocation, 2026-06-08 - Limit scope to cascaded single-slot topology, 2026-06-08 - Reclaim capacity from lightly used I/O stacks, 2026-07-20 - Test shelf-side delay independently, Decisions

### Community 39 - "perfume_detection.py"
Cohesion: 0.16
Nodes (11): predict(), predict_proba(), to_batch(), train(), best_f1_threshold(), main(), report(), val_auc() (+3 more)

### Community 40 - "Changelog"
Cohesion: 0.33
Nodes (5): 2025-01-12, 2026-01-12, 2026-01-13, Added, Changelog

### Community 41 - "services/photos.py"
Cohesion: 0.27
Nodes (4): InvalidInputError, NotFoundError, _decoded_format(), PhotoService

### Community 42 - "Product"
Cohesion: 0.16
Nodes (9): Photo, ProductStatus, _photo(), _product(), ProductRepository, Base, PhotoRow, ProductAttributeRow (+1 more)

### Community 43 - "Backend"
Cohesion: 0.22
Nodes (9): API, Backend, Code layout, Configuration, Database and migrations, Design choices, How checks run, Setup (+1 more)

### Community 44 - "typing"
Cohesion: 0.15
Nodes (4): get_services(), delete_photo(), get_photo_content(), upload_photo()

### Community 45 - "Firmware setup controls handoff"
Cohesion: 0.40
Nodes (4): Control 1 — cascade bus allocation, Control 2 — cascade slot, Firmware setup controls handoff, Validation

### Community 46 - "Онтология предметной области"
Cohesion: 0.40
Nodes (4): Онтология предметной области, Предел ЗАЛУПЫ, Сопутствующие сущности, Ядро

### Community 50 - "validator.py"
Cohesion: 0.12
Nodes (21): CodeFormat, CodeProblem, _expand_upce(), _has_valid_check_digit(), _is_digits(), _validate_chestny_znak(), validate_code(), _validate_gs1_number() (+13 more)

### Community 52 - "Debug boot logging optimization"
Cohesion: 0.50
Nodes (3): Debug boot logging optimization, Keep, Remove

### Community 53 - "rest/errors.py"
Cohesion: 0.24
Nodes (6): _field_path(), _message(), register_error_handlers(), handle_invalid_input(), handle_request_validation(), validation_error_response()

### Community 54 - "siglip_experiment.py"
Cohesion: 0.22
Nodes (4): _as_tensor(), embed_images(), embed_texts(), zero_shot_scores()

### Community 55 - "final_evaluation.py"
Cohesion: 0.27
Nodes (6): bootstrap_binary(), ci(), frame_type_section(), macro_f1(), main(), perfume_section()

### Community 56 - "barcode/test_check.py"
Cohesion: 0.44
Nodes (7): run_on(), test_invalid_chestny_znak_code_is_a_warning(), test_no_photos_is_not_checked(), test_photo_without_code_needs_review(), test_same_code_on_two_photos_counts_once(), test_unreadable_photo_needs_review(), test_valid_codes_pass()

### Community 57 - "Structures to Avoid"
Cohesion: 0.05
Nodes (33): Before/After Examples, Example 1: Throat-Clearing + Binary Contrast, Example 2: Filler + Unnecessary Reassurance, Example 3: Business Jargon Stack, Example 4: Dramatic Fragmentation, Example 5: Rhetorical Setup, Adverbs, Business Jargon (+25 more)

### Community 62 - "product.ts"
Cohesion: 0.13
Nodes (12): Nullable, CardStatus, PerfumeryType, PhotoAngle, Product, ProductListItem, ProductPhoto, ProductStandardNumber (+4 more)

### Community 65 - "environment"
Cohesion: 0.30
Nodes (12): environment, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, S3_ACCESS_KEY, S3_BUCKET (+4 more)

### Community 66 - "CheckStatus"
Cohesion: 0.14
Nodes (12): CheckStatus, Merged into `dev` and worth keeping, New checks with no existing code (also after the rewrite), Not ported, Open PRs: out of scope, land after the rewrite, Port table: what to carry into the new layout, Blocking, Comments (+4 more)

### Community 67 - "backend"
Cohesion: 0.18
Nodes (11): container_name, depends_on, image, ports, restart, volumes, migrate, s3 (+3 more)

### Community 68 - "package.json"
Cohesion: 0.10
Nodes (28): dependencies, axios@^1.20.0, class-variance-authority@^0.7.1, clsx@^2.1.1, @hookform/resolvers@^6.0.0, react@^19.2.4, react-dom@^19.2.4, react-hook-form@^7.90.0 (+20 more)

### Community 76 - "x-backend-env"
Cohesion: 0.18
Nodes (11): x-backend-env, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, S3_ACCESS_KEY, S3_BUCKET (+3 more)

### Community 82 - "ui/index.ts"
Cohesion: 0.20
Nodes (3): TSelectOption, initialProducts, Product

### Community 83 - "migrate"
Cohesion: 0.20
Nodes (10): context, dockerfile, condition, db, build, command, container_name, depends_on (+2 more)

### Community 86 - "scripts"
Cohesion: 0.20
Nodes (10): scripts, build, dev, format, format:check, lint, lint:fix, prepare (+2 more)

### Community 95 - "Button"
Cohesion: 0.29
Nodes (6): Button(), ButtonProps, ButtonVariantProps, buttonVariants, NotFoundIllustration(), NotFoundPage()

### Community 96 - "release.yml"
Cohesion: 0.20
Nodes (9): name, on, push, permissions, contents, packages, branches, paths (+1 more)

### Community 97 - "with"
Cohesion: 0.20
Nodes (10): with, cache-from, cache-to, context, file, password, push, registry (+2 more)

### Community 100 - "Attempts"
Cohesion: 0.50
Nodes (3): 2026-10-31 16:00 - Steps 0-3 in one run, 2026-10-31 16:30 - Steps 4-6 in the working tree, Attempts

### Community 101 - "tests/conftest.py"
Cohesion: 0.18
Nodes (4): upgrade(), client(), database_url(), object_storage_url()

### Community 102 - "algorithms/AGENTS.md"
Cohesion: 0.25
Nodes (6): Dependencies, Layout, Model-based checks, Purity, Statuses, Tests

### Community 125 - "Deferred endpoint-recovery solution report"
Cohesion: 0.20
Nodes (10): Correctness constraints, Deferred endpoint-recovery solution report, Deferred sequence, Identity absent, Invalid BAR, Result, Summary, Two failure modes (+2 more)

### Community 146 - "File schemas"
Cohesion: 0.06
Nodes (28): `ATTEMPTS.md` - append-only log, `CONNECTIONS.md` - living document, `.context/ISSUES.md` — living document, `DECISIONS.md` - append-only log, Example of self-directed issue, Example of ticket-backed issue, Examples, File kinds (+20 more)

### Community 148 - "db"
Cohesion: 0.22
Nodes (9): container_name, environment, image, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+1 more)

### Community 149 - "jobs"
Cohesion: 0.22
Nodes (9): uses, uses, if, needs, runs-on, jobs, algorithms-tests, backend-tests (+1 more)

### Community 150 - "steps"
Cohesion: 0.33
Nodes (9): steps, steps, steps, GITHUB_TOKEN, env, id, name, run (+1 more)

### Community 151 - "s3"
Cohesion: 0.25
Nodes (8): RUSTFS_ACCESS_KEY, RUSTFS_SECRET_KEY, container_name, environment, image, restart, volumes, s3

### Community 153 - "build-latest"
Cohesion: 0.25
Nodes (8): if, needs, runs-on, strategy, strategy, build-latest, image, matrix

### Community 154 - "App.tsx"
Cohesion: 0.48
Nodes (3): App(), Header(), ProductListPage()

### Community 156 - "Product"
Cohesion: 0.21
Nodes (3): Product, ProductService, FixedProducts

### Community 157 - "compute_scores"
Cohesion: 0.24
Nodes (3): compute_scores(), main(), summarize()

### Community 158 - "services"
Cohesion: 0.33
Nodes (5): name, services, volumes, postgres_data, s3_data

### Community 159 - "interface"
Cohesion: 0.40
Nodes (4): interface, default_prompt, display_name, short_description

### Community 160 - "interface"
Cohesion: 0.40
Nodes (4): interface, default_prompt, display_name, short_description

### Community 161 - "healthcheck"
Cohesion: 0.40
Nodes (5): healthcheck, interval, retries, test, timeout

### Community 162 - "build-release"
Cohesion: 0.50
Nodes (4): if, needs, runs-on, build-release

### Community 163 - "lint-staged"
Cohesion: 0.67
Nodes (3): lint-staged, *.{css,scss,json,md}, *.{js,jsx,ts,tsx}

### Community 165 - "run_volume"
Cohesion: 0.70
Nodes (3): run_volume(), test_fractional_suffix_count_is_never_truncated(), test_registered_volume_check()

### Community 172 - "eslint.config.js"
Cohesion: 0.13
Nodes (14): eslint@^9.39.4, @eslint/js@^9.39.4, eslint-plugin-prettier@5.5.5, eslint-plugin-react-hooks@^7.0.1, eslint-plugin-react-refresh@^0.5.2, globals@^17.4.0, typescript-eslint@^8.56.1, eslint (+6 more)

### Community 174 - "vite.config.ts"
Cohesion: 0.20
Nodes (8): @tailwindcss/vite@^4.3.3, @rolldown/plugin-babel@^0.2.0, vite@^8.0.0, @vitejs/plugin-react@^6.0.0, @rolldown/plugin-babel, @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 226 - "schemas/products.py"
Cohesion: 0.13
Nodes (13): create_product(), get_product(), list_products(), update_product(), ApiModel, photo_url(), PhotoOut, ProductAttributes (+5 more)

### Community 231 - "test_photos_api.py"
Cohesion: 0.11
Nodes (21): blank_png(), render_barcode(), test_check_of_unknown_product_returns_404(), test_check_returns_one_result_per_registered_check(), create_product(), encode_image(), test_delete_removes_photo_and_its_content(), test_missing_perspective_is_a_validation_error() (+13 more)

### Community 232 - "FW-1427/ISSUE.md"
Cohesion: 0.22
Nodes (5): Boot matrix, FW-1427 verification procedure, Linux, UEFI Shell, Starting prompt

### Community 233 - "Findings"
Cohesion: 0.25
Nodes (8): 2026-05-21 - Root-port padding cannot enlarge the stack window, 2026-06-08 - Parallel and cascaded shelves consume bus windows differently, 2026-06-26 - A precompiled initialization component overwrites the supplied socket ratio, 2026-07-17 - The bus-number shortage is resolved, 2026-07-20 - Remaining losses have two endpoint-readiness signatures, 2026-07-24 - Aggressive passive retry and the first reset escalation were insufficient, 2026-07-31 - Deferred recovery produced the first 11-boot clean run, Findings

### Community 234 - "Bus-rebalance solution report"
Cohesion: 0.25
Nodes (8): Bus-rebalance solution report, Parallel versus cascade, Problem statement, Rebalance algorithm, Result and remaining issue, Safety and controls, Two allocation levels, Why the reported numbers were misleading

### Community 236 - "Handoff"
Cohesion: 0.29
Nodes (5): Current state, Handoff, Last thing tried, Next step, Warning

### Community 237 - "PCI bus-allocation findings"
Cohesion: 0.29
Nodes (6): Allocation model, Build-consumer discovery, Evidence that allocation is fixed, Final allocation direction, PCI bus-allocation findings, Why root-port padding failed

### Community 240 - "PCIe/NVMe discovery progress"
Cohesion: 0.33
Nodes (5): Current result, PCIe/NVMe discovery progress, Phase 1 — resource diagnosis, Phase 2 — intermittent endpoint failures, Recovery evolution

### Community 241 - "Recovery failure investigation — 2026-07-24"
Cohesion: 0.29
Nodes (6): Follow-up, Interpretation, Recovery failure investigation — 2026-07-24, Required changes, Results, Test context

### Community 242 - "Reliable discovery of cascaded external NVMe shelves"
Cohesion: 0.40
Nodes (5): Acceptance criteria, Links, Reliable discovery of cascaded external NVMe shelves, Scope, Summary

### Community 243 - "settings.py"
Cohesion: 0.16
Nodes (4): CheckSettings, DatabaseSettings, PhotoSettings, WeightsSettings

### Community 244 - "load_settings"
Cohesion: 0.31
Nodes (5): load_settings(), test_absolute_weights_dir_is_kept(), test_committed_settings_file_loads(), test_database_and_object_storage_come_from_the_environment(), test_relative_weights_dir_resolves_against_the_file()

### Community 246 - "bootstrap.py"
Cohesion: 0.11
Nodes (8): build_services(), Services, CheckRunner, CheckService, ObjectStorageSettings, create_session_factory(), create_photo_object_store(), PhotoObjectStore

### Community 247 - "app.py"
Cohesion: 0.22
Nodes (5): create_app(), health(), get_settings(), Settings, test_health_returns_ok()

### Community 249 - "Handoff"
Cohesion: 0.33
Nodes (5): Current state, Handoff, Last thing tried, Next step, Warning

### Community 250 - "Как добавить проверку"
Cohesion: 0.22
Nodes (9): 1. Выберите требование, 2. Создайте пакет, 3. Напишите проверку, 4. Выберите статус, 5. Зарегистрируйте проверку, 6. Напишите тесты, 7. Проверьте и откройте PR, Если нужна модель или тяжёлая библиотека (+1 more)

### Community 251 - "ADR 0002. Store product photos in S3-compatible object storage"
Cohesion: 0.40
Nodes (4): ADR 0002. Store product photos in S3-compatible object storage, Consequences, Context, Decision

### Community 252 - "Algorithms"
Cohesion: 0.25
Nodes (8): Algorithms, Choosing a status, Dependencies, How a check works, Model weights, Project layout, Setup, Tests

### Community 259 - "REST API бэкенда"
Cohesion: 0.25
Nodes (8): REST API бэкенда, Карточка, Карточка товара, Ошибки, Результат проверки, Строка каталога, Фото, Эндпоинты

### Community 260 - "Blocking (must be fixed before merge)"
Cohesion: 0.33
Nodes (6): Blocking (must be fixed before merge), Dependencies and files, Invalid placement and architecture consistency, Process, Python backend rules, Tests

### Community 262 - "Carat"
Cohesion: 0.33
Nodes (6): Carat, Contributing, Develop, Documentation, Repository layout, Run with Docker

### Community 263 - "Требования заказчика (Честный Знак)"
Cohesion: 0.50
Nodes (4): Выведено командой (не требование заказчика), Как пользоваться, Требования, Требования заказчика (Честный Знак)

### Community 264 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the ESLint configuration, React Compiler, React + TypeScript + Vite

### Community 265 - "test_check_service.py"
Cohesion: 0.31
Nodes (3): BlockingCheck, CountingStore, test_waiting_request_loads_no_photos_until_it_gets_a_slot()

### Community 266 - "ProductCard"
Cohesion: 0.19
Nodes (8): ProductCard, Check, CheckResult, CrashingCheck, PassingCheck, test_crashing_check_becomes_error_and_others_still_run(), test_runner_without_checks_returns_empty_list(), Steps (in order, each is one or a few commits)

### Community 267 - "get_checks"
Cohesion: 0.20
Nodes (5): Adding a check, get_checks(), BarcodeOnPhotoCheck, test_registered_check_ids_are_unique(), test_result_serializes_with_api_keys()

### Community 270 - "core/__init__.py"
Cohesion: 0.24
Nodes (3): CardModel, CardPhoto, Volume

## Knowledge Gaps
- **77 isolated node(s):** `VALID_KINDS`, `script_dir`, `templates_dir`, `context_dir`, `issue_dir` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 961 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **146 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_services()` connect `bootstrap.py` to `services/photos.py`, `get_checks`, `Backend`, `app.py`, `Decisions`, `Product`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `CheckResult` (e.g. with `Layout` and `Check`) actually correct?**
  _`CheckResult` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `VALID_KINDS`, `script_dir`, `templates_dir` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Шкала состояний проекта` be split into smaller, more focused modules?**
  _Cohesion score 0.07692307692307693 - nodes in this community are weakly interconnected._
- **Why does `CheckRunner` connect `bootstrap.py` to `CheckStatus`, `Blocking (must be fixed before merge)`, `test_check_service.py`, `ProductCard`, `Backend`, `Findings`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ProductRepository` (e.g. with `PhotoService` and `ProductService`) actually correct?**
  _`ProductRepository` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `checker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._