AWS Serverless Incident API

A serverless incident logging API built on AWS using API Gateway (HTTP API), AWS Lambda (Python), and DynamoDB. The project includes observability with CloudWatch Logs, alerting with CloudWatch Alarms + SNS email notifications, and a documented failure simulation to validate monitoring and least-privilege IAM behavior.

Architecture

Request flow:

Client (curl/Postman)
→ API Gateway (HTTP API)
→ Lambda (Python 3.12)
→ DynamoDB (IncidentReports table + optional GSI)

Observability and alerting:

CloudWatch Logs (Lambda logs)
CloudWatch Alarm (Lambda Errors / Throttles)
SNS Topic → Email subscription

Diagram (add your exported image here):

diagrams/architecture.png

AWS Resources (as deployed)

Region: us-west-2

API Gateway (HTTP API)

Name: AWS-IncidentAPI-HTTP

Routes:

POST /incidents

GET /incidents

GET /incidents/{incident_id}

PATCH /incidents/{incident_id}

Lambda

Function: AWS-IncidentAPI-Lambda

Runtime: Python 3.12

Env vars:

TABLE_NAME=AWS-IncidentReports

DynamoDB

Table: AWS-IncidentReports

Partition key: incident_id (String)

Billing: On-demand

Optional query optimization (recommended)

GSI: GSI1-Service-CreatedAt

Partition key: service (String)

Sort key: created_at (String)

Supports: GET /incidents?service=<service-name>

IAM (least privilege)

Execution role: AWS-IncidentAPI-LambdaRole

Permissions (scoped to the table and index ARN):

dynamodb:PutItem

dynamodb:GetItem

dynamodb:Scan

dynamodb:Query

dynamodb:UpdateItem

CloudWatch Logs permissions:

logs:CreateLogGroup

logs:CreateLogStream

logs:PutLogEvents

Monitoring

Alarm: AWS-IncidentAPI-Lambda-Errors

Metric: AWS/Lambda Errors

Threshold: >= 1 (1 minute)

Action: SNS publish → email notification

Alarm: AWS-IncidentAPI-Lambda-Throttles (optional)

Metric: AWS/Lambda Throttles

Threshold: >= 1

SNS

Topic: AWS-IncidentAPI-Alerts

Subscription: email (confirmed)

API
Create an incident

POST /incidents

Example request body:
{
"title": "ALB 502 errors",
"severity": "HIGH",
"service": "api-gateway",
"description": "Spike in 502 responses observed.",
"reported_by": "steven",
"environment": "prod"
}

Example response:
{
"incident_id": "INC#2026-03-03T01:23:45+00:00#A1B2C3",
"created_at": "2026-03-03T01:23:45+00:00",
"status": "OPEN"
}

List incidents

GET /incidents?limit=20

Optional query:

service=<service-name> (uses the DynamoDB GSI if enabled)

Get an incident

GET /incidents/{incident_id}

Update incident status

PATCH /incidents/{incident_id}

Body:
{ "status": "RESOLVED" }

Allowed:

OPEN

RESOLVED

Testing

See:

examples/curl-tests.md

Failure Simulation (Monitoring + IAM validation)

Goal: prove that monitoring and alerting work and that IAM is truly least-privilege.

Steps:

Remove DynamoDB permissions from the Lambda execution role (temporarily).

Call POST /incidents → expect failure (AccessDeniedException).

Confirm CloudWatch Logs show the error.

Confirm CloudWatch Alarm enters ALARM state (Lambda Errors).

Confirm SNS sends email notification.

Restore the DynamoDB permissions.

Call POST /incidents again → success.

Confirm the alarm returns to OK.

This provides an “incident response” story for Cloud Support / Cloud Engineer interviews.

Screenshots

Place screenshots in screenshots/ and reference them here (recommended numbering):

01-api-gateway-routes.png

02-lambda-config-env.png

03-dynamodb-table.png

04-iam-least-privilege.png

05-cloudwatch-logs-success.png

06-alarm-errors.png

07-sns-email.png

08-failure-accessdenied-logs.png

09-alarm-in-alarm.png

Teardown / Cost Control

See:

teardown.md