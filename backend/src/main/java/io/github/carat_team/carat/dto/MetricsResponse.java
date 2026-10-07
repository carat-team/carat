package io.github.carat_team.carat.dto;

public record MetricsResponse(
    String databaseCallbackTime,
    String redisCallbackTime,
    String modelCallbackTime
) {
}
