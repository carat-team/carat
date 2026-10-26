package io.github.carat_team.carat.inference;

import com.google.protobuf.ByteString;
import io.github.carat_team.carat.config.InferenceGrpcProperties;
import io.github.carat_team.carat.grpc.SegmentationGrpc;
import io.github.carat_team.carat.grpc.SegmentationReply;
import io.github.carat_team.carat.grpc.SegmentationRequest;
import io.grpc.ManagedChannel;
import io.grpc.Server;
import io.grpc.Status;
import io.grpc.inprocess.InProcessChannelBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.stub.StreamObserver;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.time.Duration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class SegmentationGrpcClientTest {

    private Server server;
    private ManagedChannel channel;

    @AfterEach
    void tearDown() {
        channel.shutdownNow();
        server.shutdownNow();
    }

    @Test
    void decodesMask() throws IOException {
        BufferedImage mask = new BufferedImage(4, 3, BufferedImage.TYPE_BYTE_GRAY);
        mask.getRaster().setSample(1, 1, 0, 255);
        ByteArrayOutputStream png = new ByteArrayOutputStream();
        ImageIO.write(mask, "png", png);

        SegmentationGrpcClient client = startClient(new SegmentationGrpc.SegmentationImplBase() {
            @Override
            public void segmentProduct(SegmentationRequest request, StreamObserver<SegmentationReply> responseObserver) {
                responseObserver.onNext(SegmentationReply.newBuilder()
                    .setMaskPng(ByteString.copyFrom(png.toByteArray()))
                    .setWidth(4)
                    .setHeight(3)
                    .build());
                responseObserver.onCompleted();
            }
        });

        BufferedImage result = client.segmentProduct(new byte[] {1, 2, 3});
        assertEquals(4, result.getWidth());
        assertEquals(255, result.getRaster().getSample(1, 1, 0));
        assertEquals(0, result.getRaster().getSample(0, 0, 0));
    }

    @Test
    void mapsInvalidArgumentToBadRequest() throws IOException {
        SegmentationGrpcClient client = startClient(new SegmentationGrpc.SegmentationImplBase() {
            @Override
            public void segmentProduct(SegmentationRequest request, StreamObserver<SegmentationReply> responseObserver) {
                responseObserver.onError(Status.INVALID_ARGUMENT.asRuntimeException());
            }
        });

        ResponseStatusException ex = assertThrows(
            ResponseStatusException.class,
            () -> client.segmentProduct(new byte[] {1, 2, 3})
        );
        assertEquals(HttpStatus.BAD_REQUEST, ex.getStatusCode());
    }

    @Test
    void mapsUnavailableToServiceUnavailable() throws IOException {
        SegmentationGrpcClient client = startClient(new SegmentationGrpc.SegmentationImplBase() {
            @Override
            public void segmentProduct(SegmentationRequest request, StreamObserver<SegmentationReply> responseObserver) {
                responseObserver.onError(Status.UNAVAILABLE.asRuntimeException());
            }
        });

        ResponseStatusException ex = assertThrows(
            ResponseStatusException.class,
            () -> client.segmentProduct(new byte[] {1, 2, 3})
        );
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, ex.getStatusCode());
    }

    private SegmentationGrpcClient startClient(SegmentationGrpc.SegmentationImplBase service) throws IOException {
        String serverName = InProcessServerBuilder.generateName();
        server = InProcessServerBuilder.forName(serverName).directExecutor().addService(service).build().start();
        channel = InProcessChannelBuilder.forName(serverName).directExecutor().build();

        InferenceGrpcProperties properties = new InferenceGrpcProperties();
        properties.setTimeout(Duration.ofSeconds(5));
        return new SegmentationGrpcClient(SegmentationGrpc.newBlockingStub(channel), properties);
    }
}
