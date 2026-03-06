# curl Tests — AWS Incident API

Use these commands to validate the deployed API.

## Set the API Gateway Invoke URL

```bash
INVOKE_URL="https://fyqha6h6b5.execute-api.us-west-2.amazonaws.com"
```

---

## 1) Create incident (POST /incidents)

```bash
curl -sS -X POST "$INVOKE_URL/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "ALB 502 errors",
    "severity": "HIGH",
    "service": "api-gateway",
    "description": "Spike in 502 responses observed.",
    "reported_by": "steven",
    "environment": "prod"
  }'
```

Expected response example:

```json
{
  "incident_id": "INC2026-03-05T04:49:39Z-0006159",
  "created_at": "2026-03-05T04:49:39Z",
  "status": "OPEN"
}
```

---

## 2) List incidents (GET /incidents)

```bash
curl -sS "$INVOKE_URL/incidents?limit=20"
```

---

## 3) List incidents by service

Requires DynamoDB GSI: **GSI1-Service-CreatedAt**

```bash
curl -sS "$INVOKE_URL/incidents?service=api-gateway&limit=20"
```

---

## 4) Get incident by ID

Replace `<INCIDENT_ID>` with a real ID.

```bash
curl -sS "$INVOKE_URL/incidents/<INCIDENT_ID>"
```

---

## 5) Update incident status

```bash
curl -sS -X PATCH "$INVOKE_URL/incidents/<INCIDENT_ID>" \
  -H "Content-Type: application/json" \
  -d '{"status":"RESOLVED"}'
```