FROM python:3.11-slim

RUN pip install icalendar mysql-connector-python

COPY watch_calendar.py /watch_calendar.py
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
