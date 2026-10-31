package io.github.carat_team.carat.services.background;

import java.util.ArrayList;
import java.util.List;

/**
 * Binary image of {@code width x height} pixels stored row by row, with the morphology and
 * connected-component operations the background check needs.
 */
record BinaryMask(boolean[] pixels, int width, int height) {

    record Blob(int minX, int minY, int maxX, int maxY, int area) {
        int boxWidth() {
            return maxX - minX + 1;
        }

        int boxHeight() {
            return maxY - minY + 1;
        }
    }

    /** Pixel labels (0 = not set, i = index + 1 in {@code components}) and component stats. */
    record Labeling(int[] labels, List<Blob> components) {
    }

    static BinaryMask empty(int width, int height) {
        return new BinaryMask(new boolean[width * height], width, height);
    }

    boolean get(int x, int y) {
        return pixels[y * width + x];
    }

    int count() {
        int count = 0;
        for (boolean pixel : pixels) {
            if (pixel) {
                count++;
            }
        }
        return count;
    }

    BinaryMask not() {
        boolean[] result = new boolean[pixels.length];
        for (int i = 0; i < pixels.length; i++) {
            result[i] = !pixels[i];
        }
        return new BinaryMask(result, width, height);
    }

    BinaryMask and(BinaryMask other) {
        boolean[] result = new boolean[pixels.length];
        for (int i = 0; i < pixels.length; i++) {
            result[i] = pixels[i] && other.pixels[i];
        }
        return new BinaryMask(result, width, height);
    }

    /** Dilation with a square {@code (2 * radius + 1)} kernel; pixels outside the image count as unset. */
    BinaryMask dilate(int radius) {
        if (radius <= 0) {
            return this;
        }
        boolean[] horizontal = new boolean[pixels.length];
        int[] prefix = new int[Math.max(width, height) + 1];
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                prefix[x + 1] = prefix[x] + (pixels[y * width + x] ? 1 : 0);
            }
            for (int x = 0; x < width; x++) {
                horizontal[y * width + x] = prefix[Math.min(width, x + radius + 1)] - prefix[Math.max(0, x - radius)] > 0;
            }
        }
        boolean[] result = new boolean[pixels.length];
        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                prefix[y + 1] = prefix[y] + (horizontal[y * width + x] ? 1 : 0);
            }
            for (int y = 0; y < height; y++) {
                result[y * width + x] = prefix[Math.min(height, y + radius + 1)] - prefix[Math.max(0, y - radius)] > 0;
            }
        }
        return new BinaryMask(result, width, height);
    }

    /** Erosion with a square kernel; pixels outside the image count as set (as in OpenCV). */
    BinaryMask erode(int radius) {
        return not().dilate(radius).not();
    }

    /** Morphological opening: removes specks smaller than the kernel. */
    BinaryMask open(int radius) {
        return erode(radius).dilate(radius);
    }

    /** 8-connected components of the set pixels. */
    Labeling label() {
        int[] labels = new int[pixels.length];
        List<Blob> components = new ArrayList<>();
        int[] queue = new int[pixels.length];

        for (int start = 0; start < pixels.length; start++) {
            if (!pixels[start] || labels[start] != 0) {
                continue;
            }
            int label = components.size() + 1;
            int head = 0;
            int tail = 0;
            queue[tail++] = start;
            labels[start] = label;
            int minX = width;
            int minY = height;
            int maxX = -1;
            int maxY = -1;

            while (head < tail) {
                int index = queue[head++];
                int x = index % width;
                int y = index / width;
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);

                for (int dy = -1; dy <= 1; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        int nx = x + dx;
                        int ny = y + dy;
                        if (nx < 0 || ny < 0 || nx >= width || ny >= height) {
                            continue;
                        }
                        int neighbor = ny * width + nx;
                        if (pixels[neighbor] && labels[neighbor] == 0) {
                            labels[neighbor] = label;
                            queue[tail++] = neighbor;
                        }
                    }
                }
            }
            components.add(new Blob(minX, minY, maxX, maxY, tail));
        }
        return new Labeling(labels, List.copyOf(components));
    }

    /** Pixels whose label is one of {@code selected} (1-based labels). */
    static BinaryMask ofLabels(Labeling labeling, List<Integer> selected, int width, int height) {
        boolean[] chosen = new boolean[labeling.components().size() + 1];
        for (int label : selected) {
            chosen[label] = true;
        }
        boolean[] result = new boolean[width * height];
        for (int i = 0; i < result.length; i++) {
            result[i] = chosen[labeling.labels()[i]];
        }
        return new BinaryMask(result, width, height);
    }
}
