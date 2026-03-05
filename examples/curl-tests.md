curl Tests — AWS Incident API

Replace:

<INVOKE_URL> with your API Gateway invoke URL (no trailing slash)

Example:
INVOKE_URL="https://fyqha6h6b5.execute-api.us-west-2.amazonaws.com
"

Create incident (POST /incidents)

curl -sS -X POST "$INVOKE_URL/incidents"
-H "Content-Type: application/json"
-d '{
"title": "ALB 502 errors",
"severity": "HIGH",
"service": "api-gateway",
"description": "Spike in 502 responses observed.",
"reported_by": "steven",
"environment": "prod"
}'

List incidents (GET /incidents)

curl -sS "$INVOKE_URL/incidents?limit=20"

List incidents by service (GET /incidents?service=...)

Requires DynamoDB GSI (GSI1-Service-CreatedAt)

curl -sS "$INVOKE_URL/incidents?service=api-gateway&limit=20"

Get incident by id (GET /incidents/{incident_id})

Replace <INCIDENT_ID> with a real ID from the create/list output.

curl -sS "$INVOKE_URL/incidents/<INCIDENT_ID>"

Update incident status (PATCH /incidents/{incident_id})

curl -sS -X PATCH "$INVOKE_URL/incidents/<INCIDENT_ID>"
-H "Content-Type: application/json"
-d '{"status":"RESOLVED"}'