from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # How many cards may run checks at the same time; heavy checks share one process
    check_concurrency: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
