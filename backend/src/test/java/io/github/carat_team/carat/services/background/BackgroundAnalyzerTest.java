package io.github.carat_team.carat.services.background;

import io.github.carat_team.carat.dto.BackgroundCheckResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.BackgroundVerdict;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ForeignObjectSource;
import org.junit.jupiter.api.Test;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class BackgroundAnalyzerTest {
    private static final int SIZE = 200;

    private final BackgroundAnalyzer analyzer = new BackgroundAnalyzer();

    @Test
    void plainBackgroundIsClean() {
        BufferedImage image = filled(new Color(240, 240, 240));
        drawRect(image, Color.DARK_GRAY, 70, 40, 60, 120);
        BufferedImage mask = mask(new int[] {70, 40, 60, 120});

        BackgroundCheckResponse result = analyzer.analyze(image, mask, 2.0, 400, 400);

        assertEquals(BackgroundVerdict.CLEAN, result.verdict());
        assertTrue(result.ok());
        assertTrue(result.foreignObjects().isEmpty());
        assertEquals(140, result.mainObject().x());
        assertEquals(240, result.mainObject().height());
        assertEquals("#f0f0f0", result.background().color());
    }

    @Test
    void smoothGradientIsClean() {
        BufferedImage image = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_RGB);
        for (int y = 0; y < SIZE; y++) {
            for (int x = 0; x < SIZE; x++) {
                int value = 180 + x * 60 / SIZE;
                image.setRGB(x, y, new Color(value, value - 20, value - 40).getRGB());
            }
        }
        drawRect(image, Color.BLACK, 80, 50, 40, 100);

        BackgroundCheckResponse result = analyzer.analyze(image, mask(new int[] {80, 50, 40, 100}), 1.0, SIZE, SIZE);

        assertEquals(BackgroundVerdict.CLEAN, result.verdict());
    }

    @Test
    void texturedBackgroundIsNoisy() {
        BufferedImage image = filled(Color.WHITE);
        Random random = new Random(42);
        for (int y = 0; y < SIZE; y++) {
            for (int x = 0; x < SIZE; x++) {
                int value = 120 + random.nextInt(100);
                image.setRGB(x, y, new Color(value, value, value).getRGB());
            }
        }
        drawRect(image, Color.BLACK, 80, 50, 40, 100);

        BackgroundCheckResponse result = analyzer.analyze(image, mask(new int[] {80, 50, 40, 100}), 1.0, SIZE, SIZE);

        assertEquals(BackgroundVerdict.NOISY, result.verdict());
        assertFalse(result.ok());
    }

    @Test
    void separateSmallObjectInMaskIsForeign() {
        BufferedImage image = filled(Color.WHITE);
        drawRect(image, Color.BLACK, 40, 40, 60, 120);
        drawRect(image, Color.RED, 150, 150, 20, 20);

        BackgroundCheckResponse result = analyzer.analyze(
            image, mask(new int[] {40, 40, 60, 120}, new int[] {150, 150, 20, 20}), 1.0, SIZE, SIZE);

        assertEquals(BackgroundVerdict.OBJECTS, result.verdict());
        assertEquals(1, result.foreignObjects().size());
        assertEquals(ForeignObjectSource.MASK, result.foreignObjects().getFirst().source());
        assertEquals(150, result.foreignObjects().getFirst().box().x());
    }

    @Test
    void bottleWithItsBoxIsOneProduct() {
        BufferedImage image = filled(Color.WHITE);
        drawRect(image, Color.BLACK, 30, 40, 70, 120);
        drawRect(image, Color.GRAY, 120, 80, 30, 80);

        BackgroundCheckResponse result = analyzer.analyze(
            image, mask(new int[] {30, 40, 70, 120}, new int[] {120, 80, 30, 80}), 1.0, SIZE, SIZE);

        assertEquals(BackgroundVerdict.CLEAN, result.verdict());
        assertEquals(30, result.mainObject().x());
        assertEquals(120, result.mainObject().width());
    }

    @Test
    void blobMissedByMaskIsForeign() {
        BufferedImage image = filled(Color.WHITE);
        drawRect(image, Color.BLACK, 30, 40, 50, 120);
        drawRect(image, new Color(200, 30, 30), 140, 20, 30, 30);

        BackgroundCheckResponse result = analyzer.analyze(image, mask(new int[] {30, 40, 50, 120}), 1.0, SIZE, SIZE);

        assertEquals(BackgroundVerdict.OBJECTS, result.verdict());
        assertEquals(ForeignObjectSource.BACKGROUND, result.foreignObjects().getFirst().source());
    }

    @Test
    void emptyMaskMeansNoObject() {
        BackgroundCheckResponse result = analyzer.analyze(filled(Color.WHITE), mask(), 1.0, SIZE, SIZE);

        assertEquals(BackgroundVerdict.NO_OBJECT, result.verdict());
        assertNull(result.mainObject());
        assertFalse(result.ok());
    }

    private static BufferedImage filled(Color color) {
        BufferedImage image = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_RGB);
        drawRect(image, color, 0, 0, SIZE, SIZE);
        return image;
    }

    private static void drawRect(BufferedImage image, Color color, int x, int y, int width, int height) {
        Graphics2D graphics = image.createGraphics();
        graphics.setColor(color);
        graphics.fillRect(x, y, width, height);
        graphics.dispose();
    }

    /** Mask with the given {x, y, width, height} rectangles set to 255. */
    private static BufferedImage mask(int[]... rectangles) {
        BufferedImage mask = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_BYTE_GRAY);
        for (int[] r : rectangles) {
            drawRect(mask, Color.WHITE, r[0], r[1], r[2], r[3]);
        }
        return mask;
    }
}
