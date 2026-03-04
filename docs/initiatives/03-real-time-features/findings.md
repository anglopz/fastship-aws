# Initiative 03: Real-Time Features — Findings

---

## Architectural Decisions

_(To be populated as decisions are made during implementation)_

---

## Infrastructure Trade-offs

### IT-01: WebSocket scaling consideration
Current ECS Fargate deployment runs behind an ALB. ALB supports WebSocket connections natively, but scaling WebSocket services requires sticky sessions or Redis pub/sub for cross-instance message broadcasting. This is more complex than HTTP scaling.

---

## AWS Cost Considerations

- ALB charges per WebSocket connection hour (same as HTTP connection)
- Long-lived WebSocket connections increase ALB costs vs short HTTP requests
- Redis pub/sub for cross-instance broadcast uses existing ElastiCache — no additional cost
- GraphQL doesn't add infrastructure cost — same ECS service

---

## Risks Identified

_(To be populated as risks are discovered)_

---

## Open Questions

- Is Strawberry the right GraphQL library, or should we evaluate Ariadne?
- Should WebSocket and REST API share the same ECS service or be separated?
- What analytics retention period is appropriate?
