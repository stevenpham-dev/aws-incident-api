import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get("TABLE_NAME", "").strip()
if not TABLE_NAME:
    logger.error("Missing required env var TABLE_NAME")

table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None

ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
ALLOWED_ENVIRONMENTS = {"dev", "test", "stage", "prod"}
ALLOWED_STATUS = {"OPEN", "RESOLVED"}

GSI_SERVICE_CREATEDAT = "GSI1-Service-CreatedAt"

JSON_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
}

def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(body),
    }

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _new_incident_id(now_iso: str) -> str:
    suffix = uuid.uuid4().hex[:6].upper()
    return f"INC#{now_iso}#{suffix}"

def _parse_json_body(event: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    raw = event.get("body")
    if raw is None or raw == "":
        return None, "Request body is required."
    try:
        if event.get("isBase64Encoded"):
            import base64
            raw = base64.b64decode(raw).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "Body must be a JSON object."
        return data, None
    except json.JSONDecodeError:
        return None, "Invalid JSON body."

def _get_request_id(event: Dict[str, Any]) -> str:
    rc = event.get("requestContext", {}) or {}
    return rc.get("requestId") or str(uuid.uuid4())

def _get_method_path(event: Dict[str, Any]) -> Tuple[str, str]:
    rc = event.get("requestContext", {}) or {}
    http = rc.get("http", {}) or {}
    method = (http.get("method") or "").upper()
    path = event.get("rawPath") or ""
    return method, path

def _get_path_param(event: Dict[str, Any], name: str) -> Optional[str]:
    params = event.get("pathParameters") or {}
    return params.get(name)

def _get_query_param(event: Dict[str, Any], name: str) -> Optional[str]:
    qs = event.get("queryStringParameters") or {}
    return qs.get(name)

def _parse_limit(event: Dict[str, Any], default: int = 20) -> Tuple[int, Optional[str]]:
    limit_str = _get_query_param(event, "limit")
    limit = default
    if limit_str:
        try:
            limit = max(1, min(100, int(limit_str)))
        except ValueError:
            return 0, "limit must be an integer between 1 and 100."
    return limit, None

def _validate_create(payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    required = ["title", "severity", "service", "description", "reported_by", "environment"]
    missing = [k for k in required if not str(payload.get(k, "")).strip()]
    if missing:
        return None, f"Missing required field(s): {', '.join(missing)}"

    severity = str(payload["severity"]).strip().upper()
    if severity not in ALLOWED_SEVERITIES:
        return None, f"severity must be one of: {sorted(ALLOWED_SEVERITIES)}"

    environment = str(payload["environment"]).strip().lower()
    if environment not in ALLOWED_ENVIRONMENTS:
        return None, f"environment must be one of: {sorted(ALLOWED_ENVIRONMENTS)}"

    item = {
        "title": str(payload["title"]).strip(),
        "severity": severity,
        "service": str(payload["service"]).strip(),
        "description": str(payload["description"]).strip(),
        "reported_by": str(payload["reported_by"]).strip(),
        "environment": environment,
    }
    return item, None

def handle_create_incident(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    payload, err = _parse_json_body(event)
    if err:
        logger.info(json.dumps({"request_id": request_id, "msg": "validation_failed", "error": err}))
        return _response(400, {"error": err})

    item_fields, err = _validate_create(payload)
    if err:
        logger.info(json.dumps({"request_id": request_id, "msg": "validation_failed", "error": err}))
        return _response(400, {"error": err})

    created_at = _now_iso()
    incident_id = _new_incident_id(created_at)

    item = {
        "incident_id": incident_id,
        "created_at": created_at,
        "status": "OPEN",
        **item_fields,
    }

    try:
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(incident_id)")
        logger.info(json.dumps({"request_id": request_id, "msg": "incident_created", "incident_id": incident_id}))
        return _response(201, {"incident_id": incident_id, "created_at": created_at, "status": "OPEN"})
    except ClientError:
        logger.exception("DynamoDB put_item failed")
        raise  # IMPORTANT: allows CloudWatch Errors metric + alarm

def handle_get_incident(event: Dict[str, Any], request_id: str, incident_id: str) -> Dict[str, Any]:
    try:
        resp = table.get_item(Key={"incident_id": incident_id})
        item = resp.get("Item")
        if not item:
            return _response(404, {"error": "Incident not found.", "incident_id": incident_id})
        logger.info(json.dumps({"request_id": request_id, "msg": "incident_fetched", "incident_id": incident_id}))
        return _response(200, {"incident": item})
    except ClientError:
        logger.exception("DynamoDB get_item failed")
        raise

def handle_list_incidents(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    limit, err = _parse_limit(event, default=20)
    if err:
        return _response(400, {"error": err})

    service = _get_query_param(event, "service")
    try:
        if service:
            # Use GSI: service + created_at
            resp = table.query(
                IndexName=GSI_SERVICE_CREATEDAT,
                KeyConditionExpression=Key("service").eq(service),
                ScanIndexForward=False,  # newest first
                Limit=limit,
            )
            items = resp.get("Items", [])
            logger.info(json.dumps({"request_id": request_id, "msg": "incidents_queried_by_service", "service": service, "count": len(items)}))
            return _response(200, {"count": len(items), "incidents": items, "query": {"service": service}})
        else:
            # Fallback: scan
            resp = table.scan(Limit=limit)
            items = resp.get("Items", [])
            items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            logger.info(json.dumps({"request_id": request_id, "msg": "incidents_scanned", "count": len(items)}))
            return _response(200, {"count": len(items), "incidents": items})
    except ClientError:
        logger.exception("DynamoDB list/query failed")
        raise

def handle_patch_incident(event: Dict[str, Any], request_id: str, incident_id: str) -> Dict[str, Any]:
    payload, err = _parse_json_body(event)
    if err:
        return _response(400, {"error": err})

    new_status = payload.get("status")
    if not new_status or str(new_status).strip().upper() not in ALLOWED_STATUS:
        return _response(400, {"error": f"status is required and must be one of: {sorted(ALLOWED_STATUS)}"})

    new_status = str(new_status).strip().upper()
    updated_at = _now_iso()

    try:
        resp = table.update_item(
            Key={"incident_id": incident_id},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": new_status, ":u": updated_at},
            ConditionExpression="attribute_exists(incident_id)",
            ReturnValues="ALL_NEW",
        )
        item = resp.get("Attributes", {})
        logger.info(json.dumps({"request_id": request_id, "msg": "incident_updated", "incident_id": incident_id, "status": new_status}))
        return _response(200, {"incident": item})
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "ConditionalCheckFailedException":
            return _response(404, {"error": "Incident not found.", "incident_id": incident_id})
        logger.exception("DynamoDB update_item failed")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    request_id = _get_request_id(event)
    method, path = _get_method_path(event)

    logger.info(json.dumps({"request_id": request_id, "method": method, "path": path, "msg": "request_received"}))

    if method == "OPTIONS":
        return {"statusCode": 204, "headers": JSON_HEADERS, "body": ""}

    if not table:
        return _response(500, {"error": "Server misconfigured: TABLE_NAME not set."})

    # /incidents
    if path == "/incidents" and method == "POST":
        return handle_create_incident(event, request_id)
    if path == "/incidents" and method == "GET":
        return handle_list_incidents(event, request_id)

    # /incidents/{incident_id}
    if path.startswith("/incidents/"):
        incident_id = _get_path_param(event, "incident_id")
        if not incident_id:
            incident_id = path.split("/incidents/", 1)[-1].strip()

        if not incident_id:
            return _response(400, {"error": "incident_id is required in path."})

        if method == "GET":
            return handle_get_incident(event, request_id, incident_id)
        if method == "PATCH":
            return handle_patch_incident(event, request_id, incident_id)

    return _response(404, {"error": "Route not found.", "method": method, "path": path})