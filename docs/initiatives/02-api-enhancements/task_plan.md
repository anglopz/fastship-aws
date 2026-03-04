# Initiative 02: API Enhancements

**Scope:** Webhooks, bulk operations, advanced search, API hardening
**Covers:** Extending the API layer beyond current feature set

---

## Phase 0 — Rate Limiting & Caching (Complete)

- [x] Step 1: Rate limiting middleware — 10 req/min auth endpoints, 5 req/5min signup, Redis backend
- [x] Step 2: Response caching middleware — implemented with Redis
- [x] Step 3: Request logging middleware — performance metrics tracking

## Phase 1 — Search & Filtering (Not Started)

- [ ] Step 1: Advanced search — full-text search on shipments, sellers, delivery partners
- [ ] Step 2: Filtering — query parameter-based filtering with Pydantic validation
- [ ] Step 3: Cursor-based pagination — replace offset pagination for large datasets

## Phase 2 — Bulk Operations & Webhooks (Not Started)

- [ ] Step 1: Bulk operations API — batch create/update shipments via Celery tasks
- [ ] Step 2: Webhook registration — CRUD endpoints for webhook subscriptions
- [ ] Step 3: Webhook delivery — event-driven notifications with exponential backoff retry
- [ ] Step 4: Webhook security — HMAC signatures, delivery verification

## Phase 3 — API Hardening (Not Started)

- [ ] Step 1: Input validation audit — review all Pydantic schemas for edge cases
- [ ] Step 2: API versioning — implement /v1/ prefix strategy for future breaking changes
- [ ] Step 3: OpenAPI spec export — automated SDK generation from schema
- [ ] Step 4: Integration test expansion — cover all error paths and edge cases
