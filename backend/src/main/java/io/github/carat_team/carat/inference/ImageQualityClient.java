package io.github.carat_team.carat.inference;

public interface ImageQualityClient {
    ImageQuality analyzeImageQuality(byte[] imageContent);
}
