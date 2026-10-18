package io.github.carat_team.carat.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.github.duckysmacky.cogniflex.analysis.AnalysisVerdict;

import java.util.List;

public record AnalysisResultResponse(
    AnalysisVerdict verdict,
    double confidence,
    List<EvidenceResponse> evidence,
    @JsonInclude(JsonInclude.Include.NON_NULL) QualityResponse quality
) {
    public AnalysisResultResponse {
        evidence = evidence == null ? List.of() : List.copyOf(evidence);
    }

    public AnalysisResultResponse(
        AnalysisVerdict verdict,
        double confidence,
        List<EvidenceResponse> evidence
    ) {
        this(verdict, confidence, evidence, null);
    }

    public AnalysisResultResponse(AnalysisVerdict verdict, double confidence) {
        this(verdict, confidence, List.of(), null);
    }
}
