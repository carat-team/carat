package io.github.carat_team.carat.services.barcode;

import com.google.zxing.BarcodeFormat;
import org.springframework.stereotype.Component;

import java.util.Optional;

/**
 * Checks the length and the check digit of a decoded code.
 */
@Component
public class BarcodeValidator {

    private static final int GTIN_LENGTH = 14;
    // Chestny Znak code: "01" + GTIN-14 + "21" + serial number + optional fields
    private static final String GTIN_PREFIX = "01";
    private static final String SERIAL_PREFIX = "21";

    /**
     * @return a human-readable error, or empty if the code is valid
     */
    public Optional<String> validate(String text, BarcodeFormat format) {
        if (text.isEmpty()) {
            return Optional.of("Empty code");
        }

        return switch (format) {
            case EAN_13 -> validateGs1Number(text, 13);
            case EAN_8, UPC_E -> validateGs1Number(text, 8);
            case UPC_A -> validateGs1Number(text, 12);
            case ITF -> validateItf(text);
            case DATA_MATRIX -> validateChestnyZnak(text);
            default -> Optional.empty();
        };
    }

    private Optional<String> validateGs1Number(String text, int length) {
        if (!isDigits(text)) {
            return Optional.of("Code must contain only digits");
        }
        if (text.length() != length) {
            return Optional.of("Expected " + length + " digits, got " + text.length());
        }
        if (!hasValidCheckDigit(text)) {
            return Optional.of("Wrong check digit");
        }
        return Optional.empty();
    }

    private Optional<String> validateItf(String text) {
        if (!isDigits(text)) {
            return Optional.of("Code must contain only digits");
        }
        if (text.length() % 2 != 0) {
            return Optional.of("ITF code must have an even number of digits");
        }
        // ITF-14 is a GTIN, shorter ITF codes have no check digit
        if (text.length() == GTIN_LENGTH && !hasValidCheckDigit(text)) {
            return Optional.of("Wrong check digit");
        }
        return Optional.empty();
    }

    private Optional<String> validateChestnyZnak(String text) {
        int serialStart = GTIN_PREFIX.length() + GTIN_LENGTH;
        boolean hasStructure = text.startsWith(GTIN_PREFIX)
            && text.startsWith(SERIAL_PREFIX, serialStart);
        if (!hasStructure) {
            return Optional.of("Not a Chestny Znak code: expected 01<GTIN>21<serial>");
        }
        if (text.length() == serialStart + SERIAL_PREFIX.length()) {
            return Optional.of("Empty serial number");
        }
        return validateGs1Number(text.substring(GTIN_PREFIX.length(), serialStart), GTIN_LENGTH);
    }

    private static boolean isDigits(String text) {
        return text.chars().allMatch(c -> c >= '0' && c <= '9');
    }

    // GS1: weights 3 and 1 alternate from the rightmost digit before the check digit
    private static boolean hasValidCheckDigit(String digits) {
        int sum = 0;
        for (int i = digits.length() - 2, weight = 3; i >= 0; i--, weight = 4 - weight) {
            sum += (digits.charAt(i) - '0') * weight;
        }
        int checkDigit = digits.charAt(digits.length() - 1) - '0';
        return (10 - sum % 10) % 10 == checkDigit;
    }
}
