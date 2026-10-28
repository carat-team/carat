package io.github.carat_team.carat.quality;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;

@Service
public class QualityService {
    private static final Logger log = LoggerFactory.getLogger(QualityService.class);

    private final QualityGrpcClient qualityClient;

    public QualityService(QualityGrpcClient qualityClient) {
        this.qualityClient = qualityClient;
    }

    public QualityResponse analyze(MultipartFile file) {
        long startedAt = System.nanoTime();

        if (file.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Uploaded file is empty");
        }

        byte[] content;
        try {
            content = file.getBytes();
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot read uploaded file", e);
        }

        QualityResponse response = qualityClient.analyze(content);

        long elapsedMs = (System.nanoTime() - startedAt) / 1_000_000;
        log.info("quality analysis completed in {} ms", elapsedMs);
        return response;
    }
}
