package io.github.carat_team.carat.services;

import io.github.carat_team.carat.services.availability.DatabaseAvailabilityService;
import io.github.carat_team.carat.services.availability.MLServiceAvailabilityService;
import io.github.carat_team.carat.services.availability.RedisAvailabilityService;
import org.springframework.boot.availability.ApplicationAvailability;
import org.springframework.stereotype.Service;

import io.github.carat_team.carat.dto.StatusResponse;

@Service
public class StatusService {
    private final ApplicationAvailability applicationAvailability;
    private final MLServiceAvailabilityService MLServiceAvailabilityService;
    private final DatabaseAvailabilityService databaseAvailabilityService;
    private final RedisAvailabilityService redisAvailabilityService;

    public StatusService(
        ApplicationAvailability applicationAvailability,
        MLServiceAvailabilityService MLServiceAvailabilityService,
        DatabaseAvailabilityService databaseAvailabilityService,
        RedisAvailabilityService redisAvailabilityService
    ) {
        this.applicationAvailability = applicationAvailability;
        this.MLServiceAvailabilityService = MLServiceAvailabilityService;
        this.databaseAvailabilityService = databaseAvailabilityService;
        this.redisAvailabilityService = redisAvailabilityService;
    }

    public StatusResponse getStatus() {
        return new StatusResponse(
            applicationAvailability.getLivenessState().toString(),
            applicationAvailability.getReadinessState().toString(),
            MLServiceAvailabilityService.getStatus(),
            databaseAvailabilityService.getStatus(),
            redisAvailabilityService.getStatus()
        );
    }
}
