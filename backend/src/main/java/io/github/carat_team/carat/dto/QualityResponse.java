package io.github.carat_team.carat.dto;

import io.github.carat_team.carat.inference.ImageQuality;
import io.github.carat_team.carat.inference.QualityVerdict;

public record QualityResponse(
    int sharpness,
    int overexposure,
    int underexposure,
    int resolution,
    int overall,
    QualityVerdict verdict,
    String weakest,
    int width,
    int height
) {
    public static QualityResponse from(ImageQuality quality) {
        return new QualityResponse(
            quality.sharpness(),
            quality.overexposure(),
            quality.underexposure(),
            quality.resolution(),
            quality.overall(),
            quality.verdict(),
            quality.weakest(),
            quality.width(),
            quality.height()
        );
    }
}
