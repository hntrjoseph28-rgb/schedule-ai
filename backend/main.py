from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import run as agent_run
from canvas import get_courses, get_upcoming_assignments
from gcalendar import create_event, delete_event, get_events

app = FastAPI(title="ScheduleAI")

# Allow the Streamlit frontend (running on a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Canvas ────────────────────────────────────────────────────────────────────

@app.get("/courses")
def list_courses():
    """Return all active Canvas courses."""
    return get_courses()


@app.get("/assignments")
def list_assignments(days_ahead: int = 7):
    """Return assignments due within the next `days_ahead` days."""
    return get_upcoming_assignments(days_ahead=days_ahead)


# ── Google Calendar ───────────────────────────────────────────────────────────

@app.get("/events")
def list_events(days_ahead: int = 7):
    """Return Google Calendar events for the next `days_ahead` days."""
    return get_events(days_ahead=days_ahead)


class EventCreate(BaseModel):
    summary: str
    start: str        # ISO 8601 with offset, e.g. "2026-06-20T14:00:00-06:00"
    end: str
    description: str = ""
    location: str = ""


@app.post("/events", status_code=201)
def add_event(body: EventCreate):
    """Create a new Google Calendar event."""
    return create_event(
        summary=body.summary,
        start=body.start,
        end=body.end,
        description=body.description,
        location=body.location,
    )


@app.delete("/events/{event_id}", status_code=204)
def remove_event(event_id: str):
    """Delete a Google Calendar event by its ID."""
    try:
        delete_event(event_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── AI Agent ──────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    message: str


@app.post("/agent")
def ask_agent(body: AgentRequest):
    """Send a message to the AI scheduling agent and get a response."""
    reply = agent_run(body.message)
    return {"reply": reply}
