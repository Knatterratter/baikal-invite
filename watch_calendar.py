import mysql.connector
import time
import icalendar
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

print("Starte Terminüberwachung...")

# Verbindungsparameter aus Umgebungsvariablen
import os

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")

conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME
)

cursor = conn.cursor(dictionary=True)
last_ids = set()

while True:
    cursor.execute("SELECT id, calendardata FROM calendarobjects ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        if row['id'] not in last_ids:
            last_ids.add(row['id'])

            try:
                # Wichtig: Kein .encode(), da Daten bereits bytes sind
                ical = icalendar.Calendar.from_ical(row['calendardata'])

                for component in ical.walk():
                    if component.name == "VEVENT":
                        summary = component.get("summary", "Kein Titel")
                        dtstart = component.get("dtstart").dt
                        attendees = component.get("attendee")
                        if not attendees:
                            continue
                        if not isinstance(attendees, list):
                            attendees = [attendees]

                        for attendee in attendees:
                            email = attendee.to_ical().decode().replace("mailto:", "")
                            msg = MIMEText(f"Neue Einladung: {summary}\nBeginn: {dtstart}")
                            msg["Subject"] = f"Einladung: {summary}"
                            msg["From"] = formataddr(("Kalender", FROM_EMAIL))
                            msg["To"] = email

                            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                                server.starttls()
                                server.login(SMTP_USER, SMTP_PASS)
                                server.sendmail(FROM_EMAIL, [email], msg.as_string())

                            print(f"Einladung gesendet an: {email}")

            except Exception as e:
                print(f"Fehler beim Verarbeiten von Eintrag {row['id']}: {e}")

    time.sleep(30)  # Alle 30 Sekunden prüfen
