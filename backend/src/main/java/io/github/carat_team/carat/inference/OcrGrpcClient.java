package io.github.carat_team.carat.inference;

import com.google.protobuf.ByteString;
import io.github.carat_team.carat.config.InferenceGrpcProperties;
import io.github.carat_team.carat.dto.TextBlockResponse;
import io.github.carat_team.carat.grpc.OcrGrpc;
import io.github.carat_team.carat.grpc.OcrReply;
import io.github.carat_team.carat.grpc.OcrRequest;
import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
public class OcrGrpcClient {
    private static final Logger log = LoggerFactory.getLogger(OcrGrpcClient.class);

    private final OcrGrpc.OcrBlockingStub baseStub;
    private final InferenceGrpcProperties properties;

    public OcrGrpcClient(OcrGrpc.OcrBlockingStub baseStub, InferenceGrpcProperties properties) {
        this.baseStub = baseStub;
        this.properties = properties;
    }

    public List<TextBlockResponse> readText(byte[] imageContent) {
        OcrRequest request = OcrRequest.newBuilder()
            .setImageData(ByteString.copyFrom(imageContent))
            .build();

        long startedAt = System.nanoTime();
        log.info("Calling ML service: ReadText [bytes={}]", imageContent.length);

        try {
            OcrReply reply = baseStub
                .withDeadlineAfter(properties.getTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .readText(request);
            log.info("ML service call completed: ReadText in {} ms", (System.nanoTime() - startedAt) / 1_000_000);

            return reply.getBlocksList().stream()
                .map(block -> new TextBlockResponse(block.getText(), block.getConfidence()))
                .toList();
        } catch (StatusRuntimeException ex) {
            log.error("ML service call failed: ReadText, status={}", ex.getStatus().getCode(), ex);
            throw mapGrpcException(ex);
        }
    }

    private ResponseStatusException mapGrpcException(StatusRuntimeException ex) {
        HttpStatus status = switch (ex.getStatus().getCode()) {
            case DEADLINE_EXCEEDED -> HttpStatus.GATEWAY_TIMEOUT;
            case UNAVAILABLE -> HttpStatus.SERVICE_UNAVAILABLE;
            case INVALID_ARGUMENT -> HttpStatus.BAD_REQUEST;
            default -> HttpStatus.BAD_GATEWAY;
        };
        return new ResponseStatusException(status, "ML service call failed during ReadText", ex);
    }
}
