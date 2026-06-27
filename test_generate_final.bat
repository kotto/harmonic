@echo off
echo Testing /generate endpoint...
curl -X POST http://54.166.179.141:8000/generate -H "Content-Type: application/json" -d "{\"prompt\":\"test\"}" --max-time 10
echo.
echo Test completed!
pause
