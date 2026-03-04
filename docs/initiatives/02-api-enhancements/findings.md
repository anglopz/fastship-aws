# Initiative 02: API Enhancements — Findings

---

## Architectural Decisions

### AD-01: Redis-backed rate limiting
Rate limiting uses Redis as the backend store, shared with the cache and Celery broker. Keeps infrastructure simple — no additional services needed. Different rate limits per endpoint category (auth vs signup vs general).

### AD-02: Middleware-based cross-cutting concerns
Rate limiting, caching, and request logging are all implemented as FastAPI middleware. Keeps router code clean and ensures consistent application across all endpoints.

---

## Infrastructure Trade-offs

### IT-01: Shared Redis instance
Rate limiting, response caching, Celery broker, and token blacklist all share a single Redis instance. Simplifies infrastructure but creates a single point of failure. At current scale this is acceptable; at higher load, consider separating Celery broker from cache.

---

## AWS Cost Considerations

_(To be populated — webhook delivery may need SQS/SNS for reliable delivery at scale)_

---

## Risks Identified

_(To be populated as implementation progresses)_

---

## Open Questions

- Should webhooks use direct HTTP delivery or route through SNS/SQS for reliability?
- Is cursor-based pagination a priority given current dataset sizes?
