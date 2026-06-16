import os
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL", "https://byui.instructure.com")
CANVAS_API_KEY = os.getenv("CANVAS_API_KEY")

EXCLUDED_COURSE_IDS = {48558}

def _headers() -> dict:
    """Build the auth header Canvas expects on every request."""
    return {"Authorization": f"Bearer {CANVAS_API_KEY}"}


def _get_all_pages(url: str, params: dict | None = None) -> list:
    """
    Canvas paginates results — each response may contain a Link header
    pointing to the next page. This helper follows those links until
    there are no more pages and returns all items combined.
    """
    results = []
    while url:
        response = requests.get(url, headers=_headers(), params=params)
        response.raise_for_status()
        results.extend(response.json())

        # Canvas signals the next page via a Link header like:
        # <https://...?page=2>; rel="next"
        next_url = None
        link_header = response.headers.get("Link", "")
        for part in link_header.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
                break
        url = next_url
        params = None  # params are already encoded in the next URL

    return results


def get_courses() -> list[dict]:
    """
    Return active courses for the current user, excluding any course IDs
    in EXCLUDED_COURSE_IDS (e.g. the BYU-I events pseudo-course).
    """
    url = f"{CANVAS_BASE_URL}/api/v1/courses"
    params = {
        "enrollment_state": "active",
        "per_page": 50,
    }
    courses = _get_all_pages(url, params)
    return [c for c in courses if c.get("id") not in EXCLUDED_COURSE_IDS]


def get_upcoming_assignments(days_ahead: int = 7) -> list[dict]:
    """
    Fetch assignments due within the next `days_ahead` days across all
    active (non-excluded) courses. Returns a sorted list of dicts with
    the keys: id, name, course_name, due_at, html_url.
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    courses = get_courses()

    upcoming = []
    for course in courses:
        course_id = course["id"]
        course_name = course.get("name", f"Course {course_id}")

        url = f"{CANVAS_BASE_URL}/api/v1/courses/{course_id}/assignments"
        params = {
            "bucket": "upcoming",
            "per_page": 50,
            "order_by": "due_at",
        }
        assignments = _get_all_pages(url, params)

        for a in assignments:
            due_str = a.get("due_at")
            if not due_str:
                continue
            due_dt = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
            if now <= due_dt <= end:
                upcoming.append({
                    "id": a["id"],
                    "name": a["name"],
                    "course_name": course_name,
                    "due_at": due_str,
                    "html_url": a.get("html_url", ""),
                })

    upcoming.sort(key=lambda a: a["due_at"])
    return upcoming


if __name__ == "__main__":
    print("=== Active Courses ===")
    for course in get_courses():
        print(f"  [{course['id']}] {course.get('name', 'Unnamed')}")

    print("\n=== Upcoming Assignments (next 7 days) ===")
    assignments = get_upcoming_assignments()
    if not assignments:
        print("  None found.")
    for a in assignments:
        print(f"  {a['due_at'][:10]}  {a['course_name']} — {a['name']}")
        print(f"           {a['html_url']}")
