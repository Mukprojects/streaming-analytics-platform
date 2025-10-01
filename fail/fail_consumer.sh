#!/usr/bin/env bash
# Failure injection script - simulates processor crash and recovery

echo "=== Streaming Pipeline Failure Test ==="
echo "This script will:"
echo "1. Stop the processor (simulate crash)"
echo "2. Wait 10 seconds (simulate downtime)"
echo "3. Restart processor (simulate recovery)"
echo "4. Show recovery metrics"
echo

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found"
    exit 1
fi

echo "Step 1: Checking current state..."
docker-compose exec redis redis-cli XINFO GROUPS events 2>/dev/null || echo "No consumer groups yet"

echo
echo "Step 2: Stopping processor (simulating crash)..."
docker-compose stop processor

echo
echo "Step 3: Waiting 10 seconds (simulating downtime)..."
for i in {10..1}; do
    echo "  Downtime: ${i}s remaining..."
    sleep 1
done

echo
echo "Step 4: Checking pending messages during downtime..."
docker-compose exec redis redis-cli XPENDING events event_group 2>/dev/null || echo "No pending messages"

echo
echo "Step 5: Restarting processor (simulating recovery)..."
docker-compose start processor

echo
echo "Step 6: Waiting for recovery (5s)..."
sleep 5

echo
echo "Step 7: Post-recovery status:"
echo "Consumer group info:"
docker-compose exec redis redis-cli XINFO GROUPS events 2>/dev/null || echo "Consumer group not found"

echo
echo "Pending messages:"
docker-compose exec redis redis-cli XPENDING events event_group 2>/dev/null || echo "No pending messages"

echo
echo "=== Failure test complete ==="
echo "Check Grafana dashboard to see the recovery pattern"
echo "Expected behavior:"
echo "- Events should continue processing after restart"
echo "- No data loss (at-least-once delivery)"
echo "- Pending messages should be processed"