package io.github.carat_team.carat.controllers;

import io.github.carat_team.carat.dto.StatusResponse;
import io.github.carat_team.carat.services.StatusService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class StatusController {

    private final StatusService statusService;

    public StatusController(StatusService statusService) {
        this.statusService = statusService;
    }

    @GetMapping("/api/status")
    public ResponseEntity<StatusResponse> getStatus() {
        return ResponseEntity.ok(statusService.getStatus());
    }
}
