#!/bin/bash
# Quick script to start API and get room_id from your bedroom scan

echo "=== 3D Room Intelligence API - Quick Start ==="
echo ""

# Navigate to project directory
cd "/home/nathan/Documents/Cursor Projects/3d Scan integration"

# Activate virtual environment
echo "1. Activating virtual environment..."
source venv311/bin/activate

# Start PostgreSQL
echo "2. Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for database
echo "3. Waiting for database to be ready (10 seconds)..."
sleep 10

# Check if database is ready
if docker-compose ps | grep -q "postgres.*Up"; then
    echo "   ✅ Database is running"
else
    echo "   ❌ Database failed to start"
    exit 1
fi

# Start API in background
echo "4. Starting API server..."
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/room_api.log 2>&1 &
API_PID=$!

# Wait for API to start
echo "5. Waiting for API to start (5 seconds)..."
sleep 5

# Check if API is running
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "   ✅ API is running at http://localhost:8000"
else
    echo "   ❌ API failed to start. Check /tmp/room_api.log"
    exit 1
fi

echo ""
echo "=== Uploading Your Bedroom Scan ==="
echo ""

# Upload the scan
if [ -f "Room scan v1.ply" ]; then
    echo "Uploading Room scan v1.ply..."
    RESPONSE=$(curl -s -X POST "http://localhost:8000/api/upload-scan" \
      -F "file=@Room scan v1.ply")
    
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    
    # Extract room_id
    ROOM_ID=$(echo "$RESPONSE" | jq -r '.room_id' 2>/dev/null)
    
    if [ "$ROOM_ID" != "null" ] && [ -n "$ROOM_ID" ]; then
        echo ""
        echo "=== SUCCESS ==="
        echo ""
        echo "✅ Your room_id is: $ROOM_ID"
        echo ""
        echo "Save this for your other project!"
        echo ""
        echo "=== Quick Test Queries ==="
        echo ""
        
        # Get dimensions
        echo "Room Dimensions:"
        curl -s "http://localhost:8000/api/room/$ROOM_ID/dimensions" | jq '.'
        
        echo ""
        echo "Detected Objects:"
        curl -s "http://localhost:8000/api/room/$ROOM_ID/objects" | jq '. | length' | xargs echo "  Count:"
        curl -s "http://localhost:8000/api/room/$ROOM_ID/objects" | jq '.[].type' | sort | uniq -c
        
        echo ""
        echo "=== Next Steps ==="
        echo ""
        echo "Tell Cursor in your other project:"
        echo "\"My room_id is '$ROOM_ID'. Query the API now to get real dimensions.\""
        echo ""
        echo "API is running at: http://localhost:8000"
        echo "API Docs: http://localhost:8000/api/docs"
        echo "API PID: $API_PID (kill $API_PID to stop)"
    else
        echo "❌ Failed to get room_id from response"
        echo "Response was: $RESPONSE"
    fi
else
    echo "❌ Room scan v1.ply not found!"
    echo "Place your scan file in the project root directory."
fi

echo ""
echo "=== API Status ==="
echo "✅ API running on http://localhost:8000 (PID: $API_PID)"
echo "✅ Database running (docker-compose)"
echo ""
echo "To stop:"
echo "  kill $API_PID"
echo "  docker-compose down"

