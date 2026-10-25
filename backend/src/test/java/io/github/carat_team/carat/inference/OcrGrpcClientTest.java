package io.github.carat_team.carat.inference;

import io.github.carat_team.carat.config.InferenceGrpcProperties;
import io.github.carat_team.carat.dto.TextBlockResponse;
import io.github.carat_team.carat.grpc.OcrGrpc;
import io.github.carat_team.carat.grpc.OcrReply;
import io.github.carat_team.carat.grpc.OcrRequest;
import io.github.carat_team.carat.grpc.TextBlock;
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

import java.io.IOException;
import java.time.Duration;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class OcrGrpcClientTest {

    private Server server;
    private ManagedChannel channel;

    @AfterEach
    void tearDown() {
        channel.shutdownNow();
        server.shutdownNow();
    }

    @Test
    void mapsTextBlocks() throws IOException {
        OcrGrpcClient client = startClient(new OcrGrpc.OcrImplBase() {
            @Override
            public void readText(OcrRequest request, StreamObserver<OcrReply> responseObserver) {
                responseObserver.onNext(OcrReply.newBuilder()
                    .addBlocks(TextBlock.newBuilder().setText("CHANEL").setConfidence(0.5f))
                    .build());
                responseObserver.onCompleted();
            }
        });

        assertEquals(List.of(new TextBlockResponse("CHANEL", 0.5)), client.readText(new byte[] {1, 2, 3}));
    }

    @Test
    void mapsInvalidArgumentToBadRequest() throws IOException {
        OcrGrpcClient client = startClient(new OcrGrpc.OcrImplBase() {
            @Override
            public void readText(OcrRequest request, StreamObserver<OcrReply> responseObserver) {
                responseObserver.onError(Status.INVALID_ARGUMENT.asRuntimeException());
            }
        });

        ResponseStatusException ex = assertThrows(
            ResponseStatusException.class,
            () -> client.readText(new byte[] {1, 2, 3})
        );
        assertEquals(HttpStatus.BAD_REQUEST, ex.getStatusCode());
    }

    private OcrGrpcClient startClient(OcrGrpc.OcrImplBase service) throws IOException {
        String serverName = InProcessServerBuilder.generateName();
        server = InProcessServerBuilder.forName(serverName).directExecutor().addService(service).build().start();
        channel = InProcessChannelBuilder.forName(serverName).directExecutor().build();

        InferenceGrpcProperties properties = new InferenceGrpcProperties();
        properties.setTimeout(Duration.ofSeconds(5));
        return new OcrGrpcClient(OcrGrpc.newBlockingStub(channel), properties);
    }
}
