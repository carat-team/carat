package io.github.carat_team.carat.dto;

import jakarta.validation.constraints.NotBlank;

public record CreateTextDetectionRequest(
        @NotBlank
        String text
) {
}
