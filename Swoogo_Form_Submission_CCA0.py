#CCA0 - Perform visitor identification using data from a Swoogo form completion.
import os
import time
from typing import Optional
import requests

#This form requires the followin inputs to be defined.
#portal_id as your portal ID
#email as email address from the contact record. The main email of the contact record. It might not be the one they registered withg.
#swoogo_utk as swoogo_utk from the contact record. This is the hubspot_utk value capured during registration.
#swoogo_slug as swoogo_slug from the contact record. This is the page slug where they registered.

FORMS_FORM_GUID = "1ac4bcc4-0370-4713-a2d7-1fca322fd840"
BASE_DOMAIN = "https://nanoporetech.swoogo.com"

def _normalize_slug(slug: str) -> str:
    """
    Expected slug comes WITHOUT a leading '/', and we must strip any query strings.
    We also trim whitespace just in case.
    """
    slug = (slug or "").strip()
    if slug.startswith("/"):
        slug = slug[1:]
    if "?" in slug:
        slug = slug.split("?", 1)[0]
    return slug

def _build_page_url(slug: str) -> str:
    slug = _normalize_slug(slug)
    return f"{BASE_DOMAIN}/{slug}" if slug else BASE_DOMAIN

def _fail(message: str, submission_status: str = "", submission_id: str = "", page_url: str = ""):
    return {
        "outputFields": {
            "error_state": 1,
            "error_message": message[:2000],
            "submission_status": submission_status,
            "submission_id": submission_id,
            "page_url": page_url,
        }
    }

def _success(message: str, submission_status: str, submission_id: str, page_url: str):
    return {
        "outputFields": {
            "error_state": 0,
            "error_message": message[:2000],
            "submission_status": submission_status,
            "submission_id": submission_id,
            "page_url": page_url,
        }
    }

def _post_with_retry(url: str, headers: dict, payload: dict, timeout: int = 8) -> requests.Response:
    """
    One quick retry on 5xx/429 within HubSpot's 20s execution window.
    """
    session = requests.Session()
    attempt = 0
    last_exc: Optional[Exception] = None
    while attempt < 2:
        try:
            resp = session.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code >= 500 or resp.status_code == 429:
                time.sleep(0.5 if attempt == 0 else 1.0)
                attempt += 1
                continue
            return resp
        except requests.RequestException as e:
            last_exc = e
            time.sleep(0.5 if attempt == 0 else 1.0)
            attempt += 1
    if last_exc:
        raise last_exc
    raise RuntimeError("Unexpected error without exception or response during form submission.")

def main(event):
    """
    Inputs (set in the right sidebar):
      - email (string)
      - swoogo_slug (string) e.g. "nanopore-community-meeting" (no leading '/', no query)
      - swoogo_utk (string) hubspotutk cookie value

    Secret:
      - HubSpot_Custom_Code_Forms (Private App token)
      - portal_id (HubSpot Forms portal ID)
    """
    inputs = event.get("inputFields", {}) or {}
    email = (inputs.get("email") or "").strip()
    swoogo_slug = (inputs.get("swoogo_slug") or "").strip()
    swoogo_utk = (inputs.get("swoogo_utk") or "").strip()

    page_url = _build_page_url(swoogo_slug)

    # Minimal validation per requirements (no regex)
    if not email:
        return _fail("Validation error: 'email' is required but missing.", page_url=page_url)
    if "@" not in email:
        return _fail(f"Validation error: 'email' doesn't look valid: {email}", page_url=page_url)
    if not swoogo_utk:
        return _fail("Validation error: 'swoogo_utk' (hubspotutk) is required but missing.", page_url=page_url)

    token = os.getenv("HubSpot_Custom_Code_Forms")
    if not token:
        return _fail("Configuration error: Missing Private App token 'HubSpot_Custom_Code_Forms' in Secrets.",
                     page_url=page_url)

    portal_id = os.getenv("portal_id")
    if not portal_id:
        return _fail("Configuration error: Missing 'portal_id' in Secrets.", page_url=page_url)

    forms_endpoint = (
        f"https://api.hsforms.com/submissions/v3/integration/secure/submit/"
        f"{portal_id}/{FORMS_FORM_GUID}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, */*;q=0.8",
    }

    payload = {
        "fields": [
            {"name": "email", "value": email},
            {"name": "swoogo_utk", "value": swoogo_utk},
        ],
        "context": {
            "hutk": swoogo_utk,
            "pageUri": page_url,
            "pageName": _normalize_slug(swoogo_slug) or "swoogo",
        },
    }

    try:
        resp = _post_with_retry(forms_endpoint, headers, payload, timeout=8)
    except Exception as e:
        return _fail(f"Network error while submitting form: {e}", page_url=page_url)

    submission_status = ""
    submission_id = ""
    resp_text = resp.text or ""

    # Try to parse JSON if present
    resp_json = None
    if resp_text:
        try:
            resp_json = resp.json()
        except ValueError:
            resp_json = None

    if 200 <= resp.status_code < 300:
        if isinstance(resp_json, dict):
            submission_status = (
                resp_json.get("inlineMessage")
                or resp_json.get("message")
                or f"Success ({resp.status_code})"
            )
            submission_id = resp_json.get("submissionId") or resp_json.get("guid") or ""
        else:
            submission_status = f"Success ({resp.status_code})"
        return _success(
            message="Form submission succeeded.",
            submission_status=submission_status,
            submission_id=submission_id,
            page_url=page_url,
        )

    # Non-2xx: craft a helpful error
    detail = ""
    if isinstance(resp_json, dict):
        parts = []
        if resp_json.get("status"): parts.append(f"status={resp_json.get('status')}")
        if resp_json.get("message"): parts.append(f"message={resp_json.get('message')}")
        if resp_json.get("errors"): parts.append(f"errors={resp_json.get('errors')}")
        if resp_json.get("correlationId"): parts.append(f"correlationId={resp_json.get('correlationId')}")
        detail = "; ".join(parts)
    elif resp_text:
        detail = resp_text[:500]

    return _fail(
        message=f"HubSpot Forms submission failed with HTTP {resp.status_code}. {detail or 'No body returned.'}",
        submission_status=f"HTTP {resp.status_code}",
        submission_id="",
        page_url=page_url,
    )
