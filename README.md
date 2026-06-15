# ScheduleAI
 
An AI-powered scheduling assistant that connects to your Google Calendar and Canvas LMS. Chat with it to create and manage events, or add them manually through the interface.
 
## What it does
 
- Reads your existing Google Calendar events and Canvas assignments in one place
- Creates calendar events from natural language ("block 2 hours for my CS homework Thursday afternoon")
- Lets you manually add, edit, or delete events if the AI gets something wrong
- Keeps a running view of your week so you can see what's scheduled at a glance
## Tech stack
 
- [Claude](https://anthropic.com) — conversational AI and scheduling logic
- [Google Calendar API](https://developers.google.com/calendar) — read and write calendar events
- [Canvas LMS API](https://canvas.instructure.com/doc/api/) — pull assignment due dates
- [Streamlit](https://streamlit.io/) — chat interface and calendar view
- [FastAPI](https://fastapi.tiangolo.com/) — backend API
- Python 3.10+
## Project structure
 
```
schedule-ai/
├── backend/
│   ├── main.py          # FastAPI backend
│   ├── calendar.py      # Google Calendar integration
│   ├── canvas.py        # Canvas LMS integration
│   └── agent.py         # Claude agent and tool definitions
├── frontend/
│   └── app.py           # Streamlit chat and calendar UI
├── .env.example         # Required API keys
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
pip install anthropic fastapi uvicorn streamlit google-auth google-auth-oauthlib google-api-python-client python-dotenv requests
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
 
- Anthropic key: [console.anthropic.com](https://console.anthropic.com)
- Google credentials: [Google Cloud Console](https://console.cloud.google.com) — enable the Calendar API and create OAuth 2.0 credentials
- Canvas key: BYU-I Canvas → Account → Settings → New Access Token
### 4. Run the backend
 
```bash
cd backend
python -m uvicorn main:app --reload
```
 
### 5. Run the frontend
 
```bash
cd frontend
python -m streamlit run app.py
```
 
Open `http://localhost:8501` in your browser.
 
## How it works
 
1. On startup, the app pulls your Canvas assignments and Google Calendar events for the current week
2. You chat with the assistant in plain English about your schedule
3. The assistant uses Claude's tool use to create, read, or update calendar events based on your input
4. You can also manually add or edit events directly in the UI without going through the chat
## API endpoints
 
| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/events` | Fetch calendar events for a date range |
| POST | `/events` | Create a new calendar event |
| PUT | `/events/{id}` | Update an existing event |
| DELETE | `/events/{id}` | Delete an event |
| GET | `/assignments` | Fetch upcoming Canvas assignments |
| POST | `/chat` | Send a message to the scheduling assistant |
 
## Status
 
In development.