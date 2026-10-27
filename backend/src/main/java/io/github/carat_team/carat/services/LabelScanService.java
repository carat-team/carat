package io.github.carat_team.carat.services;

import io.github.carat_team.carat.dto.BarcodeResponse;
import io.github.carat_team.carat.dto.LabelScanResponse;
import io.github.carat_team.carat.dto.TextBlockResponse;
import io.github.carat_team.carat.inference.OcrGrpcClient;
import io.github.carat_team.carat.services.barcode.BarcodeReader;
import io.github.carat_team.carat.services.barcode.BarcodeValidator;
import io.github.carat_team.carat.services.barcode.DecodedBarcode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.List;
import java.util.Optional;

/**
 * Reads barcodes (static, here) and text (OCR model in inference) from a product label photo.
 */
@Service
public class LabelScanService {
    private static final Logger log = LoggerFactory.getLogger(LabelScanService.class);

    private final BarcodeReader barcodeReader;
    private final BarcodeValidator barcodeValidator;
    private final OcrGrpcClient ocrClient;

    public LabelScanService(BarcodeReader barcodeReader, BarcodeValidator barcodeValidator, OcrGrpcClient ocrClient) {
        this.barcodeReader = barcodeReader;
        this.barcodeValidator = barcodeValidator;
        this.ocrClient = ocrClient;
    }

    public LabelScanResponse scan(MultipartFile file) {
        byte[] content = readContent(file);
        BufferedImage image = decodeImage(content);

        List<BarcodeResponse> barcodes = barcodeReader.read(image).stream()
            .map(this::toResponse)
            .toList();
        List<TextBlockResponse> texts = ocrClient.readText(content);

        // Codes and texts are product data, so only their counts are logged
        log.info("Label scan completed: barcodes={}, textBlocks={}", barcodes.size(), texts.size());
        return new LabelScanResponse(barcodes, texts);
    }

    private BarcodeResponse toResponse(DecodedBarcode barcode) {
        Optional<String> error = barcodeValidator.validate(barcode.text(), barcode.format());
        return new BarcodeResponse(barcode.text(), barcode.format().name(), error.isEmpty(), error.orElse(null));
    }

    private static byte[] readContent(MultipartFile file) {
        try {
            byte[] content = file.getBytes();
            if (content.length == 0) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is empty");
            }
            return content;
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot read uploaded file", e);
        }
    }

    private static BufferedImage decodeImage(byte[] content) {
        try {
            BufferedImage image = ImageIO.read(new ByteArrayInputStream(content));
            if (image == null) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is not a supported image");
            }
            return image;
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is not a supported image", e);
        }
    }
}
