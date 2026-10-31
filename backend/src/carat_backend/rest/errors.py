from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from carat_backend.domain.errors import InvalidInputError, NotFoundError

# Request parts that mean nothing to the frontend: `body.attributes.volume.value` becomes `volume.value`
REQUEST_PARTS = {"body", "form", "query", "path"}
MESSAGES = {
    "missing": "Обязательное поле",
    "extra_forbidden": "Неизвестное поле",
    "greater_than": "Значение должно быть положительным числом",
    "string_too_long": "Слишком длинное значение",
    "string_pattern_mismatch": "Неверный формат",
    "literal_error": "Недопустимое значение",
}
WRONG_TYPE_MESSAGE = "Неверный тип значения"


def validation_error_response(fields: dict[str, str]) -> JSONResponse:
    # The frontend depends on this exact shape: change it only together with the frontend team
    return JSONResponse(status_code=422, content={"error": "VALIDATION_ERROR", "fields": fields})


def _message(error_type: str, fallback: str) -> str:
    if error_type in MESSAGES:
        return MESSAGES[error_type]
    if error_type.endswith(("_type", "_parsing")):
        return WRONG_TYPE_MESSAGE
    return fallback


def _field_path(location: Sequence[int | str]) -> str:
    parts = [str(part) for part in location]
    if parts and parts[0] in REQUEST_PARTS:
        parts = parts[1:]
    # Card fields are named without the wrapping object; a missing `attributes` itself keeps its name
    if len(parts) > 1 and parts[0] == "attributes":
        parts = parts[1:]
    return ".".join(parts)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    def handle_request_validation(request: Request, error: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for item in error.errors():
            fields.setdefault(_field_path(item["loc"]), _message(str(item["type"]), str(item["msg"])))
        return validation_error_response(fields)

    @app.exception_handler(InvalidInputError)
    def handle_invalid_input(request: Request, error: InvalidInputError) -> JSONResponse:
        return validation_error_response(error.fields)

    @app.exception_handler(NotFoundError)
    def handle_not_found(request: Request, error: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})
