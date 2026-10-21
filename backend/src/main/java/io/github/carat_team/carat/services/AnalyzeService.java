package io.github.carat_team.carat.services;

import io.github.duckysmacky.cogniflex.analysis.AnalysisOrchestrator;
import io.github.duckysmacky.cogniflex.analysis.AnalysisResultSummary;
import io.github.duckysmacky.cogniflex.analysis.ContentItem;
import io.github.duckysmacky.cogniflex.analysis.ContentItemFactory;
import io.github.duckysmacky.cogniflex.analysis.score.FinalScore;
import io.github.carat_team.carat.dto.AnalysisResultResponse;
import io.github.carat_team.carat.dto.CreateHistoryItemRequest;
import io.github.carat_team.carat.dto.CreateTextDetectionRequest;
import io.github.carat_team.carat.dto.EvidenceResponse;
import io.github.carat_team.carat.dto.QualityResponse;
import io.github.carat_team.carat.inference.ImageQuality;
import io.github.carat_team.carat.inference.ImageQualityClient;
import io.github.duckysmacky.cogniflex.analysis.InputType;
import io.github.duckysmacky.cogniflex.analysis.MediaType;
import io.github.duckysmacky.cogniflex.processing.media.MediaParser;
import io.github.duckysmacky.cogniflex.processing.media.ParsedMedia;
import io.github.duckysmacky.cogniflex.processing.text.PreprocessedText;
import io.github.duckysmacky.cogniflex.processing.text.TextPreprocessingOptions;
import io.github.duckysmacky.cogniflex.processing.text.TextPreprocessor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;

@Service
public class AnalyzeService {
    private static final Logger log = LoggerFactory.getLogger(AnalyzeService.class);

    private final AnalysisOrchestrator analysisOrchestrator;
    private final ContentItemFactory contentItemFactory;
    private final HistoryService historyService;
    private final TextPreprocessor textPreprocessor;
    private final MediaParser mediaParser;
    private final ImageQualityClient imageQualityClient;

    public AnalyzeService(
        AnalysisOrchestrator analysisOrchestrator,
        ContentItemFactory contentItemFactory,
        HistoryService historyService,
        TextPreprocessor textPreprocessor,
        MediaParser mediaParser,
        ImageQualityClient imageQualityClient
    ) {
        this.analysisOrchestrator = analysisOrchestrator;
        this.contentItemFactory = contentItemFactory;
        this.historyService = historyService;
        this.textPreprocessor = textPreprocessor;
        this.mediaParser = mediaParser;
        this.imageQualityClient = imageQualityClient;
    }

    public AnalysisResultResponse analyzeText(CreateTextDetectionRequest request) {
        long startedAt = System.nanoTime();

        PreprocessedText text = textPreprocessor.preprocess(request.text(), TextPreprocessingOptions.forModelInput());
        ContentItem item = contentItemFactory.fromText(text);

        AnalysisResultSummary result = analysisOrchestrator.submit(item);
        AnalysisResultResponse response = toResponse(result, null);

        historyService.createHistoryItem(new CreateHistoryItemRequest(
            InputType.TEXT,
            null,
            response.verdict(),
            response.confidence()
        ));

        logElapsed("text", startedAt);
        return response;
    }

    public AnalysisResultResponse analyzeMedia(MultipartFile file) {
        long startedAt = System.nanoTime();

        ParsedMedia media = mediaParser.parse(file);
        ContentItem item = contentItemFactory.fromMedia(media);

        AnalysisResultSummary result = analysisOrchestrator.submit(item);
        ImageQuality quality = media.mediaType() == MediaType.IMAGE ? tryAnalyzeQuality(file) : null;
        AnalysisResultResponse response = toResponse(result, quality);

        historyService.createHistoryItem(new CreateHistoryItemRequest(
            InputType.MEDIA,
            media.mediaType(),
            response.verdict(),
            response.confidence()
        ));

        logElapsed(media.mediaType().name().toLowerCase(), startedAt);
        return response;
    }

    private ImageQuality tryAnalyzeQuality(MultipartFile file) {
        try {
            return requestQuality(file);
        } catch (Exception e) {
            log.warn("Image quality analysis failed, responding without it: {}", e.getMessage());
            return null;
        }
    }

    private ImageQuality requestQuality(MultipartFile file) {
        try {
            return imageQualityClient.analyzeImageQuality(file.getBytes());
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot read uploaded file", e);
        }
    }

    public QualityResponse analyzeQuality(MultipartFile file) {
        long startedAt = System.nanoTime();

        ParsedMedia media = mediaParser.parse(file);
        if (media.mediaType() != MediaType.IMAGE) {
            throw new ResponseStatusException(
                HttpStatus.UNSUPPORTED_MEDIA_TYPE,
                "Quality analysis supports images only"
            );
        }

        QualityResponse response = QualityResponse.from(requestQuality(file));

        logElapsed("quality", startedAt);
        return response;
    }

    private AnalysisResultResponse toResponse(AnalysisResultSummary result, ImageQuality quality) {
        FinalScore score = result.score();
        return new AnalysisResultResponse(
            score.verdict(),
            score.confidence(),
            result.evidence().stream()
                .map(EvidenceResponse::from)
                .toList(),
            quality == null ? null : QualityResponse.from(quality)
        );
    }

    private void logElapsed(String analysisType, long startedAt) {
        long elapsedMs = (System.nanoTime() - startedAt) / 1_000_000;
        log.info("{} analysis completed in {} ms", analysisType, elapsedMs);
    }
}
