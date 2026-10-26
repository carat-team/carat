package io.github.carat_team.carat.services.background;

/** sRGB (D65) to CIE Lab conversion and back, matching OpenCV {@code COLOR_RGB2LAB} on 0..1 input. */
final class LabColor {
    private static final double WHITE_X = 0.950456;
    private static final double WHITE_Z = 1.088754;
    private static final double[] LINEAR = new double[256];

    static {
        for (int i = 0; i < 256; i++) {
            double c = i / 255.0;
            LINEAR[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        }
    }

    private LabColor() {
    }

    /** Converts a packed {@code 0xRRGGBB} pixel to {@code {L, a, b}}. */
    static double[] fromRgb(int rgb) {
        double r = LINEAR[(rgb >> 16) & 0xff];
        double g = LINEAR[(rgb >> 8) & 0xff];
        double b = LINEAR[rgb & 0xff];

        double x = (0.412453 * r + 0.357580 * g + 0.180423 * b) / WHITE_X;
        double y = 0.212671 * r + 0.715160 * g + 0.072169 * b;
        double z = (0.019334 * r + 0.119193 * g + 0.950227 * b) / WHITE_Z;

        double fx = f(x);
        double fy = f(y);
        double fz = f(z);
        double lightness = y > 0.008856 ? 116 * fy - 16 : 903.3 * y;
        return new double[] {lightness, 500 * (fx - fy), 200 * (fy - fz)};
    }

    /** Converts {@code {L, a, b}} to a {@code #rrggbb} string, clipping out-of-gamut values. */
    static String toHex(double[] lab) {
        double fy = (lab[0] + 16) / 116;
        double fx = fy + lab[1] / 500;
        double fz = fy - lab[2] / 200;

        double x = finv(fx) * WHITE_X;
        double y = finv(fy);
        double z = finv(fz) * WHITE_Z;

        double r = 3.240479 * x - 1.537150 * y - 0.498535 * z;
        double g = -0.969256 * x + 1.875992 * y + 0.041556 * z;
        double b = 0.055648 * x - 0.204043 * y + 1.057311 * z;
        return "#%02x%02x%02x".formatted(toByte(r), toByte(g), toByte(b));
    }

    private static double f(double t) {
        return t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16.0 / 116;
    }

    private static double finv(double t) {
        double cube = t * t * t;
        return cube > 0.008856 ? cube : (t - 16.0 / 116) / 7.787;
    }

    private static int toByte(double linear) {
        double c = Math.clamp(linear, 0.0, 1.0);
        double srgb = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
        return (int) Math.round(Math.clamp(srgb, 0.0, 1.0) * 255);
    }
}
