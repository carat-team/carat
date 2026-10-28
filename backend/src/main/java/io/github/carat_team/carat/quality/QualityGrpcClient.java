package io.github.carat_team.carat.quality;

import com.google.protobuf.ByteString;
import io.github.carat_team.carat.config.InferenceGrpcProperties;
import io.github.carat_team.carat.grpc.ImageQualityGrpc;
import io.github.carat_team.carat.grpc.ImageQualityReply;
import io.github.carat_team.carat.grpc.ImageQualityRequest;
import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.Locale;
import java.util.concurrent.TimeUnit;

@Service
public class QualityGrpcClient {
    private static final Logger log = LoggerFactory.getLogger(QualityGrpcClient.class);

    private final ImageQualityGrpc.ImageQualityBlockingStub baseStub;
    private final InferenceGrpcProperties properties;

    public QualityGrpcClient(
        ImageQualityGrpc.ImageQualityBlockingStub baseStub,
        InferenceGrpcProperties properties
    ) {
        this.baseStub = baseStub;
        this.properties = properties;
    }

    public QualityResponse analyze(byte[] imageContent) {
        ImageQualityRequest request = ImageQualityRequest.newBuilder()
            .setImageData(ByteString.copyFrom(imageContent))
            .build();

        long startedAt = System.nanoTime();
        log.info("Calling ML service: ImageQuality.Analyze [bytes={}]", imageContent.length);

        try {
            ImageQualityReply reply = baseStub
                .withDeadlineAfter(properties.getTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .analyze(request);

            long elapsedMs = (System.nanoTime() - startedAt) / 1_000_000;
            log.info("ML service call completed: ImageQuality.Analyze in {} ms", elapsedMs);
            return mapReply(reply);
        } catch (StatusRuntimeException ex) {
            long elapsedMs = (System.nanoTime() - startedAt) / 1_000_000;
            log.error(
                "ML service call failed: ImageQuality.Analyze in {} ms, status={}",
                elapsedMs,
                ex.getStatus().getCode(),
                ex
            );
            throw mapGrpcException(ex);
        }
    }

    private QualityResponse mapReply(ImageQualityReply reply) {
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

        return new QualityResponse(
            reply.getSharpness(),
            reply.getOverexposure(),
            reply.getUnderexposure(),
            reply.getResolution(),
            reply.getOverall(),
            mapVerdict(reply.getVerdict()),
            reply.getWeakest(),
            reply.getWidth(),
            reply.getHeight()
        );
    }

    private QualityVerdict mapVerdict(String rawVerdict) {
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

    private ResponseStatusException mapGrpcException(StatusRuntimeException ex) {
        Status.Code code = ex.getStatus().getCode();

        if (code == Status.Code.DEADLINE_EXCEEDED) {
            return new ResponseStatusException(
                HttpStatus.GATEWAY_TIMEOUT,
                "ML service timeout during quality analysis",
                ex
            );
        }

        if (code == Status.Code.UNAVAILABLE) {
            return new ResponseStatusException(
                HttpStatus.SERVICE_UNAVAILABLE,
                "ML service is unavailable during quality analysis",
                ex
            );
        }

        if (code == Status.Code.INVALID_ARGUMENT) {
            return new ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                "Uploaded file is not a valid image",
                ex
            );
        }

        return new ResponseStatusException(
            HttpStatus.BAD_GATEWAY,
            "ML service call failed during quality analysis",
            ex
        );
    }
}
