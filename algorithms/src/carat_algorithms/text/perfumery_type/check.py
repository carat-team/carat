from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.text.perfumery_type.rules import check_perfumery_name


class PerfumeryTypeCheck:
    """Compare explicit perfume type markers with the declared type (R3)."""

    check_id = "perfumery_type"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if card.full_name is None or card.perfumery_type is None:
            return self._result(
                CheckStatus.NOT_CHECKED, "PERFUMERY_MISSING_INPUT", "Не указаны наименование или тип парфюмерии"
            )
        if not card.full_name.strip():
            return self._result(CheckStatus.REVIEW, "PERFUMERY_NAME_EMPTY", "Наименование товара пустое")
        if not card.perfumery_type.strip():
            return self._result(CheckStatus.REVIEW, "PERFUMERY_TYPE_EMPTY", "Тип парфюмерии пустой")
        finding = check_perfumery_name(card.full_name, card.perfumery_type)
        return self._result(finding["status"], finding["rule"], finding["message"])

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("fullName", "perfumeryType"),
            algorithm_version=self.algorithm_version,
        )
