package io.github.carat_team.carat.inference;

public record ImageQuality(
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
}
