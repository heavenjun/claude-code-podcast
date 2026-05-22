"""Upload podcast MP3 to Google Drive using OAuth2 credentials."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import DRIVE_FOLDER_NAME

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _build_service(client_id: str, client_secret: str, refresh_token: str):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def _find_or_create_folder(service, name: str, parent_id: str | None) -> str:
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_podcast(
    mp3_path: str,
    subfolder_name: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> dict:
    """Upload mp3_path to Drive at Podcasts/{subfolder_name}/podcast.mp3."""
    service = _build_service(client_id, client_secret, refresh_token)

    root_id = _find_or_create_folder(service, DRIVE_FOLDER_NAME, parent_id=None)
    sub_id = _find_or_create_folder(service, subfolder_name, parent_id=root_id)

    file_metadata = {
        "name": os.path.basename(mp3_path),
        "parents": [sub_id],
    }
    media = MediaFileUpload(mp3_path, mimetype="audio/mpeg", resumable=True)
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink,name")
        .execute()
    )
    print(f"  Uploaded to Drive: {uploaded.get('webViewLink')}")
    return uploaded
