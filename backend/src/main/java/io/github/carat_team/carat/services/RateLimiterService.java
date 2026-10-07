package io.github.carat_team.carat.services;

public interface RateLimiterService {
    boolean tryConsume(String key);
}
