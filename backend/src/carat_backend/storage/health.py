"""Probes of the dependencies the API needs.

Each probe has its own connection settings and short timeouts. They do not share the pool or the client of the
request path: a busy pool or a long retry loop there must not make a probe wait, and a hung probe must not hold
a connection a request needs.
"""

import certifi
import urllib3
from minio import Minio
from sqlalchemy import URL, Engine, create_engine, text

from carat_backend.settings import ObjectStorageSettings


class DatabaseProbe:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def check(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))


class ObjectStoreProbe:
    def __init__(self, client: Minio, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def check(self) -> None:
        # The bucket is created on the first upload, so a missing bucket is not a failure here. An unreachable
        # endpoint, a wrong key or a failing server raises.
        self._client.bucket_exists(bucket_name=self._bucket)


def create_database_probe(database_url: URL | str, timeout_seconds: int) -> DatabaseProbe:
    engine = create_engine(
        database_url,
        # libpq limits: connecting, and one query (milliseconds)
        connect_args={"connect_timeout": timeout_seconds, "options": f"-c statement_timeout={timeout_seconds * 1000}"},
        pool_size=2,
        max_overflow=0,
        pool_timeout=timeout_seconds,
        pool_pre_ping=True,
    )
    return DatabaseProbe(engine)


def create_object_store_probe(settings: ObjectStorageSettings, timeout_seconds: int) -> ObjectStoreProbe:
    http_client = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=timeout_seconds, read=timeout_seconds),
        # No retries: the default client retries with backoff, which is minutes for an unreachable endpoint
        retries=urllib3.Retry(total=0),
        cert_reqs="CERT_REQUIRED",
        ca_certs=certifi.where(),
    )
    client = Minio(
        endpoint=settings.endpoint,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        secure=settings.secure,
        http_client=http_client,
    )
    return ObjectStoreProbe(client, settings.bucket)
