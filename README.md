# Carat

Carat is a platform for checking product-card submissions for the Honest Sign (Честный Знак) marking system. The current work focuses on perfumery: product names, declared attributes, brands and product photos.

Carat grew out of [Cogniflex](https://github.com/duckysmacky/cogniflex). The repository still contains its AI-content analysis core. The current integrated API returns human/ai results for individual text or media inputs. Product-card validation is being developed and is not yet a complete integrated workflow.

## Project documentation

- [Project architecture](https://taiga.nikdor.xyz/project/cogniflex/wiki/arkhitektura-proekta)
- [ML-service architecture task](https://taiga.nikdor.xyz/project/cogniflex/us/51)
- [GitHub workflow](https://taiga.nikdor.xyz/project/cogniflex/wiki/gaid-po-rabote-s-github)
- [Frontend guide](https://taiga.nikdor.xyz/project/cogniflex/wiki/gaid-po-rabote-s-frontend)

The project Wiki holds the detailed architecture and team guides. The ML-service architecture link currently points to its task; a Wiki-page link can be added after that page is published.

## Repository layout

| Directory | Purpose | Stack |
| --- | --- | --- |
| backend/ | REST API, analysis orchestration and persistence | Java 25, Spring Boot 4, Gradle |
| inference/ | Internal model-serving service | Python 3.12, uv, gRPC, PyTorch CPU |
| frontend/ | Product-card UI under development | React 19, TypeScript, Vite |
| model/ | Research, training and evaluation | Python, PyTorch, Jupyter |
| proto/ | Shared backend/inference contracts | Protocol Buffers |

~~~text
Frontend --REST--> Backend --gRPC--> Inference
                       |
                PostgreSQL + Redis
~~~

Research code in model/ is not deployed by importing it into inference/. Model artifacts are supplied separately.

## Development status

The integrated inference service currently uses RoBERTa and ResNet models for the inherited AI-content checks. Its video RPC uses a mock detector and must not be treated as a supported production check.

SigLIP 2 experiments for frame type and perfume classification are available in model/training/frame_classifier/. They have not yet been integrated into the inference service. Other product-card checks are being developed in separate branches and pull requests; their presence there does not mean that they are included in dev or a release.

The frontend contains a product-list route, a not-found route and a three-step product form scaffold. Product persistence and end-to-end card validation are still in development.

## Run the current services

1. Copy .env.example to .env and fill in the required settings.
2. Obtain the existing runtime model weights from the ML team using the sources documented in inference/README.md, and place them in inference/weights/ according to inference/config.yaml. The experimental SigLIP heads do not replace these runtime weights.
3. From the repository root, run:

~~~sh
docker compose up --build
~~~

Docker Compose starts the backend, inference service, PostgreSQL and Redis. The backend is available at http://localhost:8080 by default. Check /api/status. The frontend is not included in this Compose configuration; follow frontend/README.md for its development setup. Inference startup requires the configured weights.

For service-specific commands, see [backend agent/build guidance](backend/AGENTS.md), [inference README](inference/README.md) and [frontend README](frontend/README.md).

## Contributing

Create a task branch from the current dev and open a pull request into dev. Maintainers promote dev to master. Follow the [GitHub workflow guide](https://taiga.nikdor.xyz/project/cogniflex/wiki/gaid-po-rabote-s-github) and the repository's [agent guidance](AGENTS.md).

Keep datasets, model weights, secrets and generated build files out of normal source-code pull requests.
