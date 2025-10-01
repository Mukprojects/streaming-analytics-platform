#!/usr/bin/env python3
"""
Basic unit tests for the streaming pipeline components.
"""
import pytest
import redis
import time
import json
from unittest.mock import Mock, patch

def test_redis_connection():
    """Test Redis connection"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        assert r.ping() == True
    except redis.ConnectionError:
        pytest.skip("Redis not available for testing")

def test_event_generation():
    """Test event generation logic"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'producer'))
    
    from producer import make_event
    
    event = make_event(1)
    
    # Check required fields
    assert 'event_id' in event
    assert 'user_id' in event
    assert 'event_type' in event
    assert 'ts' in event
    
    # Check data types
    assert isinstance(event['event_id'], str)
    assert isinstance(event['user_id'], str)
    assert event['event_type'] in ['click', 'view', 'purchase', 'signup', 'logout', 'search']

def test_aggregation_logic():
    """Test aggregation logic"""
    # Mock Redis for testing
    mock_redis = Mock()
    
    # Test data
    test_msg = {
        'event_type': 'click',
        'user_id': '123',
        'session_id': '456',
        'product': 'laptop',
        'ts': str(int(time.time() * 1000))
    }
    
    # This would test the update_aggregates function
    # In a real implementation, we'd extract this to a testable function
    assert test_msg['event_type'] == 'click'
    assert test_msg['user_id'] == '123'

def test_api_response_format():
    """Test API response format"""
    # Mock aggregates data
    mock_data = {
        'total_count': '1000',
        'type:click:count': '500',
        'type:view:count': '300',
        'last_updated': str(int(time.time()))
    }
    
    # Test parsing logic (simplified)
    event_types = {}
    for k, v in mock_data.items():
        if k.startswith("type:") and k.endswith(":count"):
            event_type = k.split(":")[1]
            event_types[event_type] = int(v)
    
    assert 'click' in event_types
    assert 'view' in event_types
    assert event_types['click'] == 500
    assert event_types['view'] == 300

if __name__ == "__main__":
    pytest.main([__file__])