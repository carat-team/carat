package io.github.carat_team.carat.dto;

import java.util.List;

public record LabelScanResponse(
    List<BarcodeResponse> barcodes,
    List<TextBlockResponse> texts
) {
}
