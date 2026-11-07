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

## Brand value check

`BrandValueCheck` validates `ProductCard.brand` independently of the product category. It compares the whole
normalized field with explicitly configured stop phrases. It does not search inside a brand, determine whether a
trademark is registered or reject an unfamiliar brand.

Normalization applies Unicode NFKC, `casefold`, trimming and whitespace collapsing. Punctuation is preserved.
The canonical value `Без товарного знака` is allowed by this implementation and is checked before configured rules.

The registry creates the check without a stop list. Until the team approves and supplies that list, an ordinary
non-empty brand returns `NOT_CHECKED / BRAND_VALUE_CONFIG_MISSING`. Preliminary candidates are not imported into
the runtime configuration.

An application can supply approved rules explicitly:

```python
from carat_algorithms.core import CheckConfig, get_checks
from carat_algorithms.text.brand_value import BrandValueCheck, BrandValueConfig, ForbiddenBrandValue

brand_value_config = BrandValueConfig(
    forbidden_values=(
        ForbiddenBrandValue("approved exact-only value"),
        ForbiddenBrandValue("approved fuzzy value", max_distance=0.05),
    )
)
check = BrandValueCheck(brand_value_config)
registered_checks = get_checks(check_config=CheckConfig(brand_value_config=brand_value_config))
```

The proposed V1 list requires an even more explicit import because it is not approved:

```python
from carat_algorithms.core import CheckConfig, get_checks
from carat_algorithms.text.brand_value.proposed import build_proposed_brand_value_config_v1

checks = get_checks(
    check_config=CheckConfig(brand_value_config=build_proposed_brand_value_config_v1())
)
```

`max_distance=None` means exact comparison only. This is the safe default for short values. A configured threshold
uses Jaro-Winkler distance, where `0` is identical and larger values are less similar. Thresholds are per phrase;
there is no shared default threshold. The distance scale and prefix weight `0.1` follow the
[RapidFuzz JaroWinkler normalized distance definition](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html),
but the implementation is local and adds no runtime dependency. Tests include the published `MARTHA` / `MARHTA`
control pair from the
[Winkler comparison table](https://www.niss.org/sites/default/files/winkler-presentation.pdf).

| Reason code | Status | Condition |
|---|---|---|
| `BRAND_VALUE_MISSING` | `NOT_CHECKED` | `brand` is absent |
| `BRAND_VALUE_EMPTY` | `WARNING` | `brand` is empty after normalization |
| `BRAND_VALUE_CANONICAL` | `PASS` | canonical `Без товарного знака` |
| `BRAND_VALUE_CONFIG_MISSING` | `NOT_CHECKED` | approved stop list is not configured |
| `BRAND_VALUE_FORBIDDEN` | `WARNING` | exact match with a configured stop phrase |
| `BRAND_VALUE_SIMILAR` | `REVIEW` | distance is within that phrase's configured threshold |
| `BRAND_VALUE_OK` | `PASS` | configured rules ran and found no match |

`PASS` only means that this check found no configured forbidden value. It does not confirm the legal status of a
brand. A similar match is sent to review and does not modify the card.

Explanations for empty and exactly forbidden values recommend the canonical fallback `Без товарного знака` when
the product has no trademark. A similar-value explanation keeps the submitted value, matched stop phrase,
distance and threshold, and presents the same fallback as a conditional manual-review recommendation.

### Preliminary candidates

`PROPOSED_BRAND_STOP_PHRASES_V1` is proposed for review and has not been approved by the team. It is kept in
`text.brand_value.proposed`, is not re-exported from `text.brand_value`, and is not runtime configuration unless a
caller explicitly builds and passes it. Source `A` means the task author's working hypothesis; source `X` means
the supplied export `Косметика и парфюмерия (все атрибуты).xlsx`. Counts use its three non-overlapping general
sheets, normalize case and whitespace, and keep punctuation.

| Proposed phrase | Count | Source | Mode | Preliminary max distance |
|---|---:|---|---|---:|
| `отсутствует` | 20135 | A, X | Jaro-Winkler | 0.07 |
| `нет товарного знака` | 5205 | X | Jaro-Winkler | 0.06 |
| `без бренда` | 1154 | A, X | Jaro-Winkler | 0.05 |
| `без торговой марки` | 5 | A, X | Jaro-Winkler | 0.05 |
| `без товарной марки` | 9 | X | Jaro-Winkler | 0.05 |
| `товарный знак отсутствует` | 19 | A, X | Jaro-Winkler | 0.06 |
| `нет` | 2230 | A, X | Exact | - |
| `без знака` | 2069 | X | Exact | - |
| `без тм` | 100 | A, X | Exact | - |
| `без тз` | 83 | X | Exact | - |
| `нет бренда` | 13 | X | Exact | - |
| `не указан` | 0 | A | Exact | - |
| `не указано` | 2 | X | Exact | - |
| `без марки` | 0 | A | Exact | - |
| `б/н` | 0 | A | Exact | - |
| `no brand` | 1 | A, X | Exact | - |
| `no name` | 14 | A, X | Exact | - |
| `noname` | 3 | A, X | Exact | - |
| `честный знак` | 289 | A, X | Exact | - |
| `-` | 144 | X | Exact | - |
| `n/a` | 6 | X | Exact | - |
| `none` | 1 | X | Exact | - |
| `нет в справочнике` | 5 | X | Exact | - |
| `без названия бренда` | 10 | X | Exact | - |
| `без указания бренда` | 11 | X | Exact | - |
| `товарного знака нет` | 1 | X | Exact | - |

The canonical value `без товарного знака` occurs 23277 times and remains allowed. Its spelling variants are a
separate review problem and are not stop phrases. Ambiguous values such as `noname pr`, observed 130 times, are not
included in V1.

The supplied CSV contains 47 malformed multiline `brand` records caused by unclosed quoting. Some values absorb
subsequent product rows and reach 31460 characters. These records were not silently repaired and were excluded as
a source of authoritative frequencies. The XLSX source has 37 multiline brand cells and a maximum brand length of
200 characters.

Jaro-Winkler is spelling similarity, not semantic matching. A shared fuzzy threshold is unsafe: for example,
`нет` and `не` have distance about `0.0889`, while `noname` and the possible brand `Noeme` have distance about
`0.1422`. Short stop phrases should remain exact-only unless separately evaluated against labeled data.

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

`ImageQualityCheck` version 3 applies EXIF orientation, composites transparency on
white, and bounds the working image to 1024 pixels before creating composite and BGR
copies. JPEG draft decoding reduces the source buffer where supported; PNG still
needs its source pixels decoded; palette/binary/16-bit modes and color-key alpha are normalized before filtered resizing. Resolution uses the original oriented dimensions,
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

Version 2 uses CPU ISNet with RGB Lanczos 1024x1024 preprocessing from rembg's
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

Version 2 bounds the image before white compositing and subsequent RGB copies,
using JPEG draft decoding where supported. Palette/binary/16-bit sources and color-key alpha are converted
before filtered resizing, preserving the same model input for identical pixels.
PNG still needs its source pixels decoded. Known malformed EXIF/image errors
return REVIEW for the affected photo; the final finding names its photo position.
An installed but broken model remains an operational ERROR from the runner,
rather than being reported as an absent model. Geometry/color diagnostics and the
cutout helper are retained for research and the follow-up photo-editing task.
