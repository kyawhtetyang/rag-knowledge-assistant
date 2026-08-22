# Changelog

All notable changes to this project are documented here.

## [Unreleased]

## [0.9.0] - 2026-08-22

### Changed
- Worker is the sole owner of queued async ingestion execution.
- Async upload acceptance returns HTTP 202.
- Production CORS origins are explicit and configurable.
- Internal server errors are logged server-side and no longer expose raw exception strings to clients.

### Added
- Upload and text-ingestion request limits.
- Optional admin-key protection for demo-data cleanup.
- Backend regression tests for file validation, redaction, and production configuration.
- GitHub Actions CI for migrations/tests, frontend lint/build, and backend Docker build.
- Architecture and release-process documentation.

### Release policy
- `v0.9.x` is the production-foundation stabilization line.
- `v1.0.0` is reserved for the first deployment-validated production-stable contract.
