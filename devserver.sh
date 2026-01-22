#!/bin/sh
source .venv/bin/activate
# Use port 8080 as a default if $PORT is not set
python -u -m flask --app src.app run -p ${PORT:-8080} --debug
