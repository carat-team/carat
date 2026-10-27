package io.github.carat_team.carat.dto;

public record BarcodeResponse(
    String text,
    String format,
    boolean valid,
    String validationError
) {
}
