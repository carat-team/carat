# Carat

Carat is a platform for checking product-card submissions for the Honest Sign (Честный Знак) marking system. The current work focuses on perfumery: product names, declared attributes, brands and product photos.

Carat started as a fork of [Cogniflex](https://github.com/duckysmacky/cogniflex), an AI-content detector. That code
was removed; its last state is kept under the git tag `legacy/java-backend`.

## Repository layout

| Directory | What | Stack |
|---|---|---|
| [algorithms/](algorithms/README.md) | The checks: a library with no server and no database | Python 3.12, uv |
| [backend/](backend/README.md) | REST API: stores cards and photos, runs the checks | Python 3.12, FastAPI, PostgreSQL, S3 |
| [frontend/](frontend/README.md) | Web UI | React 19, TypeScript, Vite |
| [model/](model/README.md) | Research, training and evaluation; not deployed | Python, PyTorch, Jupyter |
| [docs/](docs/) | API contract, customer requirements, how-to guides (Russian) | Markdown |
| `weights/` | Model weights, one subdirectory per model family; never committed | - |

```text
frontend --REST--> backend --imports--> algorithms
                      |
            PostgreSQL + S3 (RustFS)
```

The backend imports `algorithms` as a package, so a check runs in the same process as the API. `model/` produces
weights and measurements; nothing imports it.

## Run with Docker

1. Copy `.env.example` to `.env` and fill in at least `DB_PASSWORD`, `S3_ACCESS_KEY` and `S3_SECRET_KEY`.
2. Put the model weights into `weights/` as described in the [algorithms README](algorithms/README.md#model-weights).
   The backend starts without them; only model-based checks need them.
3. Start the stack:

```sh
docker compose up --build
```

Compose starts PostgreSQL, RustFS (S3-compatible photo storage), a one-off migration container and the backend.
The API listens on `http://localhost:8080` and `/docs` shows the interactive API.

## Develop

You need [uv](https://docs.astral.sh/uv/), [just](https://just.systems/) and Docker. For the frontend, Node 24 and
yarn. The root `justfile` delegates to each Python project:

```sh
just sync              # install dependencies of algorithms/ and backend/
just check             # lock check, ruff, pyright and pytest in both projects
just backend run       # API on http://localhost:8080, needs PostgreSQL and S3 from .env
just algorithms check  # one project only
```

Each project README covers its own setup, settings and tests.

## Documentation

- [docs/api.md](docs/api.md): the REST contract between frontend and backend.
- [docs/requirements.md](docs/requirements.md): customer requirements R1-R8, the source for which checks exist.
- [docs/how-to-add-a-check.md](docs/how-to-add-a-check.md): adding a new check, step by step.
- [Project wiki](https://taiga.nikdor.xyz/project/cogniflex/wiki/arkhitektura-proekta) and the
  [GitHub workflow guide](https://taiga.nikdor.xyz/project/cogniflex/wiki/gaid-po-rabote-s-github) on Taiga.

## Contributing

Branch from `dev` and open a pull request into `dev`; maintainers promote `dev` to `master`. Run `just check` (and
the frontend checks for frontend changes) before pushing. [REVIEW.md](REVIEW.md) lists what reviewers look for.
