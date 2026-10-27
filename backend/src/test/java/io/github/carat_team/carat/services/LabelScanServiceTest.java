package io.github.carat_team.carat.services;

import com.google.zxing.BarcodeFormat;
import io.github.carat_team.carat.dto.BarcodeResponse;
import io.github.carat_team.carat.dto.LabelScanResponse;
import io.github.carat_team.carat.dto.TextBlockResponse;
import io.github.carat_team.carat.inference.OcrGrpcClient;
import io.github.carat_team.carat.services.barcode.BarcodeReader;
import io.github.carat_team.carat.services.barcode.BarcodeValidator;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.server.ResponseStatusException;

import javax.imageio.ImageIO;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.List;

import static io.github.carat_team.carat.services.barcode.BarcodeImages.render;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verifyNoInteractions;

class LabelScanServiceTest {

    private final OcrGrpcClient ocrClient = mock(OcrGrpcClient.class);
    private final LabelScanService service =
        new LabelScanService(new BarcodeReader(), new BarcodeValidator(), ocrClient);

    @Test
    void returnsValidatedBarcodesAndOcrText() throws Exception {
        List<TextBlockResponse> texts = List.of(new TextBlockResponse("MADE IN FRANCE", 0.97));
        given(ocrClient.readText(any())).willReturn(texts);

        LabelScanResponse response = service.scan(png(BarcodeFormat.EAN_13, "3614272049529"));

        assertEquals(List.of(new BarcodeResponse("3614272049529", "EAN_13", true, null)), response.barcodes());
        assertEquals(texts, response.texts());
    }

    @Test
    void rejectsFileThatIsNotAnImage() {
        MockMultipartFile file = new MockMultipartFile("file", "card.txt", "text/plain", "not an image".getBytes());

        ResponseStatusException ex = assertThrows(ResponseStatusException.class, () -> service.scan(file));

        assertEquals(HttpStatus.BAD_REQUEST, ex.getStatusCode());
        verifyNoInteractions(ocrClient);
    }

    @Test
    void rejectsEmptyFile() {
        MockMultipartFile file = new MockMultipartFile("file", "empty.png", "image/png", new byte[0]);

        ResponseStatusException ex = assertThrows(ResponseStatusException.class, () -> service.scan(file));

        assertEquals(HttpStatus.BAD_REQUEST, ex.getStatusCode());
    }

    private static MockMultipartFile png(BarcodeFormat format, String text) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        if (!ImageIO.write(render(format, text, 400, 150), "png", out)) {
            throw new IOException("PNG writer is not available");
        }
        return new MockMultipartFile("file", "label.png", "image/png", out.toByteArray());
    }
}
