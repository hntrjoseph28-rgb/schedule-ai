import os
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# We only need read + write access to calendar events.
# If you change these scopes later, delete token.json so re-auth triggers.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Tokens are stored next to this file for simplicity.
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.json")

# Build the client config dict from env vars so we don't need a separate
# credentials.json file checked into the repo.
def _client_config() -> dict:
    return {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _get_credentials() -> Credentials:
    """
    Load credentials from token.json if they exist and are still valid.
    If the access token is expired, the library refreshes it automatically.
    If no token exists yet, run the browser-based OAuth flow.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
            # Opens a local browser tab; listens on a random available port.
            creds = flow.run_local_server(port=0)

        # Persist so the next call skips the browser flow.
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def _service():
    """Return an authenticated Google Calendar API service object."""
    return build("calendar", "v3", credentials=_get_credentials())


# ── Read ──────────────────────────────────────────────────────────────────────

def get_events(days_ahead: int = 7, calendar_id: str = "primary") -> list[dict]:
    """
    Return events from now through the next `days_ahead` days.
    Each dict has: id, summary, start, end, description, location.
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    result = (
        _service()
        .events()
        .list(
            calendarId=calendar_id,
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,          # expand recurring events into instances
            orderBy="startTime",
        )
        .execute()
    )

    events = []
    for item in result.get("items", []):
        start = item["start"].get("dateTime", item["start"].get("date"))
        end_val = item["end"].get("dateTime", item["end"].get("date"))
        events.append({
            "id": item["id"],
            "summary": item.get("summary", "(no title)"),
            "start": start,
            "end": end_val,
            "description": item.get("description", ""),
            "location": item.get("location", ""),
        })

    return events


# ── Create ────────────────────────────────────────────────────────────────────

def create_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
) -> dict:
    """
    Create a calendar event and return the created event dict.

    `start` and `end` should be ISO 8601 strings with timezone offset,
    e.g. "2026-06-20T14:00:00-06:00" for Mountain time.
    """
    body = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start, "timeZone": "America/Denver"},
        "end": {"dateTime": end, "timeZone": "America/Denver"},
    }

    created = _service().events().insert(calendarId=calendar_id, body=body).execute()
    return {
        "id": created["id"],
        "summary": created.get("summary"),
        "start": created["start"].get("dateTime"),
        "end": created["end"].get("dateTime"),
        "html_url": created.get("htmlLink"),
    }


# ── Update ────────────────────────────────────────────────────────────────────

def update_event(
    event_id: str,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str = "primary",
) -> dict:
    """
    Patch an existing event — only the fields you pass are changed.
    Uses PATCH (not PUT) so you don't have to send the full event body.
    """
    service = _service()

    # Fetch current state so we can fill in any fields not being updated.
    existing = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

    patch_body = {}
    if summary is not None:
        patch_body["summary"] = summary
    if description is not None:
        patch_body["description"] = description
    if location is not None:
        patch_body["location"] = location
    if start is not None:
        tz = existing["start"].get("timeZone", "America/Denver")
        patch_body["start"] = {"dateTime": start, "timeZone": tz}
    if end is not None:
        tz = existing["end"].get("timeZone", "America/Denver")
        patch_body["end"] = {"dateTime": end, "timeZone": tz}

    updated = (
        service.events()
        .patch(calendarId=calendar_id, eventId=event_id, body=patch_body)
        .execute()
    )
    return {
        "id": updated["id"],
        "summary": updated.get("summary"),
        "start": updated["start"].get("dateTime"),
        "end": updated["end"].get("dateTime"),
        "html_url": updated.get("htmlLink"),
    }


# ── Delete ────────────────────────────────────────────────────────────────────

def delete_event(event_id: str, calendar_id: str = "primary") -> None:
    """Delete an event by its ID. Raises an error if the event doesn't exist."""
    _service().events().delete(calendarId=calendar_id, eventId=event_id).execute()


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Upcoming Calendar Events (next 7 days) ===")
    events = get_events(days_ahead=7)
    if not events:
        print("  None found.")
    for e in events:
        print(f"  {e['start'][:16]}  {e['summary']}")
