package io.github.carat_team.carat.services.barcode;

import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.MultiFormatReader;
import com.google.zxing.NotFoundException;
import com.google.zxing.RGBLuminanceSource;
import com.google.zxing.Result;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.multi.GenericMultipleBarcodeReader;
import org.springframework.stereotype.Component;

import java.awt.image.BufferedImage;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

@Component
public class BarcodeReader {

    private static final Map<DecodeHintType, Object> HINTS = Map.of(DecodeHintType.TRY_HARDER, Boolean.TRUE);

    public List<DecodedBarcode> read(BufferedImage image) {
        int width = image.getWidth();
        int height = image.getHeight();
        int[] pixels = image.getRGB(0, 0, width, height, null, 0, width);
        BinaryBitmap bitmap = new BinaryBitmap(new HybridBinarizer(new RGBLuminanceSource(width, height, pixels)));

        try {
            Result[] results = new GenericMultipleBarcodeReader(new MultiFormatReader()).decodeMultiple(bitmap, HINTS);
            return Arrays.stream(results)
                .map(result -> new DecodedBarcode(result.getText(), result.getBarcodeFormat()))
                .distinct()
                .toList();
        } catch (NotFoundException e) {
            return List.of();
        }
    }
}
