# HARMONIC AI - DEMONSTRATION INSTRUCTIONS

## ðŸš€ LIVE DEMO ENDPOINT

### Base URL
```
http://__EC2_IP__:8000
```

### Available Endpoints

#### 1. Health Check
```bash
curl -X GET "http://__EC2_IP__:8000/health"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0-real",
  "timestamp": 1778908039.1848667,
  "features": {
    "harmonic_transform": true,
    "deterministic_cache": true,
    "verified_mode": true
  }
}
```

#### 2. Generate Text
```bash
curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "Explain the importance of determinism in AI for healthcare applications.",
    "max_tokens": 500,
    "temperature": 0.0,
    "verified_mode": false
  }'
```

#### 3. Generate with Verified Mode
```bash
curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "What are the clinical guidelines for hypertension management?",
    "max_tokens": 800,
    "temperature": 0.0,
    "verified_mode": true,
    "require_citations": true
  }'
```

## ðŸ”¬ DETERMINISM VERIFICATION TEST

### Test Procedure

1. **Send identical requests multiple times:**
```bash
for i in {1..5}; do
  curl -X POST "http://__EC2_IP__:8000/generate"     -H "Content-Type: application/json"     -d '{
      "prompt": "Calculate 15 * 27 and explain the multiplication process.",
      "max_tokens": 300,
      "temperature": 0.0
    }' | jq '.response_id, .text[0:100]'
  echo "---"
done
```

2. **Verify Results:**
   - All `response_id` values should be identical
   - All `text` responses should be byte-for-byte identical
   - All `tokens_generated` counts should match

### Expected Outcome
```
"sha256:abc123def456..."
"15 * 27 = 405. The multiplication can be broken down as..."
---
"sha256:abc123def456..."
"15 * 27 = 405. The multiplication can be broken down as..."
---
"sha256:abc123def456..."
"15 * 27 = 405. The multiplication can be broken down as..."
```

## ðŸ“Š PERFORMANCE TESTING

### Response Time Measurement
```bash
time curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "Write a Python function to check if a number is prime.",
    "max_tokens": 400,
    "temperature": 0.0
  }'
```

### Throughput Test
```bash
# Test with 10 concurrent requests
for i in {1..10}; do
  curl -X POST "http://__EC2_IP__:8000/generate"     -H "Content-Type: application/json"     -d '{
      "prompt": "Test request $i",
      "max_tokens": 100,
      "temperature": 0.0
    }' &
done
wait
```

## ðŸŽ¯ LM ARENA SPECIFIC TESTS

### 1. Reasoning Test
```bash
curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "If all cats are mammals, and all mammals are animals, are all cats animals? Explain the syllogistic reasoning.",
    "max_tokens": 500,
    "temperature": 0.0
  }'
```

### 2. Programming Test
```bash
curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "Write an optimized Python function to find the longest palindrome substring in a given string.",
    "max_tokens": 600,
    "temperature": 0.0
  }'
```

### 3. Mathematics Test
```bash
curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "Calculate the integral of xÂ² * sin(x) from 0 to Ï€. Show step-by-step integration.",
    "max_tokens": 700,
    "temperature": 0.0
  }'
```

### 4. Creativity Test
```bash
curl -X POST "http://__EC2_IP__:8000/generate"   -H "Content-Type: application/json"   -d '{
    "prompt": "Write a short science fiction story about a world where AI has solved all human problems but created new existential dilemmas.",
    "max_tokens": 800,
    "temperature": 0.0
  }'
```

## âš ï¸ TROUBLESHOOTING

### Common Issues

1. **Connection Timeout**
   - Verify instance is running: `ping __EC2_IP__`
   - Check firewall rules
   - Ensure port 8000 is open

2. **Slow Responses**
   - Model is processing complex requests
   - Check instance resource utilization
   - Consider simpler prompts for speed testing

3. **Verification Failures**
   - Ensure identical parameters (especially temperature=0.0)
   - Check for network variability
   - Verify no external context influencing responses

### Support Contact
For technical issues with the demo endpoint:
- **Email:** support@harmonica.ai
- **Response Time:** < 4 hours during business hours

## ðŸ“ˆ MONITORING

### Health Status
```
GET /health
```

### Performance Metrics
```
GET /metrics
```

### System Information
```
GET /info
```

---

*Last Updated: 16 May 2026*
*Demo available 24/7 with 99.9% uptime guarantee*
