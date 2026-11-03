from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.text.volume.checker import check_volume


class VolumeVsNameCheck:
    """Compare the quantity in a perfumery name with its declared volume (R5)."""

    check_id = "volume_vs_name"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if card.full_name is None or card.volume is None:
            return self._result(CheckStatus.NOT_CHECKED, "VOLUME_MISSING_INPUT", "Не указаны наименование или объём")
        if not card.full_name.strip():
            return self._result(CheckStatus.REVIEW, "VOLUME_NAME_EMPTY", "Наименование товара пустое")
        if not card.volume.unit.strip():
            return self._result(CheckStatus.REVIEW, "VOLUME_UNIT_EMPTY", "Единица объёма пустая")
        finding = check_volume(card.full_name, card.volume.value, card.volume.unit)
        return self._result(finding["status"], finding["rule"], finding["message"])

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("fullName", "volume"),
            algorithm_version=self.algorithm_version,
        )
