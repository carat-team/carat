from carat_algorithms.core import CheckResult, CheckStatus, ProductCard
from carat_algorithms.identifiers.gtin import validate_code
from carat_algorithms.vision.barcode.reader import DecodedCode, read_codes


class BarcodeOnPhotoCheck:
    """
    Barcodes found on the card photos have a valid structure and check digit.
    """

    check_id = "barcode_on_photo"
    algorithm_version = 1

    def run(self, card: ProductCard) -> CheckResult:
        if not card.photos:
            return self._result(CheckStatus.NOT_CHECKED, "BARCODE_ON_PHOTO_NO_PHOTOS", "У карточки нет фото")

        decoded = [read_codes(photo.content) for photo in card.photos]
        readable = [codes for codes in decoded if codes is not None]
        if not readable:
            return self._result(CheckStatus.REVIEW, "BARCODE_ON_PHOTO_UNREADABLE", "Не удалось открыть ни одно фото")

        codes: list[DecodedCode] = list(dict.fromkeys(code for photo_codes in readable for code in photo_codes))
        if not codes:
            return self._result(CheckStatus.REVIEW, "BARCODE_ON_PHOTO_NOT_FOUND", "На фото не найден штрихкод")

        for code in codes:
            problem = validate_code(code.text, code.code_format)
            if problem is not None:
                return self._result(
                    CheckStatus.WARNING,
                    "BARCODE_ON_PHOTO_INVALID_CODE",
                    f"Код {code.code_format} на фото: {problem.explanation}",
                )
        return self._result(
            CheckStatus.PASS, "BARCODE_ON_PHOTO_OK", f"Найдено кодов на фото: {len(codes)}, все корректны"
        )

    def _result(self, status: CheckStatus, reason_code: str, explanation: str) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            status=status,
            reason_code=reason_code,
            explanation=explanation,
            field_refs=("photos",),
            algorithm_version=self.algorithm_version,
        )
