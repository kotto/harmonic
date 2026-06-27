#!/bin/bash
curl -v -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"prompt":"test"}' --max-time 10
