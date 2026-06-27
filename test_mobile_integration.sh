#!/bin/bash

# Test script for mobile compression integration
# Tests all mobile endpoints and verifies functionality

set -e

BASE_URL="http://localhost:3000"
TEST_DIR="/tmp/mobile_test"
RESULTS_FILE="$TEST_DIR/results.txt"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Mobile Compression Integration Test"
echo "=========================================="
echo ""

# Create test directory
mkdir -p "$TEST_DIR"
> "$RESULTS_FILE"

# Function to log results
log_result() {
    local test_name=$1
    local status=$2
    local message=$3
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        echo "✓ PASS: $test_name - $message" >> "$RESULTS_FILE"
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        echo "✗ FAIL: $test_name - $message" >> "$RESULTS_FILE"
    fi
}

# Test 1: Check if server is running
echo "Test 1: Checking if server is running..."
if curl -s "$BASE_URL/api/mobile/info" > /dev/null 2>&1; then
    log_result "Server Running" "PASS" "Server is accessible at $BASE_URL"
else
    log_result "Server Running" "FAIL" "Cannot reach server at $BASE_URL"
    echo "Make sure your server is running: npm start"
    exit 1
fi
echo ""

# Test 2: Get mobile info
echo "Test 2: Getting mobile codec info..."
RESPONSE=$(curl -s "$BASE_URL/api/mobile/info")
if echo "$RESPONSE" | grep -q "supported_formats"; then
    log_result "Mobile Info Endpoint" "PASS" "Returns supported formats"
    echo "Supported formats:"
    echo "$RESPONSE" | grep -o '"photos":\[[^]]*\]' | head -1
    echo "$RESPONSE" | grep -o '"videos":\[[^]]*\]' | head -1
else
    log_result "Mobile Info Endpoint" "FAIL" "Did not return expected format"
fi
echo ""

# Test 3: Create test JPEG image
echo "Test 3: Creating test JPEG image..."
if command -v convert &> /dev/null; then
    convert -size 800x600 xc:blue "$TEST_DIR/test_photo.jpg" 2>/dev/null
    if [ -f "$TEST_DIR/test_photo.jpg" ]; then
        SIZE=$(stat -f%z "$TEST_DIR/test_photo.jpg" 2>/dev/null || stat -c%s "$TEST_DIR/test_photo.jpg" 2>/dev/null)
        log_result "Test Image Creation" "PASS" "Created test JPEG ($SIZE bytes)"
    else
        log_result "Test Image Creation" "FAIL" "Could not create test image"
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC}: ImageMagick not installed, skipping test image creation"
    echo "To test with real images, use: curl -X POST $BASE_URL/api/mobile/compress -F 'file=@your_photo.jpg'"
fi
echo ""

# Test 4: Test compression endpoint (if test image exists)
if [ -f "$TEST_DIR/test_photo.jpg" ]; then
    echo "Test 4: Testing compression endpoint..."
    RESPONSE=$(curl -s -X POST "$BASE_URL/api/mobile/compress" \
        -F "file=@$TEST_DIR/test_photo.jpg" \
        -F "media-type=auto")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        log_result "Compression Endpoint" "PASS" "Successfully compressed test image"
        
        # Extract metrics
        RATIO=$(echo "$RESPONSE" | grep -o '"ratio":[0-9.]*' | cut -d: -f2)
        SAVINGS=$(echo "$RESPONSE" | grep -o '"savings":[0-9.]*' | cut -d: -f2)
        echo "  Compression ratio: $RATIO:1"
        echo "  Savings: $SAVINGS%"
    else
        log_result "Compression Endpoint" "FAIL" "Compression failed"
        echo "Response: $RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC}: Test image not available, skipping compression test"
fi
echo ""

# Test 5: Check Python codec
echo "Test 5: Checking Python codec..."
if python3 COMPRESSION-SOLUTIONS/HCV_MOBILE_CAMERA_CODEC/hcv_mobile_camera_codec.py --help > /dev/null 2>&1; then
    log_result "Python Codec" "PASS" "Codec script is accessible"
else
    log_result "Python Codec" "FAIL" "Cannot access codec script"
fi
echo ""

# Test 6: Check Python dependencies
echo "Test 6: Checking Python dependencies..."
MISSING_DEPS=""
for dep in pillow numpy zstandard; do
    if ! python3 -c "import ${dep//-/_}" 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $dep"
    fi
done

if [ -z "$MISSING_DEPS" ]; then
    log_result "Python Dependencies" "PASS" "All required packages installed"
else
    log_result "Python Dependencies" "FAIL" "Missing packages:$MISSING_DEPS"
    echo "Install with: pip install pillow numpy zstandard"
fi
echo ""

# Test 7: Check mobile handler file
echo "Test 7: Checking mobile handler file..."
if [ -f "api/mobile_handler.js" ]; then
    log_result "Mobile Handler" "PASS" "api/mobile_handler.js exists"
else
    log_result "Mobile Handler" "FAIL" "api/mobile_handler.js not found"
fi
echo ""

# Test 8: Check mobile routes file
echo "Test 8: Checking mobile routes file..."
if [ -f "api/routes_mobile.js" ]; then
    log_result "Mobile Routes" "PASS" "api/routes_mobile.js exists"
else
    log_result "Mobile Routes" "FAIL" "api/routes_mobile.js not found"
fi
echo ""

# Test 9: Check web interface
echo "Test 9: Checking web interface..."
if grep -q "📱 Mobile Photos/Vidéos" COMPRESSION-SOLUTIONS/unified_compression.html; then
    log_result "Web Interface" "PASS" "Mobile tab found in unified_compression.html"
else
    log_result "Web Interface" "FAIL" "Mobile tab not found in unified_compression.html"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
PASS_COUNT=$(grep -c "✓ PASS" "$RESULTS_FILE" || true)
FAIL_COUNT=$(grep -c "✗ FAIL" "$RESULTS_FILE" || true)

echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Integrate routes into your Express server:"
    echo "   const { registerMobileRoutes } = require('./api/routes_mobile');"
    echo "   registerMobileRoutes(app);"
    echo ""
    echo "2. Test with real smartphone photos/videos"
    echo ""
    echo "3. Access web interface at: http://localhost:3000/path/to/unified_compression.html"
else
    echo -e "${RED}Some tests failed. See details above.${NC}"
    exit 1
fi

echo ""
echo "Full results saved to: $RESULTS_FILE"
