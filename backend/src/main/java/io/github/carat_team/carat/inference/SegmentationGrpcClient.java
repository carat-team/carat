package io.github.carat_team.carat.inference;

import com.google.protobuf.ByteString;
import io.github.carat_team.carat.config.InferenceGrpcProperties;
import io.github.carat_team.carat.grpc.SegmentationGrpc;
import io.github.carat_team.carat.grpc.SegmentationReply;
import io.github.carat_team.carat.grpc.SegmentationRequest;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

@Service
public class SegmentationGrpcClient {
    private static final Logger log = LoggerFactory.getLogger(SegmentationGrpcClient.class);

    private final SegmentationGrpc.SegmentationBlockingStub baseStub;
    private final InferenceGrpcProperties properties;

    public SegmentationGrpcClient(SegmentationGrpc.SegmentationBlockingStub baseStub, InferenceGrpcProperties properties) {
        this.baseStub = baseStub;
        this.properties = properties;
    }

    /** Returns the grayscale object mask (255 = object) of the same size as the image. */
    public BufferedImage segmentProduct(byte[] imageContent) {
        SegmentationRequest request = SegmentationRequest.newBuilder()
            .setImageData(ByteString.copyFrom(imageContent))
            .build();

        long startedAt = System.nanoTime();
        log.info("Calling ML service: SegmentProduct [bytes={}]", imageContent.length);

        SegmentationReply reply;
        try {
            reply = baseStub
                .withDeadlineAfter(properties.getTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .segmentProduct(request);
        } catch (StatusRuntimeException ex) {
            log.error("ML service call failed: SegmentProduct, status={}", ex.getStatus().getCode(), ex);
            throw mapGrpcException(ex);
        }
        log.info("ML service call completed: SegmentProduct in {} ms", (System.nanoTime() - startedAt) / 1_000_000);

        try {
            BufferedImage mask = ImageIO.read(new ByteArrayInputStream(reply.getMaskPng().toByteArray()));
            if (mask == null) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "ML service returned an unreadable mask");
            }
            return mask;
        } catch (IOException ex) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "ML service returned an unreadable mask", ex);
        }
    }

    private ResponseStatusException mapGrpcException(StatusRuntimeException ex) {
        HttpStatus status = switch (ex.getStatus().getCode()) {
            case DEADLINE_EXCEEDED -> HttpStatus.GATEWAY_TIMEOUT;
            case UNAVAILABLE -> HttpStatus.SERVICE_UNAVAILABLE;
            case INVALID_ARGUMENT -> HttpStatus.BAD_REQUEST;
            default -> HttpStatus.BAD_GATEWAY;
        };
        return new ResponseStatusException(status, "ML service call failed during SegmentProduct", ex);
    }
}
