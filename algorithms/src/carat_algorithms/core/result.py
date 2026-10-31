"""The single result vocabulary shared by every check."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    REVIEW = "REVIEW"
    NOT_CHECKED = "NOT_CHECKED"
    ERROR = "ERROR"  # set by the backend runner when a check crashes, never by a check


class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    check_id: str
    status: CheckStatus
    reason_code: str
    explanation: str
    field_refs: tuple[str, ...]
    algorithm_version: int
