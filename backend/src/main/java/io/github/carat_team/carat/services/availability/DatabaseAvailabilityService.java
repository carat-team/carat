package io.github.carat_team.carat.services.availability;

import io.github.carat_team.carat.repositories.HistoryRepository;

import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;

@Service
public class DatabaseAvailabilityService implements AvailabilityService {
    private final HistoryRepository historyRepository;

    DatabaseAvailabilityService(HistoryRepository historyRepository) {
        this.historyRepository = historyRepository;
    }

    @Override
    public boolean isAvailable() {
        try {
            historyRepository.count();
            return true;
        } catch (DataAccessException e) {
            return false;
        }
    }

    @Override
    public String getStatus() {
        return isAvailable()
            ? "AVAILABLE"
            : "UNAVAILABLE";
    }
}
