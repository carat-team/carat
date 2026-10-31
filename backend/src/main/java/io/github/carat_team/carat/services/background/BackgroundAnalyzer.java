package io.github.carat_team.carat.services.background;

import io.github.carat_team.carat.dto.BackgroundCheckResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.BackgroundStatsResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.BackgroundVerdict;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ForeignObjectResponse;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ForeignObjectSource;
import io.github.carat_team.carat.dto.BackgroundCheckResponse.ObjectBoxResponse;
import io.github.carat_team.carat.services.background.BinaryMask.Blob;
import io.github.carat_team.carat.services.background.BinaryMask.Labeling;

import org.springframework.stereotype.Component;

import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.IntStream;

/**
 * Checks what is around the product on a photo, given the object mask from the segmentation model:
 * is the background plain, uneven, or are there other objects in the frame.
 */
@Component
public class BackgroundAnalyzer {
    /** Mask parts at least this big relative to the largest one are the product too (bottle + its box). */
    static final double PRODUCT_PART_SHARE = 0.1;
    /** Smaller blobs are noise, not objects (share of image area). */
    static final double MIN_OBJECT_SHARE = 0.005;
    /** A pixel this close to the background model counts as "same colour" (CIE76 delta E). */
    static final double NEAR_DELTA_E = 10;
    /** A pixel this far from the background model may belong to a foreign object. */
    static final double FAR_DELTA_E = 25;
    /** Share of "same colour" background pixels needed for a clean background. */
    static final double CLEAN_UNIFORMITY = 0.95;
    /** Share of edge pixels allowed on a clean background. */
    static final double CLEAN_EDGE_DENSITY = 0.02;
    static final int MASK_THRESHOLD = 127;

    /**
     * @param image  photo the mask was computed for (already downscaled for analysis)
     * @param mask   grayscale object mask of the same size, 255 = object
     * @param scale  factor from {@code image} pixels to the uploaded image pixels
     * @param width  uploaded image width, reported as is
     * @param height uploaded image height, reported as is
     */
    public BackgroundCheckResponse analyze(BufferedImage image, BufferedImage mask, double scale, int width, int height) {
        int w = image.getWidth();
        int h = image.getHeight();
        int total = w * h;
        double minArea = MIN_OBJECT_SHARE * total;

        BinaryMask objects = threshold(mask);
        Labeling labeling = objects.label();
        List<Blob> components = labeling.components();
        if (components.isEmpty()) {
            return new BackgroundCheckResponse(BackgroundVerdict.NO_OBJECT, false, width, height, null,
                new BackgroundStatsResponse(null, 0, 0), List.of());
        }

        List<Integer> parts = productParts(components);
        List<ForeignObjectResponse> foreign = new ArrayList<>();
        for (int label = 1; label <= components.size(); label++) {
            Blob component = components.get(label - 1);
            if (!parts.contains(label) && component.area() >= minArea) {
                foreign.add(new ForeignObjectResponse(box(component, total, scale), ForeignObjectSource.MASK));
            }
        }

        // Background = everything outside the objects, with a margin so object edges and shadows do not count
        int margin = Math.max(3, (int) Math.round(0.02 * Math.min(w, h)));
        BinaryMask background = objects.dilate(margin / 2).not();
        if (background.count() < minArea) {
            background = objects.not();
        }

        int[] rgb = image.getRGB(0, 0, w, h, null, 0, w);
        double[][] lab = new double[total][];
        int[] gray = new int[total];
        for (int i = 0; i < total; i++) {
            lab[i] = LabColor.fromRgb(rgb[i]);
            int r = (rgb[i] >> 16) & 0xff;
            int g = (rgb[i] >> 8) & 0xff;
            int b = rgb[i] & 0xff;
            gray[i] = (int) Math.round(0.299 * r + 0.587 * g + 0.114 * b);
        }

        double[][] model = BackgroundModel.fit(lab, background);
        double[] delta = new double[total];
        int near = 0;
        int backgroundCount = 0;
        for (int i = 0; i < total; i++) {
            delta[i] = distance(lab[i], model[i]);
            if (background.pixels()[i]) {
                backgroundCount++;
                if (delta[i] < NEAR_DELTA_E) {
                    near++;
                }
            }
        }
        double uniformity = (double) near / backgroundCount;
        double edgeDensity = (double) CannyEdges.detect(gray, w, h, 50, 150).and(background).count() / backgroundCount;

        // Blobs on the background that clearly differ from it are foreign objects, unless they touch
        // the product: those are shadows, reflections or product parts the mask missed
        BinaryMask nearProduct = BinaryMask.ofLabels(labeling, parts, w, h).dilate(margin);
        boolean[] far = new boolean[total];
        for (int i = 0; i < total; i++) {
            far[i] = delta[i] > FAR_DELTA_E && background.pixels()[i];
        }
        Labeling blobs = new BinaryMask(far, w, h).open(2).label();
        for (int label = 1; label <= blobs.components().size(); label++) {
            Blob blob = blobs.components().get(label - 1);
            if (blob.area() >= minArea && !touches(blobs.labels(), label, nearProduct)) {
                foreign.add(new ForeignObjectResponse(box(blob, total, scale), ForeignObjectSource.BACKGROUND));
            }
        }

        String color = LabColor.toHex(median(model, background));
        BackgroundVerdict verdict;
        if (!foreign.isEmpty()) {
            verdict = BackgroundVerdict.OBJECTS;
        } else if (uniformity >= CLEAN_UNIFORMITY && edgeDensity <= CLEAN_EDGE_DENSITY) {
            verdict = BackgroundVerdict.CLEAN;
        } else {
            verdict = BackgroundVerdict.NOISY;
        }

        return new BackgroundCheckResponse(
            verdict,
            verdict == BackgroundVerdict.CLEAN,
            width,
            height,
            box(bounding(components, parts), total, scale),
            new BackgroundStatsResponse(color, round(uniformity), round(edgeDensity)),
            List.copyOf(foreign)
        );
    }

    /** Binary mask of the objects. */
    static BinaryMask threshold(BufferedImage mask) {
        int w = mask.getWidth();
        int h = mask.getHeight();
        boolean[] pixels = new boolean[w * h];
        var raster = mask.getRaster();
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                pixels[y * w + x] = raster.getSample(x, y, 0) > MASK_THRESHOLD;
            }
        }
        return new BinaryMask(pixels, w, h);
    }

    /** Components that form the product: the largest one plus parts comparable to it (e.g. its box). 1-based labels. */
    static List<Integer> productParts(List<Blob> components) {
        int largest = components.stream().mapToInt(Blob::area).max().orElse(0);
        return IntStream.rangeClosed(1, components.size())
            .filter(label -> components.get(label - 1).area() >= PRODUCT_PART_SHARE * largest)
            .boxed()
            .toList();
    }

    static Blob bounding(List<Blob> components, List<Integer> parts) {
        List<Blob> selected = parts.stream().map(label -> components.get(label - 1)).toList();
        return new Blob(
            selected.stream().mapToInt(Blob::minX).min().orElseThrow(),
            selected.stream().mapToInt(Blob::minY).min().orElseThrow(),
            selected.stream().mapToInt(Blob::maxX).max().orElseThrow(),
            selected.stream().mapToInt(Blob::maxY).max().orElseThrow(),
            selected.stream().mapToInt(Blob::area).sum()
        );
    }

    private static boolean touches(int[] labels, int label, BinaryMask region) {
        for (int i = 0; i < labels.length; i++) {
            if (labels[i] == label && region.pixels()[i]) {
                return true;
            }
        }
        return false;
    }

    private static ObjectBoxResponse box(Blob component, int total, double scale) {
        return new ObjectBoxResponse(
            (int) Math.round(component.minX() * scale),
            (int) Math.round(component.minY() * scale),
            (int) Math.round(component.boxWidth() * scale),
            (int) Math.round(component.boxHeight() * scale),
            round((double) component.area() / total)
        );
    }

    private static double distance(double[] a, double[] b) {
        double dl = a[0] - b[0];
        double da = a[1] - b[1];
        double db = a[2] - b[2];
        return Math.sqrt(dl * dl + da * da + db * db);
    }

    private static double[] median(double[][] values, BinaryMask selection) {
        double[] result = new double[3];
        for (int channel = 0; channel < 3; channel++) {
            final int c = channel;
            double[] selected = IntStream.range(0, values.length)
                .filter(i -> selection.pixels()[i])
                .mapToDouble(i -> values[i][c])
                .sorted()
                .toArray();
            int middle = selected.length / 2;
            result[channel] = selected.length % 2 == 1 ? selected[middle] : (selected[middle - 1] + selected[middle]) / 2;
        }
        return result;
    }

    private static double round(double value) {
        return Math.round(value * 10_000) / 10_000.0;
    }

    /** Smooth quadratic surface fitted to the background colour, so plain colour and soft gradients both fit it. */
    static final class BackgroundModel {
        private static final int FEATURES = 6;
        private static final int MAX_SAMPLES = 20_000;

        private BackgroundModel() {
        }

        static double[][] fit(double[][] lab, BinaryMask background) {
            int w = background.width();
            int h = background.height();
            double norm = Math.max(w, h);
            int step = Math.max(1, background.count() / MAX_SAMPLES);

            // Least squares through the normal equations, one right-hand side per Lab channel
            double[][] normal = new double[FEATURES][FEATURES];
            double[][] rhs = new double[3][FEATURES];
            int seen = 0;
            for (int i = 0; i < lab.length; i++) {
                if (!background.pixels()[i] || seen++ % step != 0) {
                    continue;
                }
                double[] f = features((i % w) / norm, (i / w) / norm);
                for (int r = 0; r < FEATURES; r++) {
                    for (int c = 0; c < FEATURES; c++) {
                        normal[r][c] += f[r] * f[c];
                    }
                    for (int channel = 0; channel < 3; channel++) {
                        rhs[channel][r] += f[r] * lab[i][channel];
                    }
                }
            }
            double[][] coefficients = new double[3][];
            for (int channel = 0; channel < 3; channel++) {
                coefficients[channel] = solve(normal, rhs[channel]);
            }

            double[][] model = new double[lab.length][3];
            for (int i = 0; i < lab.length; i++) {
                double[] f = features((i % w) / norm, (i / w) / norm);
                for (int channel = 0; channel < 3; channel++) {
                    double value = 0;
                    for (int k = 0; k < FEATURES; k++) {
                        value += coefficients[channel][k] * f[k];
                    }
                    model[i][channel] = value;
                }
            }
            return model;
        }

        private static double[] features(double x, double y) {
            return new double[] {1, x, y, x * x, x * y, y * y};
        }

        /** Gaussian elimination with partial pivoting; near-singular columns get a zero coefficient. */
        private static double[] solve(double[][] matrix, double[] vector) {
            int n = vector.length;
            double[][] a = new double[n][];
            for (int r = 0; r < n; r++) {
                a[r] = Arrays.copyOf(matrix[r], n + 1);
                a[r][n] = vector[r];
            }
            for (int col = 0; col < n; col++) {
                int pivot = col;
                for (int r = col + 1; r < n; r++) {
                    if (Math.abs(a[r][col]) > Math.abs(a[pivot][col])) {
                        pivot = r;
                    }
                }
                double[] swap = a[col];
                a[col] = a[pivot];
                a[pivot] = swap;
                if (Math.abs(a[col][col]) < 1e-12) {
                    continue;
                }
                for (int r = 0; r < n; r++) {
                    if (r == col) {
                        continue;
                    }
                    double factor = a[r][col] / a[col][col];
                    for (int c = col; c <= n; c++) {
                        a[r][c] -= factor * a[col][c];
                    }
                }
            }
            double[] solution = new double[n];
            for (int r = 0; r < n; r++) {
                solution[r] = Math.abs(a[r][r]) < 1e-12 ? 0 : a[r][n] / a[r][r];
            }
            return solution;
        }
    }
}
