#!/bin/bash

exec uvicorn "main:api" --host "0.0.0.0" --port "8000" &
exec python consumer.py