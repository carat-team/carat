# Port fixtures (step 2 inventory)

Everything read at tag `legacy/java-backend` (`fe69e60`). Source of the test cases ported in step 7.

## BarcodeValidator (`backend/src/main/java/io/github/carat_team/carat/services/barcode/BarcodeValidator.java`)

`validate(text, format) -> Optional<String>` (empty = valid). Rules:

- Empty text -> `"Empty code"` (any format).
- EAN_13 / EAN_8 / UPC_A -> GS1 number of length 13 / 8 / 12:
  non-digits -> `"Code must contain only digits"`; wrong length -> `"Expected N digits, got M"`;
  bad check digit -> `"Wrong check digit"`. Order: digits, length, check digit.
- UPC_E: if 8 digits, expand to UPC-A (ZXing `UPCEReader.convertUPCEtoUPCA`) and validate as 12-digit GS1;
  otherwise validate as 8-digit GS1 (gives the length/digits error).
- ITF: digits only; odd length -> `"ITF code must have an even number of digits"`; check digit only when length 14.
- DATA_MATRIX (Честный Знак): must start with `01`, then 14-digit GTIN, then `21` at index 16, else
  `"Not a Chestny Znak code: expected 01<GTIN>21<serial>"`; nothing after `21` -> `"Empty serial number"`;
  then validate the GTIN as 14-digit GS1.
- Any other format: valid if non-empty.
- GS1 check digit: weights 3,1 alternating from the rightmost digit before the check digit;
  `(10 - sum % 10) % 10 == last digit`.

UPC-E -> UPC-A expansion (ZXing): `upce[1:7]` = d1..d6, last = d6:
- d6 in 0,1,2: `d1 d2 d6 0000 d3 d4 d5`
- d6 = 3: `d1 d2 d3 00000 d4 d5`
- d6 = 4: `d1 d2 d3 d4 00000 d5`
- else: `d1 d2 d3 d4 d5 0000 d6`
Result = `upce[0] + middle + upce[7]`.

### Test cases (BarcodeValidatorTest)

| Text | Format | Expected |
|---|---|---|
| `3614272049529` | EAN_13 | valid |
| `96385074` | EAN_8 | valid |
| `036000291452` | UPC_A | valid |
| `3614272049520` | EAN_13 | Wrong check digit |
| `361427204952` | EAN_13 | Expected 13 digits, got 12 |
| `36142720495A9` | EAN_13 | Code must contain only digits |
| `04252614` | UPC_E | valid |
| `04252610` | UPC_E | Wrong check digit |
| `0425261` | UPC_E | Expected 8 digits, got 7 |
| `8603095259` | ITF | valid |
| `14601234567890` | ITF | valid |
| `12345` | ITF | ITF code must have an even number of digits |
| `14601234567891` | ITF | Wrong check digit |
| `0104600439931256215Q8H6t\x1d93abcd` | DATA_MATRIX | valid |
| `0104600439931257215Q8H6t` | DATA_MATRIX | Wrong check digit |
| `010460043993125621` | DATA_MATRIX | Empty serial number |
| `hello` | DATA_MATRIX | Not a Chestny Znak code: expected 01<GTIN>21<serial> |
| `https://example.com` | QR_CODE | valid |
| `` (empty) | CODE_128 | Empty code |

## BarcodeReader (`.../services/barcode/BarcodeReader.java`)

ZXing `GenericMultipleBarcodeReader(MultiFormatReader)` with `TRY_HARDER`, HybridBinarizer over RGB pixels.
Returns distinct `(text, format)` pairs, empty list when nothing is found. Image decode via Java ImageIO
(no WebP). zxing-cpp `read_barcodes(image, try_harder=True)` covers the same; Pillow decodes WebP.

### Test cases (BarcodeReaderTest)

| Image | Expected |
|---|---|
| EAN_13 `3614272049529` rendered 400x150 | one code, EAN_13 |
| DATA_MATRIX `0104600439931256215Q8H6t` rendered 200x200 | one code, DATA_MATRIX |
| blank 300x200 RGB | no codes |

Rendering helper: ZXing `MultiFormatWriter` -> black/white image. Python: `zxingcpp.create_barcode(...).to_image()`
(or `write_barcode` on older zxing-cpp).

## OcrDetector (`inference/app/detectors/ocr_detector.py`)

- `easyocr.Reader(languages, gpu=False, verbose=False)`; config: `languages [ru, en]`, `min_confidence 0.3`,
  `max_image_side 1600` (`inference/config.yaml`).
- `read_text(bytes)`: `ImageOps.exif_transpose(Image.open(...)).convert("RGB")`, downscale so the longer side is at
  most `max_image_side` (`scale = min(1, max_side / max(size))`, `round()` per side), `reader.readtext(np.asarray)`,
  keep `(text, confidence)` with `confidence >= min_confidence`.
- Weights: Dockerfile pre-downloads with `easyocr.Reader(['ru', 'en'], gpu=False)` (EasyOCR default
  `~/.EasyOCR/model`). For `ru` + `en` EasyOCR loads only `craft_mlt_25k.pth` and `cyrillic_g2.pth` (cyrillic covers Latin; checked in `easyocr.py` and by a real download). New code passes
  `model_storage_directory=weights_directory`, `download_enabled=False`.
- Torch pinned to CPU index: `[tool.uv.sources] torch = { index = "pytorch-cpu" }`, index
  `https://download.pytorch.org/whl/cpu`, `explicit = true`.
- Tests: only `test_ocr_client.py`, a manual gRPC script. Nothing to port; new unit test covers the resize rule.

## LabelScanService (`.../services/LabelScanService.java`)

Empty upload -> 400 "File is empty"; undecodable -> 400 "File is not a supported image". Logs only counts.
In the new layout: upload validation is the backend photo endpoint's job; an undecodable stored photo makes
`barcode_on_photo` return `REVIEW`/`NOT_CHECKED`, never raise.
