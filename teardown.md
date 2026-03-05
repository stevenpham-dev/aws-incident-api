Teardown — AWS Incident API

Purpose: remove AWS resources to avoid ongoing costs.

API Gateway (HTTP API)

Delete the HTTP API: AWS-IncidentAPI-HTTP

Lambda

Delete function: AWS-IncidentAPI-Lambda

Delete associated log group in CloudWatch Logs (optional but clean)

DynamoDB

Delete table: AWS-IncidentReports

If you want to keep the table schema for demo, you can export screenshots first.

IAM

Delete role: AWS-IncidentAPI-LambdaRole

Delete inline policies attached to that role (if separate)

CloudWatch

Delete alarms:

AWS-IncidentAPI-Lambda-Errors

AWS-IncidentAPI-Lambda-Throttles (if used)

SNS

Delete SNS topic: AWS-IncidentAPI-Alerts

Confirm email subscription is removed with the topic deletion

Final sanity check

CloudWatch → Alarms: none remain

DynamoDB → Tables: removed

Lambda: removed

API Gateway: removed

SNS Topics: removed