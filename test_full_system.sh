#!/bin/bash
# Full System Test Script for 3D Room Intelligence API
# Tests the complete pipeline with Room scan v1.ply

set -e

API_URL="http://localhost:8000"
SCAN_FILE="Room scan v1.ply"

echo "=========================================="
echo "3D Room Intelligence - Full System Test"
echo "=========================================="
echo ""

# Check if API is running
echo "Step 1: Checking API health..."
if curl -s "${API_URL}/api/health" > /dev/null; then
    echo "✅ API is running"
    curl -s "${API_URL}/api/health" | python3 -m json.tool
else
    echo "❌ API is not running. Start it with:"
    echo "   uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo "Step 2: Checking scan file..."
if [ ! -f "$SCAN_FILE" ]; then
    echo "❌ Scan file not found: $SCAN_FILE"
    exit 1
fi
echo "✅ Scan file found: $(ls -lh "$SCAN_FILE" | awk '{print $5}')"

echo ""
echo "Step 3: Uploading room scan..."
UPLOAD_RESPONSE=$(curl -s -X POST "${API_URL}/api/upload-scan" \
    -F "file=@${SCAN_FILE}")

ROOM_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['room_id'])" 2>/dev/null || echo "unknown")

if [ "$ROOM_ID" != "unknown" ]; then
    echo "✅ Upload successful!"
    echo "$UPLOAD_RESPONSE" | python3 -m json.tool
else
    echo "❌ Upload failed"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

echo ""
echo "Step 4: Retrieving room dimensions..."
curl -s "${API_URL}/api/room/${ROOM_ID}/dimensions" | python3 -m json.tool

echo ""
echo "Step 5: Retrieving detected objects..."
OBJECTS_COUNT=$(curl -s "${API_URL}/api/room/${ROOM_ID}/objects" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "✅ Found $OBJECTS_COUNT objects"
curl -s "${API_URL}/api/room/${ROOM_ID}/objects" | python3 -m json.tool | head -40

echo ""
echo "Step 6: Retrieving complete room data..."
curl -s "${API_URL}/api/room/${ROOM_ID}/data" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Room ID: {d[\"room_id\"]}')
print(f'Dimensions: {d[\"dimensions\"][\"length\"]:.2f}m × {d[\"dimensions\"][\"width\"]:.2f}m × {d[\"dimensions\"][\"height\"]:.2f}m')
print(f'Point Count: {d[\"point_count\"]:,} original → {d[\"processed_points\"]:,} processed')
print(f'Objects Detected: {len(d[\"objects\"])}')
for i, obj in enumerate(d[\"objects\"][:5], 1):
    dims = obj[\"dimensions\"]
    print(f'  {i}. {obj[\"type\"].upper()}: {dims[0]:.2f}m × {dims[1]:.2f}m × {dims[2]:.2f}m')
    print(f'     Confidence: {obj[\"confidence\"]:.0%} | Volume: {obj[\"volume\"]:.3f}m³')
"

echo ""
echo "Step 7: Testing item fit check..."
curl -s -X POST "${API_URL}/api/room/${ROOM_ID}/check-fit" \
    -H "Content-Type: application/json" \
    -d '{"item_type": "table", "dimensions": [1.2, 0.8, 0.75]}' | python3 -m json.tool

echo ""
echo "Step 8: Testing layout optimization..."
curl -s "${API_URL}/api/room/${ROOM_ID}/optimize" | python3 -m json.tool

echo ""
echo "=========================================="
echo "✅ Full System Test Complete!"
echo "=========================================="
echo ""
echo "Room ID: $ROOM_ID"
echo "API Docs: ${API_URL}/api/docs"
echo ""

