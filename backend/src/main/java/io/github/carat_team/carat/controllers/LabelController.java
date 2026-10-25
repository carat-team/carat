package io.github.carat_team.carat.controllers;

import io.github.carat_team.carat.dto.LabelScanResponse;
import io.github.carat_team.carat.services.LabelScanService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/analyze/label")
public class LabelController {

    private final LabelScanService labelScanService;

    public LabelController(LabelScanService labelScanService) {
        this.labelScanService = labelScanService;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<LabelScanResponse> scanLabel(@RequestPart("file") MultipartFile file) {
        return ResponseEntity.ok(labelScanService.scan(file));
    }
}
