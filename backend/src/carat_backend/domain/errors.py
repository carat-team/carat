class NotFoundError(Exception):
    pass


class InvalidInputError(Exception):
    """Input that passed schema validation but breaks a service rule, keyed by field name."""

    def __init__(self, fields: dict[str, str]) -> None:
        super().__init__(fields)
        self.fields = fields
