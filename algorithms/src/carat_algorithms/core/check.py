from typing import Protocol

from carat_algorithms.core.card import ProductCard
from carat_algorithms.core.result import CheckResult


class Check(Protocol):
    """
    A check that can be run on a product card.
    Each check must be registered in carat_algorithms.core.registry.get_checks() to be run.
    """

    check_id: str
    algorithm_version: int

    def run(self, card: ProductCard) -> CheckResult: ...
