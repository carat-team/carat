from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.identifiers.gtin.validator import validate_gtin


class GtinFormatCheck:
    """
    The card's GTIN has a valid GS1 length and check digit.
    """

    check_id = "gtin_format"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if card.gtin is None:
            return self._result(CheckStatus.NOT_CHECKED, "GTIN_FORMAT_MISSING", "GTIN не указан")
        problem = validate_gtin(card.gtin)
        if problem is not None:
            return self._result(
                CheckStatus.WARNING, f"GTIN_FORMAT_{problem.reason}", f"GTIN {card.gtin}: {problem.explanation}"
            )
        return self._result(CheckStatus.PASS, "GTIN_FORMAT_OK", f"GTIN {card.gtin} корректен")

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("gtin",),
            algorithm_version=self.algorithm_version,
        )
