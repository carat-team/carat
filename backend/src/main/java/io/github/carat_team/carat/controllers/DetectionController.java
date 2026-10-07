package io.github.carat_team.carat.controllers;

import io.github.carat_team.carat.dto.AnalysisResultResponse;
import io.github.carat_team.carat.dto.CreateTextDetectionRequest;
import io.github.carat_team.carat.services.AnalyzeService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/analyze")
public class DetectionController {

    private final AnalyzeService analyzeService;

    public DetectionController(AnalyzeService analyzeService) {
        this.analyzeService = analyzeService;
    }

    @PostMapping("/text")
    public ResponseEntity<AnalysisResultResponse> analyzeText(
            @Valid @RequestBody CreateTextDetectionRequest request
    ) {
        AnalysisResultResponse response = analyzeService.analyzeText(request);
        return ResponseEntity.ok(response);
    }

    @PostMapping(value = "/media", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<AnalysisResultResponse> analyzeMedia(
            @RequestPart("file") MultipartFile file
    ) {
        AnalysisResultResponse response = analyzeService.analyzeMedia(file);
        return ResponseEntity.ok(response);
    }
}
