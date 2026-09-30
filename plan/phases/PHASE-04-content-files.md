# Phase 4 — Posts, links, and learning materials

**Status:** Not started
**Goal:** Let communities share useful content safely, including PDFs and documents.

## Work

- Implement text/link posts and approved edit/delete, save/bookmark, and reporting flows.
- Add private object storage integration with upload-intent/completion, short-lived authorized downloads, metadata, quotas, and file type/size checks.
- Add malware/content scanning and moderation handling as appropriate to selected providers and risk assessment.
- Build feed/list/detail, compose, attach/upload/progress/retry, preview/download, saved-material, and report interfaces.
- Define retention and deletion of content, attachments, and orphaned storage objects.

## Exit criteria

- Unauthorized users cannot read private content or obtain valid file URLs.
- Uploads are bounded, validated, retry-safe, and do not store file bytes in PostgreSQL.
- API and mobile tests cover upload failure, duplicate completion, expired URL, removed content, and deletion.
