# model/AGENTS.md

Research, training and evaluation; adds to the root `AGENTS.md`.

`model/` is not deployed and never imported by `algorithms/` or `backend/`. It produces weights, measurements and
decisions. Inference code for a trained model lives in `algorithms/` (see "Model-based checks" there).

## Where code goes

| Code | Home |
|---|---|
| Training, fine-tuning, experiments, ablations, dataset building and cleaning | `model/` |
| Evaluation on labeled sets (precision, recall, F1, confidence intervals) | `model/` (or `algorithms/scripts/` for one check) |
| Weight export (ONNX, state_dict) and its checksum | `model/` |
| A rule, parser or validator that needs no model | `algorithms/` |
| Running the trained model for a check at request time | `algorithms/` |

If rules can solve a check, it goes to `algorithms/` first. Do not wrap a rule in a model "for later".

## Domain notes

- Inputs are ЧЗ product cards: name, brand, category, GTIN, OKPD2, TN VED codes and photos from fixed angles.
- Primary language is Russian; mixed Russian/Latin brand names are normal.

## Python rules

- Notebooks are allowed with outputs stripped before commit.
- Type hints on every function in `.py` files, `pathlib` for paths, `logging` in library code (scripts may print).
- Fixed random seeds; report the seed and the data split in the experiment README.
- Report confidence intervals when the test set has fewer than 1000 items.

## Data and weights

- Never commit weights, datasets, images, archives or CSV dumps, not even small ones "for now".
- Each experiment folder has a `README.md`: goal, data source and download link, command to reproduce, results
  table, known limits.
- Weights go to a separate branch or external storage (example: `chore/add-frame-classifier-weights`); record the
  filename and SHA-256 in the README.
- Small results files (`results/*.json`) may be committed.

## Handing a model to `algorithms/`

1. Export weights in the format `algorithms` expects (ONNX preferred); record checksum and source.
2. Write down the exact preprocessing and the threshold, with the evidence for the threshold.
3. Open a PR in `algorithms/` that loads the weights from the caller's weights directory
   (`<weights_dir>/<family>/`).
4. Model name, preprocessing and threshold are part of the check's `algorithm_version`.
