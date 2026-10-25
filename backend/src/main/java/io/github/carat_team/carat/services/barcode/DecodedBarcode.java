package io.github.carat_team.carat.services.barcode;

import com.google.zxing.BarcodeFormat;

public record DecodedBarcode(
    String text,
    BarcodeFormat format
) {
}
