from typing import Protocol

from carat_algorithms.core.card import ProductCard
from carat_algorithms.core.result import CheckResult


class Check(Protocol):
    check_id: str
    algorithm_version: int

    def run(self, card: ProductCard) -> CheckResult: ...
