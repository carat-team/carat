package io.github.carat_team.carat.controllers;

import io.github.carat_team.carat.dto.BackgroundCheckResponse;
import io.github.carat_team.carat.services.background.BackgroundCheckService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/analyze/background")
public class BackgroundController {

    private final BackgroundCheckService backgroundCheckService;

    public BackgroundController(BackgroundCheckService backgroundCheckService) {
        this.backgroundCheckService = backgroundCheckService;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<BackgroundCheckResponse> checkBackground(@RequestPart("file") MultipartFile file) {
        return ResponseEntity.ok(backgroundCheckService.check(file));
    }

    @PostMapping(path = "/cutout", consumes = MediaType.MULTIPART_FORM_DATA_VALUE, produces = MediaType.IMAGE_PNG_VALUE)
    public ResponseEntity<byte[]> cutOut(@RequestPart("file") MultipartFile file) {
        return ResponseEntity.ok().contentType(MediaType.IMAGE_PNG).body(backgroundCheckService.cutOut(file));
    }
}
