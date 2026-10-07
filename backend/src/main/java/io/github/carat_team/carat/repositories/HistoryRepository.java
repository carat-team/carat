package io.github.carat_team.carat.repositories;

import io.github.carat_team.carat.entities.HistoryRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface HistoryRepository extends JpaRepository<HistoryRecord, UUID> {
}
