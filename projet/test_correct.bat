@echo off
echo Testing with CORRECT JSON schema...
curl -X POST http://54.166.179.141:8000/generate -H "Content-Type: application/json" -d @correct_test.json --max-time 10
echo.
echo Test completed!
pause
