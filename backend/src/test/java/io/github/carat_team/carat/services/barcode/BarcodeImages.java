package io.github.carat_team.carat.services.barcode;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.MultiFormatWriter;
import com.google.zxing.WriterException;
import com.google.zxing.common.BitMatrix;

import java.awt.image.BufferedImage;

/**
 * Renders barcodes into images for tests.
 */
public final class BarcodeImages {

    private BarcodeImages() {
    }

    public static BufferedImage render(BarcodeFormat format, String text, int width, int height) throws WriterException {
        BitMatrix matrix = new MultiFormatWriter().encode(text, format, width, height);
        BufferedImage image = new BufferedImage(matrix.getWidth(), matrix.getHeight(), BufferedImage.TYPE_INT_RGB);
        for (int x = 0; x < matrix.getWidth(); x++) {
            for (int y = 0; y < matrix.getHeight(); y++) {
                image.setRGB(x, y, matrix.get(x, y) ? 0x000000 : 0xFFFFFF);
            }
        }
        return image;
    }
}
