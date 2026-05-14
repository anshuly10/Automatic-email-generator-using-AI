# drive.py
# Search and download files from Google Drive

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
import io

# Google Workspace MIME types → export format
EXPORT_MAP = {
    "application/vnd.google-apps.document": "application/pdf",
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    "application/vnd.google-apps.presentation": "application/pdf",
}


def find_file(creds: Credentials, file_path_or_name: str) -> dict | None:
    """
    Search Google Drive for a file by name or path fragment.
    Returns a dict with id, name, mimeType or None if not found.
    """
    service = build("drive", "v3", credentials=creds)

    # Use just the filename part if a path is given (e.g. "Reports/Q3.pdf" → "Q3.pdf")
    file_name = file_path_or_name.split("/")[-1].strip()
    safe_name = file_name.replace("'", "\\'")

    results = (
        service.files()
        .list(
            q=f"name contains '{safe_name}' and trashed = false",
            fields="files(id, name, mimeType, size)",
            orderBy="modifiedTime desc",
            pageSize=10,
        )
        .execute()
    )

    files = results.get("files", [])
    if not files:
        return None

    # Prefer exact name match
    exact = next((f for f in files if f["name"].lower() == file_name.lower()), None)
    return exact or files[0]


def download_file(creds: Credentials, file_id: str, mime_type: str) -> tuple[bytes, str]:
    """
    Download a file from Google Drive.
    Google Workspace files (Docs/Sheets/Slides) are exported as PDF/XLSX.
    Returns (file_bytes, actual_mime_type).
    """
    service = build("drive", "v3", credentials=creds)
    export_mime = EXPORT_MAP.get(mime_type)
    buffer = io.BytesIO()

    if export_mime:
        # Google Workspace file → export
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        actual_mime = export_mime
    else:
        # Regular file → download directly
        request = service.files().get_media(fileId=file_id)
        actual_mime = mime_type

    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue(), actual_mime
