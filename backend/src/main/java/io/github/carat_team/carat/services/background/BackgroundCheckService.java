package io.github.carat_team.carat.services.background;

import io.github.carat_team.carat.dto.BackgroundCheckResponse;
import io.github.carat_team.carat.inference.SegmentationGrpcClient;
import io.github.carat_team.carat.services.background.BinaryMask.Labeling;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;

/**
 * Background and foreign objects check of a product photo: the object mask comes from the
 * segmentation model in inference, everything else is computed here.
 */
@Service
public class BackgroundCheckService {
    private static final Logger log = LoggerFactory.getLogger(BackgroundCheckService.class);
    /** Analysis runs on a copy with this long side; boxes are scaled back to the uploaded image. */
    static final int WORK_SIZE = 512;

    private final SegmentationGrpcClient segmentationClient;
    private final BackgroundAnalyzer analyzer;

    public BackgroundCheckService(SegmentationGrpcClient segmentationClient, BackgroundAnalyzer analyzer) {
        this.segmentationClient = segmentationClient;
        this.analyzer = analyzer;
    }

    public BackgroundCheckResponse check(MultipartFile file) {
        BufferedImage image = decodeImage(readContent(file));
        BufferedImage small = downscale(image, WORK_SIZE);
        BufferedImage mask = segment(small);

        double scale = (double) image.getWidth() / small.getWidth();
        BackgroundCheckResponse response = analyzer.analyze(small, mask, scale, image.getWidth(), image.getHeight());
        log.info("Background check completed: verdict={}, foreignObjects={}",
            response.verdict(), response.foreignObjects().size());
        return response;
    }

    /** PNG with the product on a transparent background, cropped to the product box. */
    public byte[] cutOut(MultipartFile file) {
        BufferedImage image = decodeImage(readContent(file));
        BufferedImage mask = segment(image);
        int width = image.getWidth();
        int height = image.getHeight();

        Labeling labeling = BackgroundAnalyzer.threshold(mask).label();
        if (labeling.components().isEmpty()) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_CONTENT, "No product found on the image");
        }
        List<Integer> parts = BackgroundAnalyzer.productParts(labeling.components());
        BinaryMask.Blob box = BackgroundAnalyzer.bounding(labeling.components(), parts);
        // Keep the soft edge of the product only; other objects are dropped
        BinaryMask region = BinaryMask.ofLabels(labeling, parts, width, height).dilate(2);

        BufferedImage result = new BufferedImage(box.boxWidth(), box.boxHeight(), BufferedImage.TYPE_INT_ARGB);
        var maskRaster = mask.getRaster();
        for (int y = box.minY(); y <= box.maxY(); y++) {
            for (int x = box.minX(); x <= box.maxX(); x++) {
                int alpha = region.get(x, y) ? maskRaster.getSample(x, y, 0) : 0;
                result.setRGB(x - box.minX(), y - box.minY(), (alpha << 24) | (image.getRGB(x, y) & 0xffffff));
            }
        }
        return encodePng(result);
    }

    private BufferedImage segment(BufferedImage image) {
        BufferedImage mask = segmentationClient.segmentProduct(encodePng(image));
        if (mask.getWidth() != image.getWidth() || mask.getHeight() != image.getHeight()) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "ML service returned a mask of a different size");
        }
        return mask;
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

    /** Decodes the image to RGB; transparent areas become white. */
    static BufferedImage decodeImage(byte[] content) {
        BufferedImage decoded;
        try {
            decoded = ImageIO.read(new ByteArrayInputStream(content));
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "File is not a supported image", e);
        }
        if (decoded == null) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "File is not a supported image");
        }
        BufferedImage rgb = new BufferedImage(decoded.getWidth(), decoded.getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = rgb.createGraphics();
        graphics.setColor(Color.WHITE);
        graphics.fillRect(0, 0, rgb.getWidth(), rgb.getHeight());
        graphics.drawImage(decoded, 0, 0, null);
        graphics.dispose();
        return rgb;
    }

    /** Downscales so the long side is at most {@code maxSide}, halving step by step to avoid aliasing. */
    static BufferedImage downscale(BufferedImage image, int maxSide) {
        double factor = (double) maxSide / Math.max(image.getWidth(), image.getHeight());
        if (factor >= 1) {
            return image;
        }
        int targetWidth = Math.max(1, (int) Math.round(image.getWidth() * factor));
        int targetHeight = Math.max(1, (int) Math.round(image.getHeight() * factor));

        BufferedImage current = image;
        while (current.getWidth() / 2 >= targetWidth && current.getHeight() / 2 >= targetHeight) {
            current = resize(current, current.getWidth() / 2, current.getHeight() / 2);
        }
        return current.getWidth() == targetWidth && current.getHeight() == targetHeight
            ? current
            : resize(current, targetWidth, targetHeight);
    }

    private static BufferedImage resize(BufferedImage image, int width, int height) {
        BufferedImage result = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = result.createGraphics();
        graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        graphics.drawImage(image, 0, 0, width, height, null);
        graphics.dispose();
        return result;
    }

    private static byte[] encodePng(BufferedImage image) {
        try {
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            ImageIO.write(image, "png", buffer);
            return buffer.toByteArray();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
