import requests
import streamlit as st

API = "http://localhost:8000"

st.set_page_config(page_title="ScheduleAI", page_icon="📅", layout="wide")
st.title("📅 ScheduleAI")

assignments_tab, calendar_tab, agent_tab = st.tabs(
    ["Assignments", "Calendar", "AI Assistant"]
)


# ── Assignments ───────────────────────────────────────────────────────────────

with assignments_tab:
    days = st.slider("Days ahead", 1, 30, 7, key="assign_days")

    if st.button("Refresh", key="refresh_assign"):
        st.cache_data.clear()

    @st.cache_data(ttl=120)
    def fetch_assignments(days_ahead):
        try:
            r = requests.get(f"{API}/assignments", params={"days_ahead": days_ahead})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    data = fetch_assignments(days)

    if isinstance(data, dict) and "error" in data:
        st.error(f"Could not reach backend: {data['error']}")
        st.caption("Make sure `uvicorn main:app --reload` is running in the backend folder.")
    elif not data:
        st.info("No assignments due in the next {} days. 🎉".format(days))
    else:
        for a in data:
            due = a["due_at"][:16].replace("T", " ")
            with st.expander(f"**{a['name']}** — due {due}"):
                st.write(f"**Course:** {a['course_name']}")
                st.write(f"**Due:** {a['due_at']}")
                if a.get("html_url"):
                    st.markdown(f"[Open in Canvas]({a['html_url']})")


# ── Calendar ──────────────────────────────────────────────────────────────────

with calendar_tab:
    days_cal = st.slider("Days ahead", 1, 30, 7, key="cal_days")

    col_refresh, col_add = st.columns([1, 3])
    with col_refresh:
        if st.button("Refresh", key="refresh_cal"):
            st.cache_data.clear()

    @st.cache_data(ttl=120)
    def fetch_events(days_ahead):
        try:
            r = requests.get(f"{API}/events", params={"days_ahead": days_ahead})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    events = fetch_events(days_cal)

    if isinstance(events, dict) and "error" in events:
        st.error(f"Could not reach backend: {events['error']}")
    elif not events:
        st.info("No events in the next {} days.".format(days_cal))
    else:
        for e in events:
            start = e["start"][:16].replace("T", " ") if e.get("start") else "?"
            end = e["end"][11:16] if e.get("end") else "?"
            label = f"**{e['summary']}** — {start} → {end}"
            with st.expander(label):
                if e.get("description"):
                    st.write(e["description"])
                if st.button("Delete", key=f"del_{e['id']}"):
                    try:
                        requests.delete(f"{API}/events/{e['id']}")
                        st.success("Deleted.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))

    st.divider()
    st.subheader("Add event manually")

    with st.form("add_event"):
        summary = st.text_input("Title")
        col1, col2 = st.columns(2)
        start = col1.text_input("Start (ISO 8601)", placeholder="2026-06-20T14:00:00-06:00")
        end = col2.text_input("End (ISO 8601)", placeholder="2026-06-20T16:00:00-06:00")
        description = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Create event")
        if submitted:
            if not summary or not start or not end:
                st.warning("Title, start, and end are required.")
            else:
                try:
                    r = requests.post(
                        f"{API}/events",
                        json={"summary": summary, "start": start, "end": end, "description": description},
                    )
                    r.raise_for_status()
                    st.success(f"Created: {r.json()['summary']}")
                    st.cache_data.clear()
                except Exception as ex:
                    st.error(str(ex))


# ── AI Assistant ──────────────────────────────────────────────────────────────

with agent_tab:
    st.caption(
        "Ask the AI to plan your week, suggest study blocks, or create calendar events. "
        "It reads your Canvas assignments and Google Calendar automatically."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("e.g. Schedule study time for my upcoming assignments")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    r = requests.post(
                        f"{API}/agent",
                        json={"message": user_input},
                        timeout=120,  # agent can take a while
                    )
                    r.raise_for_status()
                    reply = r.json()["reply"]
                except Exception as ex:
                    reply = f"Error reaching backend: {ex}"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.session_state.messages:
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()
