import mysql.connector
import os
import smtplib
from email.message import EmailMessage
from icalendar import Calendar

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)

cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT calendardata FROM calendarobjects
    WHERE componenttype = 'VEVENT' AND lastmodified >= UNIX_TIMESTAMP(NOW() - INTERVAL 1 MINUTE)
""")
rows = cursor.fetchall()

for row in rows:
    cal = Calendar.from_ical(row['calendardata'])
    event = next(c for c in cal.walk() if c.name == "VEVENT")
    attendees = event.get("attendee")
    if not attendees:
        continue
    if not isinstance(attendees, list):
        attendees = [attendees]

    msg = EmailMessage()
    msg["Subject"] = f"Einladung: {event.get('summary')}"
    msg["From"] = os.getenv("FROM_EMAIL")
    msg["To"] = ", ".join([a.to_ical().decode().replace("mailto:", "") for a in attendees])
    msg.set_content(f"""Einladung:

Titel: {event.get('summary')}
Beginn: {event.get('dtstart').dt}
Ende: {event.get('dtend').dt}
Ort: {event.get('location', 'nicht angegeben')}
""")

    msg.add_attachment(
        row['calendardata'].encode(),
        maintype="text",
        subtype="calendar",
        filename="invite.ics"
    )

    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as s:
        s.starttls()
        s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        s.send_message(msg)

cursor.close()
conn.close()
