package io.github.carat_team.carat.services.barcode;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import org.junit.jupiter.api.Test;

import java.awt.image.BufferedImage;
import java.util.List;

import static io.github.carat_team.carat.services.barcode.BarcodeImages.render;
import static org.junit.jupiter.api.Assertions.assertEquals;

class BarcodeReaderTest {

    private final BarcodeReader reader = new BarcodeReader();

    @Test
    void readsEan13() throws WriterException {
        BufferedImage image = render(BarcodeFormat.EAN_13, "3614272049529", 400, 150);

        assertEquals(List.of(new DecodedBarcode("3614272049529", BarcodeFormat.EAN_13)), reader.read(image));
    }

    @Test
    void readsDataMatrix() throws WriterException {
        BufferedImage image = render(BarcodeFormat.DATA_MATRIX, "0104600439931256215Q8H6t", 200, 200);

        assertEquals(
            List.of(new DecodedBarcode("0104600439931256215Q8H6t", BarcodeFormat.DATA_MATRIX)),
            reader.read(image)
        );
    }

    @Test
    void returnsEmptyListWhenNoCode() {
        BufferedImage image = new BufferedImage(300, 200, BufferedImage.TYPE_INT_RGB);

        assertEquals(List.of(), reader.read(image));
    }
}
