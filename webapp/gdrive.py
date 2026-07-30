"""Google Drive access for the webapp.

Credential lookup order (all paths relative to repo root, all git-ignored):
  1. credentials/service-account.json  — a service account with the
     JobApplications folder shared to it (simplest headless option).
  2. credentials/oauth-client.json     — an OAuth "Desktop app" client from the
     same Google Cloud project as the n8n Drive connection (docs/n8n-setup.md);
     first use opens a browser consent flow, token cached in
     credentials/token.json.

Raises DriveError with an actionable message when neither is present.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED_DIR = ROOT / "credentials"
SERVICE_ACCOUNT = CRED_DIR / "service-account.json"
OAUTH_CLIENT = CRED_DIR / "oauth-client.json"
TOKEN_CACHE = CRED_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/drive"]

_service = None


class DriveError(Exception):
    pass


def _build_service():
    from googleapiclient.discovery import build

    if SERVICE_ACCOUNT.exists():
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT), scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)

    if OAUTH_CLIENT.exists():
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        if TOKEN_CACHE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_CACHE), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT), SCOPES)
                creds = flow.run_local_server(port=0)
            TOKEN_CACHE.write_text(creds.to_json(), encoding="utf-8")
        return build("drive", "v3", credentials=creds)

    raise DriveError(
        "No Google Drive credentials found. Put either credentials/service-account.json "
        "(service account with the JobApplications folder shared to it) or "
        "credentials/oauth-client.json (OAuth Desktop-app client) in place — "
        "see docs/n8n-setup.md and webapp/README.md."
    )


def service():
    global _service
    if _service is None:
        _service = _build_service()
    return _service


def list_scrape_files(folder_id: str) -> list[dict]:
    """jobs-YYYY-MM-DD.json files in the folder, newest first."""
    resp = service().files().list(
        q=f"'{folder_id}' in parents and trashed = false and name contains 'jobs-'",
        fields="files(id, name, modifiedTime, size)",
        orderBy="name desc",
        pageSize=100,
    ).execute()
    return [f for f in resp.get("files", []) if re.match(r"jobs-\d{4}-\d{2}-\d{2}\.json$", f["name"])]


def download_json(file_id: str):
    from googleapiclient.http import MediaIoBaseDownload

    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, service().files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return json.loads(buf.getvalue().decode("utf-8"))


def find_child(folder_id: str, name: str) -> dict | None:
    safe = name.replace("'", "\\'")
    resp = service().files().list(
        q=f"'{folder_id}' in parents and trashed = false and name = '{safe}'",
        fields="files(id, name, mimeType)",
        pageSize=1,
    ).execute()
    files = resp.get("files", [])
    return files[0] if files else None


def ensure_subfolder(parent_id: str, name: str) -> str:
    existing = find_child(parent_id, name)
    if existing:
        return existing["id"]
    created = service().files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id",
    ).execute()
    return created["id"]


def upload_bytes(parent_id: str, name: str, data: bytes, mime_type: str,
                 convert_to_gdoc: bool = False) -> str:
    """Create or overwrite `name` inside `parent_id`. Returns the file id."""
    from googleapiclient.http import MediaIoBaseUpload

    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime_type, resumable=False)
    existing = find_child(parent_id, name)
    if existing:
        service().files().update(fileId=existing["id"], media_body=media).execute()
        return existing["id"]
    body: dict = {"name": name, "parents": [parent_id]}
    if convert_to_gdoc:
        body["mimeType"] = "application/vnd.google-apps.document"
    created = service().files().create(body=body, media_body=media, fields="id").execute()
    return created["id"]


def download_bytes(file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload

    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, service().files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()
