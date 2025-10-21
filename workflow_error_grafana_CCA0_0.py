#workflow_error_grafana_CCA0_0
import os
import json
import time
import requests

LOKI_URL = os.getenv("LOKI_URL") or os.getenv("grafana_url") or "https://<your-stack>.grafana.net/loki/api/v1/push"
GRAFANA_USER = os.getenv("grafana_user")
GRAFANA_TOKEN = os.getenv("grafana_token")

STREAM_LABELS = {
    "service_name": "hubspot",
    "environment": "prod",
    "process": "workflow",
    "team": "marketing_technology",
    "job": "swoogo_visitor_id",
}

def mask_email(addr: str) -> str:
    if not addr or "@" not in addr:
        return "***"
    local, domain = addr.split("@", 1)
    if len(local) == 0:
        masked_local = "***"
    elif len(local) == 1:
        masked_local = f"{local[0]}***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"

def push_success_log(event_id: str, email: str, event_slug: str) -> int:
    if not LOKI_URL:
        raise RuntimeError("Missing LOKI_URL (or grafana_url) in Secrets.")
    if not GRAFANA_USER or not GRAFANA_TOKEN:
        raise RuntimeError("Missing grafana_user and/or grafana_token in Secrets.")

    # 1) log line (free-form JSON you can parse with `| json` if you want)
    event = {
        "level": "info",
        "action": "cca0",
        "message": "success swoogo visitor id via hutk",
        "event_id": str(event_id or ""),
        "event_slug": str(event_slug or ""),
        "masked_email": mask_email(email or ""),
    }

    # 2) structured metadata (flat strings only; used for fast filtering)
    meta = {
        "level": "info",
        "action": "cca0",
        "event_id": str(event_id or ""),
        "event_slug": str(event_slug or ""),
        # keep PII like email only in the line, not metadata
    }

    ts_ns = str(time.time_ns())
    line = json.dumps(event, separators=(",", ":"))

    payload = {
        "streams": [
            {
                "stream": STREAM_LABELS,
                # values entry: [timestamp, line, structured_metadata]
                "values": [[ts_ns, line, meta]],
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    resp = requests.post(
        LOKI_URL,
        headers=headers,
        auth=(GRAFANA_USER, GRAFANA_TOKEN),
        data=json.dumps(payload),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.status_code  # typically 204

def main(event):
    inputs = (event.get("inputFields") or {})
    event_id = inputs.get("event_id", "")
    email = inputs.get("Email", "")
    event_slug = inputs.get("event_slug", "")

    try:
        http_status = push_success_log(event_id, email, event_slug)
        return {
            "outputFields": {
                "error_state": 0,
                "error_message": "",
                "status": int(http_status),
            }
        }
    except Exception as e:
        return {
            "outputFields": {
                "error_state": 1,
                "error_message": f"grafana push failed: {e}",
                "status": 0,
            }
        }