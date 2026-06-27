@echo off
echo Testing with COMPLETE GenerationRequest schema...
curl -X POST http://54.166.179.141:8000/generate -H "Content-Type: application/json" -d @test_complete.json --max-time 10
echo.
echo Test completed!
pause
