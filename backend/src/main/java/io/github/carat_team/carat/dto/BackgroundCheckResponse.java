package io.github.carat_team.carat.dto;

import java.util.List;

/**
 * Background check of a product photo. Boxes are in pixels of the uploaded image, as stored
 * (EXIF orientation is not applied).
 *
 * @param verdict        overall result
 * @param ok             {@code true} only for {@link BackgroundVerdict#CLEAN}
 * @param mainObject     the product (bottle with its box), {@code null} when nothing was found
 * @param foreignObjects other objects in the frame
 */
public record BackgroundCheckResponse(
    BackgroundVerdict verdict,
    boolean ok,
    int width,
    int height,
    ObjectBoxResponse mainObject,
    BackgroundStatsResponse background,
    List<ForeignObjectResponse> foreignObjects
) {

    public enum BackgroundVerdict {
        /** Plain colour or a smooth gradient, nothing else in the frame. */
        CLEAN,
        /** Textured or uneven background without separate objects. */
        NOISY,
        /** Something besides the product is in the frame. */
        OBJECTS,
        /** No product found. */
        NO_OBJECT
    }

    /**
     * @param color       dominant background colour, {@code #rrggbb}, {@code null} when unknown
     * @param uniformity  share of background pixels close to the background colour model (0..1)
     * @param edgeDensity share of background pixels lying on edges: texture and details (0..1)
     */
    public record BackgroundStatsResponse(String color, double uniformity, double edgeDensity) {
    }

    /** @param areaShare share of the image area (0..1) */
    public record ObjectBoxResponse(int x, int y, int width, int height, double areaShare) {
    }

    /** @param source how the object was found */
    public record ForeignObjectResponse(ObjectBoxResponse box, ForeignObjectSource source) {
    }

    public enum ForeignObjectSource {
        /** A separate object found by the segmentation model. */
        MASK,
        /** A blob on the background that clearly differs from it. */
        BACKGROUND
    }
}
