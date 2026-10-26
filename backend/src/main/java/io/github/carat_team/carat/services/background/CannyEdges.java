package io.github.carat_team.carat.services.background;

/** Canny edge detector with a 3x3 Sobel and L1 gradient, as OpenCV {@code Canny(gray, low, high)}. */
final class CannyEdges {
    private static final double TAN_22_5 = Math.tan(Math.toRadians(22.5));
    private static final double TAN_67_5 = Math.tan(Math.toRadians(67.5));

    private CannyEdges() {
    }

    static BinaryMask detect(int[] gray, int width, int height, int lowThreshold, int highThreshold) {
        int[] gx = new int[gray.length];
        int[] gy = new int[gray.length];
        int[] magnitude = new int[gray.length];
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int tl = at(gray, width, height, x - 1, y - 1);
                int tc = at(gray, width, height, x, y - 1);
                int tr = at(gray, width, height, x + 1, y - 1);
                int ml = at(gray, width, height, x - 1, y);
                int mr = at(gray, width, height, x + 1, y);
                int bl = at(gray, width, height, x - 1, y + 1);
                int bc = at(gray, width, height, x, y + 1);
                int br = at(gray, width, height, x + 1, y + 1);
                int i = y * width + x;
                gx[i] = (tr + 2 * mr + br) - (tl + 2 * ml + bl);
                gy[i] = (bl + 2 * bc + br) - (tl + 2 * tc + tr);
                magnitude[i] = Math.abs(gx[i]) + Math.abs(gy[i]);
            }
        }

        // Non-maximum suppression: keep pixels that are local maxima along the gradient direction
        byte[] state = new byte[gray.length]; // 0 = none, 1 = weak, 2 = strong
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int i = y * width + x;
                int m = magnitude[i];
                if (m <= lowThreshold) {
                    continue;
                }
                double ax = Math.abs(gx[i]);
                double ay = Math.abs(gy[i]);
                int before;
                int after;
                if (ay <= ax * TAN_22_5) {
                    before = mag(magnitude, width, height, x - 1, y);
                    after = mag(magnitude, width, height, x + 1, y);
                } else if (ay >= ax * TAN_67_5) {
                    before = mag(magnitude, width, height, x, y - 1);
                    after = mag(magnitude, width, height, x, y + 1);
                } else if ((gx[i] > 0) == (gy[i] > 0)) {
                    before = mag(magnitude, width, height, x - 1, y - 1);
                    after = mag(magnitude, width, height, x + 1, y + 1);
                } else {
                    before = mag(magnitude, width, height, x + 1, y - 1);
                    after = mag(magnitude, width, height, x - 1, y + 1);
                }
                if (m > before && m >= after) {
                    state[i] = (byte) (m > highThreshold ? 2 : 1);
                }
            }
        }

        // Hysteresis: weak edges survive only when connected to a strong one
        boolean[] edges = new boolean[gray.length];
        int[] stack = new int[gray.length];
        for (int start = 0; start < gray.length; start++) {
            if (state[start] != 2 || edges[start]) {
                continue;
            }
            int top = 0;
            stack[top++] = start;
            edges[start] = true;
            while (top > 0) {
                int index = stack[--top];
                int x = index % width;
                int y = index / width;
                for (int dy = -1; dy <= 1; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        int nx = x + dx;
                        int ny = y + dy;
                        if (nx < 0 || ny < 0 || nx >= width || ny >= height) {
                            continue;
                        }
                        int neighbor = ny * width + nx;
                        if (state[neighbor] != 0 && !edges[neighbor]) {
                            edges[neighbor] = true;
                            stack[top++] = neighbor;
                        }
                    }
                }
            }
        }
        return new BinaryMask(edges, width, height);
    }

    private static int at(int[] values, int width, int height, int x, int y) {
        return values[Math.clamp(y, 0, height - 1) * width + Math.clamp(x, 0, width - 1)];
    }

    private static int mag(int[] magnitude, int width, int height, int x, int y) {
        if (x < 0 || y < 0 || x >= width || y >= height) {
            return 0;
        }
        return magnitude[y * width + x];
    }
}
