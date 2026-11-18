#!/bin/bash
# Double-click this file to launch the organizer.
cd "$(dirname "$0")"
source .venv/bin/activate
export NOTES_ROOT="$HOME/Dropbox/Job Search"
streamlit run app.py
