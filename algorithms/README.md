# Algorithms

The library of product-card checks behind Carat. You give it a product card (attributes and photos), and each
check returns one result: a status, a reason code and a sentence in Russian that explains the verdict.

The library does not accept or reject cards. It reports what it found, and the consumer (the Carat frontend or
the Честный Знак services) applies its own policy.

It has no web server, no database and no network access. The backend imports it as a regular Python package,
and you can run and test every check without starting anything else.

## Setup

You need [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). uv installs Python 3.12 for you.

```sh
cd algorithms
just sync        # core dependencies only
just sync-all    # also the vision and ml extras, needed for the full test suite
just check       # lock check, ruff, pyright, pytest
```

From the repository root the same recipes run as `just algorithms <recipe>`.

| Recipe | What it does |
|---|---|
| `sync` / `sync-all` | Install dependencies (core / core + extras) |
| `lint` | `ruff check` and `ruff format --check` |
| `fix` | Apply ruff fixes and formatting |
| `typecheck` | `pyright` in strict mode |
| `test` | `pytest` |
| `check` | All of the above plus `uv lock --check`. Run it before every commit |

## How a check works

A check is a class with two attributes and one method:

```python
from carat_algorithms.core import CheckResult, CheckStatus, ProductCard


class BrandValueCheck:
    """The brand value "Без товарного знака" is not allowed."""

    check_id = "brand_value"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if card.brand is None:
            return self._result(CheckStatus.NOT_CHECKED, "BRAND_VALUE_MISSING", "Бренд не указан")
        if card.brand.strip().lower() == "без товарного знака":
            return self._result(CheckStatus.WARNING, "BRAND_VALUE_FORBIDDEN", 'Бренд "Без товарного знака" недопустим')
        return self._result(CheckStatus.PASS, "BRAND_VALUE_OK", "Бренд указан")

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("brand",),
            algorithm_version=self.algorithm_version,
        )
```

This example only shows the shape, not the real check

- `check_id` is a stable snake_case name. The frontend and stored results refer to it, so do not rename it.
- `algorithm_version` is an integer. Increase it by one whenever a change can give a different result for the
  same card: a new rule, a changed threshold, another model. Stored results keep the version they were made with,
  so you can still explain an old verdict after the rule changes.
- `field_refs` lists the card fields the verdict is based on, using the API names (`fullName`, `volume`).
  The frontend uses them to highlight the fields.

To make the backend run a check, add it to `get_checks()` in `src/carat_algorithms/core/registry.py`.

### Choosing a status

| Status | When |
|---|---|
| `PASS` | The rule ran and the card satisfies it |
| `WARNING` | The rule ran and found a likely problem |
| `REVIEW` | The rule cannot decide (ambiguous input, low confidence) and a person should look |
| `NOT_CHECKED` | Something the rule needs is missing: the field, a photo, or the card is out of scope |
| `ERROR` | The check crashed. The backend sets this status; a check never returns it |

A field set to `None` is absent from the card, which gives `NOT_CHECKED`. An empty string is a value the seller
entered, so a rule that needs text treats it as a finding.

When unsure, return `REVIEW`. Each false `WARNING` teaches users to ignore warnings.

The customer requirements (R1 to R8) live in [docs/requirements.md](../docs/requirements.md). Name the one your
check covers in the pull request description.

## Project layout

```
src/carat_algorithms/
  core/          ProductCard, CheckResult, CheckStatus, the Check protocol, the registry
  text/          checks on names and text attributes (volume, perfumery type, brand, ...)
  identifiers/   GTIN and other identifier validators
  vision/        photo checks: quality, background, barcode, OCR (need the vision extra)
tests/           mirrors src/; test data lives in tests/fixtures/
scripts/         developer tools such as evaluation against a labeled set; src/ never imports them
```

Each check gets its own subpackage, for example `text/volume/`, with its rules and parsing helpers.

## Dependencies

The core install is small (pydantic) so the backend and the tests start fast. Heavy libraries live in extras:

| Extra | For | Install |
|---|---|---|
| `vision` | Pillow, zxing-cpp, NumPy, OpenCV headless and ONNX Runtime (CPU) | `uv sync --extra vision` |
| `ml` | Model-based readers: EasyOCR on CPU torch | `uv sync --extra ml` |

Add a dependency with `uv add <package>` or `uv add --optional vision <package>`, and commit `uv.lock` with
`pyproject.toml`. Ask the team before adding anything that pulls in torch: it dominates the image size and memory.

## Tests

Tests use pytest. Rule tables go into `@pytest.mark.parametrize` with readable ids. When you fix a real mistake
from the Честный Знак catalog, add it as a named regression case.

Keep test data in `tests/fixtures/`. Images must be small (under 100 KB) or generated in the test.
Unit tests show that every rule works. Accuracy numbers (precision, recall) against a labeled set belong in
`scripts/` or `model/`.

## Model weights

Weights are never committed. They live in the repository's `weights/` directory, one subdirectory per model
family; docker mounts the same directory. The backend passes the whole directory (its `WEIGHTS_DIR` setting) to
the reader (`OcrReader(weights_dir)`). The reader picks its own subdirectory (`easyocr/`) and never downloads
anything on its own. A new model family only needs a new subdirectory, no new setting.

| Used by | File in `weights/easyocr/` | Source | MD5 |
|---|---|---|---|
| `vision/ocr` (text detection) | `craft_mlt_25k.pth` | [craft_mlt_25k.zip](https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip) | `2f8227d2def4037cdb3b34389dcf9ec1` |
| `vision/ocr` (Russian and English text) | `cyrillic_g2.pth` | [cyrillic_g2.zip](https://github.com/JaidedAI/EasyOCR/releases/download/v1.6.1/cyrillic_g2.zip) | `19f85f43d9128a89ac21b8d6a06973fe` |

The quickest way to fetch both files is to let EasyOCR download them once:

```sh
uv run --extra ml python -c "import easyocr; easyocr.Reader(['ru', 'en'], gpu=False, model_storage_directory='weights/easyocr')"
```

## Photo quality preprocessing

`ImageQualityCheck` version 2 applies EXIF orientation, composites transparency on
white, and bounds the working image to 1024 pixels before creating composite and BGR
copies. JPEG draft decoding reduces the source buffer where supported; PNG still
needs its source pixels decoded; palette/binary modes are converted before filtered resizing. Resolution uses the original oriented dimensions,
not the working copy. Existing metric thresholds are retained. Findings include
the photo number, original dimensions, measured value and configured reference
values. Known malformed-image decoder and OpenCV errors return REVIEW per photo;
unexpected runtime/resource failures remain ERROR from the backend runner.

### Background segmentation

`get_checks(weights_dir)` registers `background` and reads
`<weights_dir>/isnet/isnet-general-use.onnx` lazily. The backend passes
`settings.weights.dir` (configured by `WEIGHTS_DIR`). With no model installed,
the check returns `NOT_CHECKED` / `BACKGROUND_WEIGHTS_MISSING`; it never downloads weights.

- Source: [rembg ISNet general-use release](https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx).
- Filename: `isnet-general-use.onnx`; target: `weights/isnet/isnet-general-use.onnx`.
- MD5 published by rembg: `fc16ebd8b0c10d971d3513d564d01e29`.
- SHA256 verified during migration: `60920e99c45464f2ba57bee2ad08c919a52bbf852739e96947fbb4358c0d964a`.

Version 1 uses CPU ISNet with RGB Lanczos 1024x1024 preprocessing from rembg's
`DisSession`: divide by the image maximum and subtract 0.5, normalize the output
mask to 0..255, then resize to the working image. Analysis uses an RGB copy with
long side at most 512, EXIF orientation applied and transparency on white.
Masks use threshold 127. Components at least 10% of the largest are parts of the
product (for example bottle and box); smaller objects covering at least 0.5%
of the frame are foreign. A quadratic Lab background model permits soft gradients;
the original delta-E thresholds (10 and 25), 95% uniformity and 2% maximum edge
density are retained. Clean, noisy/foreign, and undecidable photos map to
`PASS`, `WARNING`, and `REVIEW`; a warning takes precedence across photos.

`vision.background.cutout.cutout_product(image, mask)` preserves the original
pure product crop helper with soft alpha. Publishing edited photos through an
API is a separate task; this PR uses the existing card-check endpoint.
The old Java/gRPC implementation is replaced, not run alongside the Python backend.
