# Product volume validation

Rule-based validation for the criterion:
"The product quantity in the name contradicts the declared quantity."

The implementation does not use ML. It extracts explicit quantities from a
product name, normalizes compatible units, calculates unambiguous multipacks,
and compares the result with the structured product-card attribute.

## Usage

```python
from model.product_validation import check_volume

result = check_volume(
    name="Духи 4 × 5 мл",
    declared_volume=20,
    declared_unit="мл",
)

print(result["status"])  # ok
print(result["rule"])    # VOLUME_SET_MATCH
print(result["message"]) # 4 × 5 мл = 20 мл; заявлено 20 мл.
```

`check_volume` preserves the perfumery-specific behavior developed for the
current criterion. `check_quantity` is the generic entry point for other
product categories and accepts an optional `QuantityProfile`.

## Statuses

| Status | Meaning |
| --- | --- |
| `ok` | The extracted or calculated quantity matches the attribute. |
| `warning` | An unambiguous quantity contradicts the attribute. |
| `manual_review` | The notation is ambiguous or cannot be compared safely. |
| `not_checked` | Required input or a supported quantity is missing. |

The checker handles ordinary quantities, liters/milliliters, grams/kilograms,
`4 × 5 ml`, `4x5ml`, `4 шт. по 5 мл`, explicit sums, mixed compatible units,
missing or incomplete units, model-number collisions, and named total volume.
It does not infer the meaning of a unitless expression from the declared
attribute: `4 × 5` may describe dimensions rather than volume.

## Tests

Run from the repository root:

```bash
python -m unittest model.product_validation.tests.test_volume_check -v
```

The automated results describe rule coverage, not statistical accuracy.
Precision, recall, and F1 require an independently labeled dataset, which is
not included in this repository.
