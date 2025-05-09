#!/bin/bash

echo "Starte Terminüberwachung..."

while true; do
  python /watch_calendar.py
  sleep 30  # alle 30 Sekunden prüfen
done
