#!/usr/bin/env bash
echo "========================================================"
echo "  Praesync Incident Command Engine (FastAPI Proxy)"
echo "  Powered by Switch AI, LiteLLM and Gemini-3.5-Flash"
echo "========================================================"
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
python3 main.py

