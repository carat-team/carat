package io.github.carat_team.carat.inference;

import com.google.protobuf.ByteString;
import io.github.duckysmacky.cogniflex.analysis.dynamic.inference.InferenceClient;
import io.github.duckysmacky.cogniflex.analysis.AnalysisVerdict;
import io.github.duckysmacky.cogniflex.analysis.ContentType;
import io.github.duckysmacky.cogniflex.analysis.dynamic.DynamicAnalysisResult;
import io.github.carat_team.carat.config.InferenceGrpcProperties;
import io.github.duckysmacky.cogniflex.exceptions.ServiceUnavailableException;
import io.github.carat_team.carat.grpc.AnalyzeReply;
import io.github.carat_team.carat.grpc.AnalyzerGrpc;
import io.github.carat_team.carat.grpc.PhotoRequest;
import io.github.carat_team.carat.grpc.QualityReply;
import io.github.carat_team.carat.grpc.TextRequest;
import io.github.carat_team.carat.grpc.VideoRequest;
import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

@Service
public class InferenceGrpcClient implements InferenceClient, ImageQualityClient {
    private static final Logger log = LoggerFactory.getLogger(InferenceGrpcClient.class);

    private final AnalyzerGrpc.AnalyzerBlockingStub baseStub;
    private final InferenceGrpcProperties properties;

    public InferenceGrpcClient(
        AnalyzerGrpc.AnalyzerBlockingStub baseStub,
        InferenceGrpcProperties properties
    ) {
        this.baseStub = baseStub;
        this.properties = properties;
    }

    @Override
    public DynamicAnalysisResult analyzeText(String normalizedText) {
        TextRequest request = TextRequest.newBuilder()
            .setText(normalizedText)
            .build();

        AnalyzeReply reply = execute(
            "AnalyzeText",
            "textLength=" + normalizedText.length(),
            () -> {
                try {
                    return stubWithTimeout().analyzeText(request);
                } catch (StatusRuntimeException e) {
                    if (e.getStatus().getCode() == Status.Code.DEADLINE_EXCEEDED) {
                        throw new ServiceUnavailableException("ML service hit a timeout during AnalyzeText request");
                    }

                    throw e;
                }
            }
        );

        return mapReply(ContentType.TEXT, reply);
    }

    @Override
    public DynamicAnalysisResult analyzeImage(byte[] imageContent) {
        PhotoRequest request = PhotoRequest.newBuilder()
            .setImageData(ByteString.copyFrom(imageContent))
            .build();

        AnalyzeReply reply = execute(
            "AnalyzePhoto",
            "bytes=" + imageContent.length,
            () -> {
                try {
                    return stubWithTimeout().analyzePhoto(request);
                } catch (StatusRuntimeException e) {
                    if (e.getStatus().getCode() == Status.Code.DEADLINE_EXCEEDED) {
                        throw new ServiceUnavailableException("ML service hit a timeout during AnalyzePhoto request");
                    }

                    throw e;
                }
            }
        );

        return mapReply(ContentType.IMAGE, reply);
    }

    @Override
    public DynamicAnalysisResult analyzeVideo(byte[] videoContent) {
        VideoRequest request = VideoRequest.newBuilder()
            .setVideoData(ByteString.copyFrom(videoContent))
            .build();

        AnalyzeReply reply = execute(
            "AnalyzeVideo",
            "bytes=" + videoContent.length,
            () -> {
                try {
                    return stubWithTimeout().analyzeVideo(request);
                } catch (StatusRuntimeException e) {
                    if (e.getStatus().getCode() == Status.Code.DEADLINE_EXCEEDED) {
                        throw new ServiceUnavailableException("ML service hit a timeout during AnalyzeVideo request");
                    }

                    throw e;
                }
            }
        );

        return mapReply(ContentType.VIDEO, reply);
    }

    @Override
    public ImageQuality analyzeImageQuality(byte[] imageContent) {
        PhotoRequest request = PhotoRequest.newBuilder()
            .setImageData(ByteString.copyFrom(imageContent))
            .build();

        QualityReply reply = execute(
            "AnalyzeQuality",
            "bytes=" + imageContent.length,
            () -> {
                try {
                    return stubWithTimeout().analyzeQuality(request);
                } catch (StatusRuntimeException e) {
                    if (e.getStatus().getCode() == Status.Code.DEADLINE_EXCEEDED) {
                        throw new ServiceUnavailableException("ML service hit a timeout during AnalyzeQuality request");
                    }

                    throw e;
                }
            }
        );

        return mapQuality(reply);
    }

    private AnalyzerGrpc.AnalyzerBlockingStub stubWithTimeout() {
        return baseStub.withDeadlineAfter(properties.getTimeout().toMillis(), TimeUnit.MILLISECONDS);
    }

    private <T> T execute(String operation, String details, Supplier<T> grpcCall) {
        long startedAt = System.nanoTime();
        log.info("Calling ML service: {} [{}]", operation, details);

        try {
            T reply = grpcCall.get();
            long elapsedMs = (System.nanoTime() - startedAt) / 1_000_000;
            log.info("ML service call completed: {} in {} ms", operation, elapsedMs);
            return reply;
        } catch (StatusRuntimeException ex) {
            long elapsedMs = (System.nanoTime() - startedAt) / 1_000_000;
            log.error(
                "ML service call failed: {} in {} ms, backendHealth={}",
                operation,
                elapsedMs,
                ex.getStatus().getCode(),
                ex
            );
            throw mapGrpcException(operation, ex);
        }
    }

    private DynamicAnalysisResult mapReply(ContentType contentType, AnalyzeReply reply) {
        AnalysisVerdict verdict = mapClass(reply.getClass_());
        double confidence = reply.getConfidence();

        if (confidence < 0.0 || confidence > 1.0) {
            throw new ResponseStatusException(
                HttpStatus.INTERNAL_SERVER_ERROR,
                "ML service returned invalid confidence: " + confidence
            );
        }

        return new DynamicAnalysisResult(contentType, verdict, confidence);
    }

    private AnalysisVerdict mapClass(String rawClass) {
        String normalizedClass = rawClass.trim().toLowerCase(Locale.ROOT);

        return switch (normalizedClass) {
            case "human", "real" -> AnalysisVerdict.HUMAN;
            case "ai", "ai_generated", "generated", "fake" -> AnalysisVerdict.AI;
            default -> throw new ResponseStatusException(
                HttpStatus.BAD_GATEWAY,
                "Unknown class returned by ML service: " + rawClass
            );
        };
    }

    private ImageQuality mapQuality(QualityReply reply) {
        int[] scores = {
            reply.getSharpness(),
            reply.getOverexposure(),
            reply.getUnderexposure(),
            reply.getResolution(),
            reply.getOverall()
        };

        for (int score : scores) {
            if (score < 0 || score > 100) {
                throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "ML service returned invalid quality score: " + score
                );
            }
        }

        return new ImageQuality(
            reply.getSharpness(),
            reply.getOverexposure(),
            reply.getUnderexposure(),
            reply.getResolution(),
            reply.getOverall(),
            mapQualityVerdict(reply.getVerdict()),
            reply.getWeakest(),
            reply.getWidth(),
            reply.getHeight()
        );
    }

    private QualityVerdict mapQualityVerdict(String rawVerdict) {
        String normalizedVerdict = rawVerdict.trim().toLowerCase(Locale.ROOT);

        return switch (normalizedVerdict) {
            case "reject" -> QualityVerdict.REJECT;
            case "review" -> QualityVerdict.REVIEW;
            case "ok" -> QualityVerdict.OK;
            default -> throw new ResponseStatusException(
                HttpStatus.BAD_GATEWAY,
                "Unknown quality verdict returned by ML service: " + rawVerdict
            );
        };
    }

    private ResponseStatusException mapGrpcException(String operation, StatusRuntimeException ex) {
        Status.Code code = ex.getStatus().getCode();

        if (code == Status.Code.DEADLINE_EXCEEDED) {
            return new ResponseStatusException(
                HttpStatus.GATEWAY_TIMEOUT,
                "ML service timeout during " + operation,
                ex
            );
        }

        if (code == Status.Code.UNAVAILABLE) {
            return new ResponseStatusException(
                HttpStatus.SERVICE_UNAVAILABLE,
                "ML service is unavailable during " + operation,
                ex
            );
        }

        if (code == Status.Code.INVALID_ARGUMENT) {
            return new ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                "ML service rejected request during " + operation,
                ex
            );
        }

        return new ResponseStatusException(
            HttpStatus.BAD_GATEWAY,
            "ML service call failed during " + operation,
            ex
        );
    }
}
