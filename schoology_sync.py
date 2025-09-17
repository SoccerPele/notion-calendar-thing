import datetime
import requests
from icalendar import Calendar
from flask import Flask, Response

# --- CONFIG ---
ICAL_URL = "webcal://app.schoology.com/calendar/feed/ical/1757944813/6f50e1c805b1488d409a0f964303e759/ical.ics"
CUTOFF_DATE = datetime.date(2025, 9, 1)
OFFSET_HOURS = -4  # shift back 4 hours

app = Flask(__name__)

def generate_filtered_calendar():
    # download feed
    resp = requests.get(ICAL_URL)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)

    # create new calendar
    new_cal = Calendar()
    for prop in cal.property_items():
        new_cal.add(prop[0], prop[1])

    # filter + adjust
    for component in cal.walk():
        if component.name == "VEVENT":
            start = component.get("DTSTART").dt

            # all-day events
            if isinstance(start, datetime.date) and not isinstance(start, datetime.datetime):
                if start >= CUTOFF_DATE:
                    new_cal.add_component(component)

            # timed events
            elif isinstance(start, datetime.datetime):
                if start.date() >= CUTOFF_DATE:
                    new_start = start + datetime.timedelta(hours=OFFSET_HOURS)
                    new_end = component.get("DTEND").dt + datetime.timedelta(hours=OFFSET_HOURS)

                    component["DTSTART"].dt = new_start
                    component["DTEND"].dt = new_end

                    new_cal.add_component(component)

    return new_cal.to_ical()

@app.route("/schoology.ics")
def serve_calendar():
    return Response(generate_filtered_calendar(), mimetype="text/calendar")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
