from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.text.name_compliance.rules import check_name_composition


class NameCompositionCheck:
    """Check product-name composition according to requirement R6."""

    check_id = "name_composition"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if card.full_name is None:
            return self._result(
                CheckStatus.NOT_CHECKED,
                "NAME_COMPOSITION_MISSING",
                "Наименование товара не указано.",
                ("fullName",),
            )

        if not card.full_name.strip():
            return self._result(
                CheckStatus.REVIEW,
                "NAME_COMPOSITION_EMPTY",
                "Наименование товара пустое.",
                ("fullName",),
            )

        finding = check_name_composition(
            card.full_name,
            card.perfumery_type,
        )

        return self._result(
            finding["status"],
            finding["rule"],
            finding["message"],
            finding["field_refs"],
        )

    def _result(
        self,
        status: CheckStatus,
        reason_code: str,
        explanation: str,
        field_refs: tuple[str, ...],
    ) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=field_refs,
            algorithm_version=self.algorithm_version,
        )
