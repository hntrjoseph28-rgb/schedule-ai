# ScheduleAI

An AI-powered scheduling assistant built for university students. It connects to your Canvas LMS and Google Calendar, letting you view upcoming assignments, manage events, and chat with an AI agent that can plan your week and create calendar events automatically.

## What it does

- **Assignments tab** — pulls upcoming assignments from Canvas across all active courses, filterable by how many days ahead to look
- **Calendar tab** — displays your Google Calendar events, lets you create events manually with a form, and delete existing ones
- **AI Assistant tab** — chat interface backed by a Claude agent that reads your Canvas assignments and calendar, suggests study blocks around your existing schedule, and creates events when you confirm

## How the agent works

The agent runs an agentic loop using Claude's tool use. When you send a message it:

1. Fetches your upcoming Canvas assignments to see what's due and when
2. Fetches your existing Google Calendar events to avoid double-booking
3. Suggests concrete study blocks with specific dates and times
4. Only creates calendar events once you've confirmed

The loop continues until Claude stops requesting tool calls, then returns the final response.

## Tech stack

- [Claude API](https://anthropic.com) — agent logic and tool use (claude-opus-4-8)
- [Google Calendar API](https://developers.google.com/calendar) — read, create, and delete events via OAuth 2.0
- [Canvas LMS API](https://canvas.instructure.com/doc/api/) — fetch upcoming assignments with pagination support
- [FastAPI](https://fastapi.tiangolo.com/) — REST API backend
- [Streamlit](https://streamlit.io/) — three-tab frontend (assignments, calendar, AI chat)
- Python 3.10+

## Project structure

```
schedule-ai/
├── backend/
│   ├── main.py        # FastAPI app — exposes all endpoints
│   ├── agent.py       # Claude agent, tool definitions, and agentic loop
│   ├── canvas.py      # Canvas API integration with pagination
│   └── gcalendar.py   # Google Calendar OAuth and CRUD operations
├── frontend/
│   └── app.py         # Streamlit UI — assignments, calendar, and chat tabs
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/hntrjoseph28-rgb/schedule-ai.git
cd schedule-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up API keys

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
CANVAS_API_KEY=your_canvas_api_key
CANVAS_BASE_URL=your_canvas_base_url
```

- **Anthropic key**: [console.anthropic.com](https://console.anthropic.com)
- **Google credentials**: [Google Cloud Console](https://console.cloud.google.com) — create a project, enable the Google Calendar API, and create an OAuth 2.0 Client ID (Desktop app type). Add your Google account as a test user under the OAuth consent screen.
- **Canvas key**: Canvas → profile picture → Settings → Approved Integrations → New Access Token

### 4. Run the backend

```bash
cd backend
python -m uvicorn main:app --reload
```

On first run, a browser tab will open for Google OAuth. After you approve access, credentials are cached in `token.json` (not committed to the repo).

### 5. Run the frontend

In a second terminal:

```bash
cd frontend
python -m streamlit run app.py
```

Open `http://localhost:8501`.

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | List active Canvas courses |
| GET | `/assignments?days_ahead=7` | Upcoming Canvas assignments |
| GET | `/events?days_ahead=7` | Google Calendar events |
| POST | `/events` | Create a calendar event |
| DELETE | `/events/{event_id}` | Delete a calendar event |
| POST | `/agent` | Send a message to the AI scheduling agent |
