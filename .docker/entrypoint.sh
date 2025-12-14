#!/bin/sh
set -e

uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --notebook-dir=/app/notebooks