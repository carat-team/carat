# model/AGENTS.md

Research, training and evaluation. Read the root `AGENTS.md` first.

`model/` is not deployed and is never imported by `algorithms/` or `backend/`. It produces three things:
weights, measurements and decisions. Production inference code for a trained model lives in
`algorithms/` (see `algorithms/AGENTS.md`, section "Model-based checks").

## Where code goes

| Code | Home |
|---|---|
| Training, fine-tuning, experiments, ablations | `model/` |
| Evaluation against labeled sets: precision, recall, F1, confidence intervals | `model/` (or `algorithms/scripts/` for a single check) |
| Dataset building and cleaning scripts | `model/` |
| Weight export (ONNX, state_dict) and the checksum | `model/` |
| A rule, parser or validator that needs no model | `algorithms/`, not here |
| Running the trained model for a check at request time | `algorithms/` |

If a check can be solved with rules, it goes to `algorithms/` first. Do not wrap a rule in a model "for later".

## Domain notes

- Inputs are product cards for ЧЗ: name, brand, category, GTIN, OKPD2, TN VED codes and photos from fixed angles.
- Primary language is Russian. Mixed Russian/Latin brand names are normal.
- Only the perfumery category is in scope (R1 in `docs/requirements.md`).
- Do not revive AI-content detection (human/ai verdicts, RoBERTa/ResNet detectors). It is not part of the customer request.

## Python rules

- uv only; `model/` has its own `pyproject.toml` and `uv.lock`. Notebooks are allowed, but strip outputs before commit.
- Type hints on every function in `.py` files. `pathlib` for paths. `logging` instead of `print` in library code
  (scripts may print results).
- Fixed random seeds. Report the seed and the data split in the README of the experiment.
- Report numbers with confidence intervals when the test set is under 1000 items.

## Data and weights

- Never commit weights, datasets, images, archives or CSV dumps. This includes small ones "just for now".
- Each experiment folder has a `README.md` with: goal, data source and download link, command to reproduce,
  results table, known limits.
- Weights go to a separate branch or external storage (current example: branch
  `chore/add-frame-classifier-weights`). Record filename and SHA-256 checksum in the README.
- Results files (`results/*.json`) are small and may be committed.

## Handing a model to `algorithms/`

1. Export weights in the format `algorithms` expects (ONNX preferred) and record checksum and source.
2. Write down the exact preprocessing and the threshold, with the evidence for the threshold.
3. Open a PR in `algorithms/` that loads the weights from a caller-provided directory.
4. The model name, preprocessing and threshold are part of the check's `algorithm_version`.
