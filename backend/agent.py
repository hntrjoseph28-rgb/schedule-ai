import json
import os

import anthropic
from dotenv import load_dotenv

from canvas import get_upcoming_assignments
from gcalendar import create_event, get_events

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

client = anthropic.Anthropic()
MODEL = "claude-opus-4-8"

# ── Tool definitions ──────────────────────────────────────────────────────────
# Each dict tells Claude what the tool does and what arguments it accepts.
# Claude decides *when* to call them; we decide *how* to execute them below.

TOOLS = [
    {
        "name": "get_upcoming_assignments",
        "description": (
            "Fetch assignments due within the next N days from Canvas. "
            "Call this to see what academic work is coming up before suggesting a schedule."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "How many days ahead to look. Defaults to 7.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_calendar_events",
        "description": (
            "Fetch events from Google Calendar within the next N days. "
            "Call this to see what time is already blocked before creating new events."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "How many days ahead to look. Defaults to 7.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "create_calendar_event",
        "description": (
            "Create a new event on Google Calendar. "
            "Use this to block study time or set a reminder for an assignment. "
            "Only create events the user has confirmed or explicitly asked for."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Event title, e.g. 'Study: CS 101 Homework'",
                },
                "start": {
                    "type": "string",
                    "description": (
                        "Start time in ISO 8601 with Mountain Time offset, "
                        "e.g. '2026-06-20T14:00:00-06:00'"
                    ),
                },
                "end": {
                    "type": "string",
                    "description": "End time in the same ISO 8601 format.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional notes, e.g. the Canvas assignment URL.",
                },
            },
            "required": ["summary", "start", "end"],
        },
    },
]


# ── Tool execution ────────────────────────────────────────────────────────────
# This is the bridge between Claude's tool requests and our Python functions.

def execute_tool(name: str, tool_input: dict) -> str:
    if name == "get_upcoming_assignments":
        days = tool_input.get("days_ahead", 7)
        assignments = get_upcoming_assignments(days_ahead=days)
        if not assignments:
            return "No upcoming assignments found in the next {} days.".format(days)
        return json.dumps(assignments, indent=2)

    if name == "get_calendar_events":
        days = tool_input.get("days_ahead", 7)
        events = get_events(days_ahead=days)
        if not events:
            return "No calendar events found in the next {} days.".format(days)
        return json.dumps(events, indent=2)

    if name == "create_calendar_event":
        result = create_event(
            summary=tool_input["summary"],
            start=tool_input["start"],
            end=tool_input["end"],
            description=tool_input.get("description", ""),
        )
        return json.dumps(result, indent=2)

    return f"Unknown tool: {name}"


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM = """You are a scheduling assistant for a university student.
You have access to their Canvas LMS (to see upcoming assignments) and
their Google Calendar (to view and create events).

When the user asks you to help plan their week:
1. Fetch upcoming assignments so you know what's due and when.
2. Fetch existing calendar events so you don't double-book.
3. Suggest specific study blocks that fit around their existing schedule.
4. Only create calendar events when the user has agreed or explicitly asked.

Use Mountain Time (America/Denver). In summer that is UTC-6, so the offset
is -06:00. Keep study sessions to 1-2 hours; suggest short breaks between them.
Be concrete — give actual dates and times, not vague suggestions."""


# ── Agentic loop ──────────────────────────────────────────────────────────────
# The loop runs until Claude stops requesting tool calls (stop_reason == "end_turn").
# Each iteration:
#   1. Send the conversation to Claude.
#   2. If Claude wants tools → execute them and send results back.
#   3. If Claude is done → return its final text reply.

def run(user_message: str) -> str:
    """Run a single-turn agent conversation and return the final text response."""
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            thinking={"type": "adaptive"},  # let Claude think when it needs to
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        # Always append the full assistant response — tool_use blocks must be
        # preserved in the history so the next turn is valid.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Claude is done — extract and return the text reply.
            return next(
                (block.text for block in response.content if block.type == "text"),
                "(no text response)",
            )

        # Claude wants to call one or more tools — execute each one.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [tool] {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,  # must match the tool_use block's id
                    "content": result,
                })

        # Feed all tool results back to Claude in one user message.
        messages.append({"role": "user", "content": tool_results})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Schedule AI — ask me to help plan your week.")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Bye!")
            break

        print("\nAssistant:", flush=True)
        reply = run(user_input)
        print(reply, "\n")
