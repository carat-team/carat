package io.github.carat_team.carat.services.barcode;

import com.google.zxing.BarcodeFormat;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;

class BarcodeValidatorTest {

    private final BarcodeValidator validator = new BarcodeValidator();

    @Test
    void acceptsRetailCodesWithCorrectCheckDigit() {
        assertEquals(Optional.empty(), validator.validate("3614272049529", BarcodeFormat.EAN_13));
        assertEquals(Optional.empty(), validator.validate("96385074", BarcodeFormat.EAN_8));
        assertEquals(Optional.empty(), validator.validate("036000291452", BarcodeFormat.UPC_A));
    }

    @Test
    void rejectsWrongCheckDigit() {
        assertEquals(Optional.of("Wrong check digit"), validator.validate("3614272049520", BarcodeFormat.EAN_13));
    }

    @Test
    void rejectsWrongLengthAndNonDigits() {
        assertEquals(
            Optional.of("Expected 13 digits, got 12"),
            validator.validate("361427204952", BarcodeFormat.EAN_13)
        );
        assertEquals(
            Optional.of("Code must contain only digits"),
            validator.validate("36142720495A9", BarcodeFormat.EAN_13)
        );
    }

    @Test
    void checksItfLengthAndItf14CheckDigit() {
        assertEquals(Optional.empty(), validator.validate("8603095259", BarcodeFormat.ITF));
        assertEquals(Optional.empty(), validator.validate("14601234567890", BarcodeFormat.ITF));
        assertEquals(
            Optional.of("ITF code must have an even number of digits"),
            validator.validate("12345", BarcodeFormat.ITF)
        );
        assertEquals(Optional.of("Wrong check digit"), validator.validate("14601234567891", BarcodeFormat.ITF));
    }

    @Test
    void checksChestnyZnakStructureAndGtin() {
        assertEquals(
            Optional.empty(),
            validator.validate("0104600439931256215Q8H6t\u001d93abcd", BarcodeFormat.DATA_MATRIX)
        );
        assertEquals(
            Optional.of("Wrong check digit"),
            validator.validate("0104600439931257215Q8H6t", BarcodeFormat.DATA_MATRIX)
        );
        assertEquals(
            Optional.of("Empty serial number"),
            validator.validate("010460043993125621", BarcodeFormat.DATA_MATRIX)
        );
        assertEquals(
            Optional.of("Not a Chestny Znak code: expected 01<GTIN>21<serial>"),
            validator.validate("hello", BarcodeFormat.DATA_MATRIX)
        );
    }

    @Test
    void acceptsAnyNonEmptyCodeOfOtherFormats() {
        assertEquals(Optional.empty(), validator.validate("https://example.com", BarcodeFormat.QR_CODE));
        assertEquals(Optional.of("Empty code"), validator.validate("", BarcodeFormat.CODE_128));
    }
}
