package io.github.carat_team.carat.dto;

import io.github.duckysmacky.cogniflex.analysis.static_.Evidence;

public record EvidenceResponse(
    String ruleCode,
    double confidence,
    String matchedValue,
    String explanation
) {
    public static EvidenceResponse from(Evidence evidence) {
        return new EvidenceResponse(
            evidence.ruleCode(),
            evidence.confidence(),
            evidence.matchedValue(),
            evidence.explanation()
        );
    }
}
