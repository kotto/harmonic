#!/bin/bash
sleep 5
curl -v -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"prompt":"victory_test"}' --max-time 15
