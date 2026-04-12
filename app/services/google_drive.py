"""
Google Drive upload service — uses OAuth2 user credentials (Desktop app flow).

Run authorize_gdrive.py once locally to generate gdrive_token.json.
The token auto-refreshes — no repeat authorization needed.

Environment variables:
  GDRIVE_TOKEN_PATH   - path to gdrive_token.json (default: /app/gdrive_token.json)
  GDRIVE_CLIENT_PATH  - path to drive_oauth_client.json (default: /app/drive_oauth_client.json)
  GDRIVE_FOLDER_NAME  - Drive folder name (default: AstroNova PDFs)
  GDRIVE_FOLDER_ID    - Drive folder ID, overrides GDRIVE_FOLDER_NAME
"""

import logging
import os
import json
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
_TOKEN_PATH = os.getenv("GDRIVE_TOKEN_PATH", "/app/gdrive_token.json")
_CLIENT_PATH = os.getenv("GDRIVE_CLIENT_PATH", "/app/drive_oauth_client.json")
_FOLDER_NAME = os.getenv("GDRIVE_FOLDER_NAME", "AstroNova PDFs")


def _resolve_file_path(env_json_key: str, file_path: str) -> str:
    """
    Returns a path to the credential file.
    If the env var <env_json_key> contains raw JSON, writes it to a temp file and returns that path.
    Otherwise falls back to file_path.
    """
    raw = os.getenv(env_json_key)
    if raw:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(raw)
        tmp.flush()
        return tmp.name
    return file_path


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_path = _resolve_file_path("GDRIVE_TOKEN_JSON", _TOKEN_PATH)

    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"Google Drive token not found at {token_path}. "
            "Run authorize_gdrive.py once to authorize access."
        )

    creds = Credentials.from_authorized_user_file(token_path, _SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Write back refreshed token — to the original path if it's a real file
        original_path = _TOKEN_PATH if not os.getenv("GDRIVE_TOKEN_JSON") else token_path
        Path(original_path).write_text(creds.to_json())
    return creds


def _get_or_create_folder(service, folder_name: str) -> str:
    folder_id_env = os.getenv("GDRIVE_FOLDER_ID")
    if folder_id_env:
        return folder_id_env

    query = (
        f"name = '{folder_name}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    items = results.get("files", [])
    if items:
        return items[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_pdf(local_path: str, filename: str) -> tuple[str, str]:
    """
    Upload *local_path* to Google Drive inside the configured folder.

    Sets the file permission to "anyone with the link can view".

    Returns a (drive_file_id, web_view_link) tuple on success, raises on failure.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    folder_id = _get_or_create_folder(service, _FOLDER_NAME)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=False)

    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )

    drive_file_id = uploaded.get("id")

    # Make the file accessible to anyone with the link
    service.permissions().create(
        fileId=drive_file_id,
        body={"type": "anyone", "role": "reader"},
        fields="id",
    ).execute()

    file_info = service.files().get(fileId=drive_file_id, fields="webViewLink").execute()
    web_link = file_info.get("webViewLink", f"https://drive.google.com/file/d/{drive_file_id}/view")

    logger.info("PDF uploaded to Google Drive: id=%s link=%s", drive_file_id, web_link)
    return drive_file_id, web_link

