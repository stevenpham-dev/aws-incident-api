# Teardown — AWS Incident API

Purpose: remove AWS resources to avoid ongoing costs.

## Delete API Gateway
- **API Gateway → HTTP APIs**
  - Delete: `AWS-IncidentAPI-HTTP`

## Delete Lambda
- **Lambda**
  - Delete function: `AWS-IncidentAPI-Lambda`
- **CloudWatch Logs (optional cleanup)**
  - Delete log group for the Lambda function

## Delete DynamoDB
- **DynamoDB**
  - Delete table: `AWS-IncidentReports`

## Delete CloudWatch Alarms
- **CloudWatch → Alarms**
  - Delete: `AWS-IncidentAPI-Lambda-Errors`
  - Delete: `AWS-IncidentAPI-Lambda-Throttles` (if created)

## Delete SNS
- **SNS → Topics**
  - Delete: `AWS-IncidentAPI-Alerts`
  - (Email subscription is removed with the topic)

## Delete IAM Role
- **IAM → Roles**
  - Delete: `AWS-IncidentAPI-LambdaRole`