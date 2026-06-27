#!/bin/bash
curl -X POST http://localhost:8000/generate -H Content-Type: application/json -d '{"prompt":"test"}' --max-time 5 &
sleep 2
sudo /opt/connective-ai/venv/bin/py-spy dump --pid 2537
