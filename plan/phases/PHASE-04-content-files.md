# Phase 4 — Posts, links, and learning materials

**Status:** Not started
**Goal:** Let communities share useful content safely, including PDFs and documents.

## Backend-first sequencing

Complete the content APIs, persistence, storage adapter contract, authorization,
and edge-case tests before building or extending any frontend flow.

## Backend work

- Implement text/link posts and approved edit/delete, save/bookmark, and reporting flows.
- Add private object storage integration with upload-intent/completion, short-lived authorized downloads, metadata, quotas, and file type/size checks.
- Add malware/content scanning and moderation handling as appropriate to selected providers and risk assessment.
- Define retention and deletion of content, attachments, and orphaned storage objects.
- Test unauthorized reads, invalid links, duplicate/retried uploads, size/type
  boundaries, expired download grants, orphan cleanup, and deleted content.

## Deferred frontend work

Feed, compose, upload, preview/download, saved-material, and report UI changes
wait until the Backend Completion Gate.

## Exit criteria

- Unauthorized users cannot read private content or obtain valid file URLs.
- Uploads are bounded, validated, retry-safe, and do not store file bytes in PostgreSQL.
- API and mobile tests cover upload failure, duplicate completion, expired URL, removed content, and deletion.
