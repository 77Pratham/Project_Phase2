import dateparser
import datetime
import re

def extract_datetime(command: str):
    """
    Extract datetime and optional duration from natural text.
    Handles:
      - 'next monday at 4 pm'
      - 'tomorrow 7am'
      - 'friday 10:30'
      - 'next wednesday 3pm for 2 hours'
    Returns (datetime_obj, duration_hours)
    """
    command = command.lower().strip()
    duration_hours = 1  # default

    # --- Duration extraction ---
    duration_match = re.search(r"for (\d+)\s*(hour|hours|hr|hrs|minute|minutes|min|mins)", command)
    if duration_match:
        value = int(duration_match.group(1))
        unit = duration_match.group(2).lower()
        if "min" in unit:
            duration_hours = value / 60
        else:
            duration_hours = value

    # --- Handle 'next <weekday>' manually ---
    match = re.search(r"\bnext (\w+day)\b", command)
    if match:
        weekday_str = match.group(1).lower()
        weekdays = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
        if weekday_str in weekdays:
            today = datetime.datetime.now()
            today_weekday = today.weekday()
            target_weekday = weekdays.index(weekday_str)
            days_ahead = (target_weekday - today_weekday + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_date = today + datetime.timedelta(days=days_ahead)

            # Look for a time part
            time_match = re.search(r"(\d{1,2}(:\d{2})?\s*(am|pm)?)", command)
            if time_match:
                time_str = time_match.group(1)
                dt = dateparser.parse(f"{next_date.strftime('%Y-%m-%d')} {time_str}")
                return dt, duration_hours
            return next_date, duration_hours

    # --- Fallback to dateparser ---
    dt = dateparser.parse(command, settings={"PREFER_DATES_FROM": "future"})
    return dt, duration_hours if dt else (None, None)
