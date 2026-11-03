# ADR 0002. Store product photos in S3-compatible object storage

Status: accepted
Date: 2026-10-31

## Context

The MVP (`CARAT_MVP.xlsx`, sheet 04) keeps photo metadata in `product_photos` and the files outside the
database, "in a folder or object storage". Files on a mounted directory tie the backend to one host and need
their own backup story; bytes in PostgreSQL bloat the database and its backups.

## Decision

- Photo bytes go to an S3-compatible bucket; `product_photos` keeps metadata and the object key
  (`products/<product_id>/<photo_id>.<ext>`).
- The backend talks plain S3 through the `minio` Python client, so any S3 service works by configuration.
- Locally and in compose the server is RustFS (`rustfs/rustfs`). MinIO stopped publishing community images
  in 2026, which ruled it out as the default server.
- The backend serves images through `GET /api/products/{id}/photos/{photoId}/content`; the bucket is not exposed.

## Consequences

- One more service in compose and in the backend test setup (`just backend test-services`).
- Storage keys (`S3_ACCESS_KEY`, `S3_SECRET_KEY`) join the database credentials in `.env`.
- Moving to a managed S3 (or the ЧЗ infrastructure) changes settings, not code.
