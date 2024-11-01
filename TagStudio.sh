#! /usr/bin/env bash
set -e
cd "$(dirname "$0")"
! [ -d .venv ] && python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd tagstudio
python tag_studio.py
