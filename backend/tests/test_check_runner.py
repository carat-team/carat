from carat_algorithms.core import CheckResult, CheckStatus, ProductCard

from carat_backend.services.check_runner import CheckRunner


class PassingCheck:
    check_id = "always_pass"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=CheckStatus.PASS,
            reason_code="ALWAYS_PASS_OK",
            explanation="Проверка пройдена",
            field_refs=("fullName",),
            algorithm_version=self.algorithm_version,
        )


class CrashingCheck:
    check_id = "always_crash"
    algorithm_version = 3

    def run(self, card: ProductCard) -> CheckResult:
        raise RuntimeError("boom")


def test_crashing_check_becomes_error_and_others_still_run() -> None:
    runner = CheckRunner([CrashingCheck(), PassingCheck()], concurrency=1)

    crashed, passed = runner.run(ProductCard(full_name="Духи"))

    assert crashed.check_id == "always_crash"
    assert crashed.status is CheckStatus.ERROR
    assert crashed.reason_code == "CHECK_CRASHED"
    assert crashed.algorithm_version == 3
    assert passed.status is CheckStatus.PASS


def test_runner_without_checks_returns_empty_list() -> None:
    assert CheckRunner([], concurrency=1).run(ProductCard()) == []
