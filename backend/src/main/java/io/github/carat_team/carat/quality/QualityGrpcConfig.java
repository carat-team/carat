package io.github.carat_team.carat.quality;

import io.github.carat_team.carat.grpc.ImageQualityGrpc;
import io.grpc.ManagedChannel;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class QualityGrpcConfig {

    @Bean
    public ImageQualityGrpc.ImageQualityBlockingStub mlImageQualityBlockingStub(ManagedChannel mlManagedChannel) {
        return ImageQualityGrpc.newBlockingStub(mlManagedChannel);
    }
}
