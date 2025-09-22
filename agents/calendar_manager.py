# agents/calendar_manager.py
from __future__ import print_function
import datetime
import os.path
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets_file.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def create_event(summary, start_time, duration=1):
    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)

    start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    end_dt = start_dt + datetime.timedelta(hours=duration)

    event = {
        "summary": summary,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: {event.get('htmlLink')}"

import dateparser
import dateparser.search
import re
import datetime

def parse_command(command):
    # Remove scheduling keywords for summary
    cleaned = re.sub(r"\b(schedule|meeting|about)\b", "", command, flags=re.IGNORECASE).strip()

    # --- Duration extraction ---
    duration_hours = 1
    duration_match = re.search(r"for (\d+)\s*(hour|hours|hr|hrs|minute|minutes|min|mins)", command, re.IGNORECASE)
    if duration_match:
        value = int(duration_match.group(1))
        unit = duration_match.group(2).lower()
        if "min" in unit:
            duration_hours = value / 60
        else:
            duration_hours = value

    # --- Custom handling for "next <weekday>" ---
    match = re.search(r"\bnext (\w+day)\b", cleaned, re.IGNORECASE)
    if match:
        weekday_str = match.group(1).lower()
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if weekday_str in weekdays:
            today = datetime.datetime.now()
            today_weekday = today.weekday()
            target_weekday = weekdays.index(weekday_str)
            days_ahead = (target_weekday - today_weekday + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_weekday_date = today + datetime.timedelta(days=days_ahead)
            cleaned = re.sub(r"\bnext \w+day\b", next_weekday_date.strftime("%Y-%m-%d"), cleaned, flags=re.IGNORECASE)

            time_match = re.search(r"at\s+([0-9]{1,2}(?::[0-9]{2})?\s*(am|pm)?)", cleaned, re.IGNORECASE)
            if time_match:
                time_str = time_match.group(1)
                # Build a full datetime string
                datetime_str = f"{next_weekday_date.strftime('%Y-%m-%d')} {time_str}"
                dt = dateparser.parse(datetime_str)
                summary = re.sub(r"\b202\d{1}-\d{2}-\d{2}\b", "", cleaned)
                summary = re.sub(r"at\s+[0-9]{1,2}(?::[0-9]{2})?\s*(am|pm)?", "", summary, flags=re.IGNORECASE).strip().title()
                if not summary:
                    summary = "General Event"
                if dt:
                    start_time = dt.strftime("%Y-%m-%d %H:%M")
                    return summary, start_time, duration_hours
            # If no time, just use the date
            dt = dateparser.parse(next_weekday_date.strftime('%Y-%m-%d'))
            summary = re.sub(r"\b202\d{1}-\d{2}-\d{2}\b", "", cleaned).strip().title()
            if not summary:
                summary = "General Event"
            if dt:
                start_time = dt.strftime("%Y-%m-%d %H:%M")
                return summary, start_time, duration_hours


    # --- Fallback: Use search_dates ---
    results = dateparser.search.search_dates(
        cleaned,
        settings={
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": False
        }
    )

    if results:
        time_phrase, dt = results[0]
        summary = cleaned.replace(time_phrase, "").strip().title()
        if not summary:
            summary = "General Event"
        start_time = dt.strftime("%Y-%m-%d %H:%M")
        return summary, start_time, duration_hours
    else:
        return None, None, None

def list_upcoming_events(max_results=5):
    creds = authenticate()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' means UTC
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])

    if not events:
        return ["No upcoming events found."]

    event_list = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        event_list.append(f"{start} - {event['summary']}")
    return event_list
