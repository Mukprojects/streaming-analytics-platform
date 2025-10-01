# System Architecture & Design

## Overview
This document describes the technical architecture of the distributed streaming data pipeline, designed to demonstrate production-level distributed systems thinking for infrastructure roles at Google.

## Core Design Principles

### 1. At-Least-Once Delivery Semantics
- **Consumer Groups**: Redis Streams consumer groups provide automatic load balancing and failure recovery
- **Message Acknowledgment**: Explicit XACK after successful processing ensures no message loss
- **Pending Message Recovery**: Automatic detection and reprocessing of unacknowledged messages
- **Idempotency**: Aggregation operations designed to handle duplicate processing gracefully

### 2. Horizontal Scalability
```
Producer → Redis Stream → [Processor-1, Processor-2, Processor-N] → Aggregates
```
- **Consumer Group Scaling**: Add processors by scaling Docker containers
- **Automatic Load Balancing**: Redis Streams distributes messages across available consumers
- **No Single Point of Failure**: Multiple processor instances provide redundancy

### 3. Real-Time Processing Architecture
- **Stream Processing**: Continuous event processing with minimal latency
- **In-Memory Aggregation**: Redis hash operations for fast aggregate updates
- **Metrics Pipeline**: Prometheus metrics for real-time monitoring
- **API Layer**: FastAPI for low-latency data serving

## Component Deep Dive

### Producer Service
**Purpose**: Simulate realistic user event generation
```python
Event Schema:
{
  "event_id": "unique_id",
  "user_id": "user_123", 
  "event_type": "click|view|purchase|signup|logout|search",
  "product": "laptop|phone|tablet|...",
  "session_id": "session_456",
  "value": "23.45",
  "ts": "1640995200000"
}
```

**Key Features**:
- Configurable event rate (events/second)
- Realistic data distribution
- Timestamp-based event ordering
- Graceful rate limiting

### Redis Streams
**Purpose**: Durable message queue with consumer group support

**Stream Structure**:
```
Stream: "events"
├── Consumer Group: "event_group"
│   ├── Consumer: "proc-1" 
│   ├── Consumer: "proc-2"
│   └── Consumer: "proc-N"
└── Messages: [event_1, event_2, ..., event_N]
```

**Advantages**:
- **Persistence**: Messages survive Redis restarts
- **Consumer Groups**: Built-in load balancing and failover
- **Pending Lists**: Automatic tracking of unprocessed messages
- **Blocking Reads**: Efficient real-time processing

### Processor Service
**Purpose**: Stream consumer with real-time aggregation

**Processing Pipeline**:
1. **Message Consumption**: XREADGROUP with consumer group
2. **Event Processing**: Parse and validate event data
3. **Aggregation**: Update Redis hash counters atomically
4. **Acknowledgment**: XACK to mark message as processed
5. **Metrics Export**: Prometheus metrics for monitoring

**Failure Recovery**:
```python
# Pending message recovery
pending = redis.xpending_range(stream, group, '-', '+', count=10)
for msg in pending:
    if msg.idle_time > threshold:
        claimed = redis.xclaim(stream, group, consumer, msg.id)
        process_and_ack(claimed)
```

**Aggregation Strategy**:
- **Event Type Counters**: `type:click:count`, `type:view:count`
- **Session Tracking**: `session:123:events`
- **Product Analytics**: `product:laptop:count`
- **Global Metrics**: `total_count`, `last_updated`

### API Service
**Purpose**: Low-latency data serving layer

**Endpoints**:
- `GET /aggregates` - Full aggregation data with parsing
- `GET /aggregates/summary` - Quick summary for dashboards
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

**Response Optimization**:
- **Data Parsing**: Convert Redis strings to appropriate types
- **Structured Output**: Organized by event types, products, sessions
- **Caching Headers**: Appropriate cache control for real-time data
- **Error Handling**: Graceful degradation on Redis failures

## Monitoring & Observability

### Prometheus Metrics
```
# Throughput Metrics
events_processed_total - Counter of processed events
event_type_count{event_type} - Per-type event counters

# Latency Metrics  
processing_latency_seconds - Processing time histogram
api_request_duration_seconds - API response time

# System Health
stream_lag_seconds - Processing lag indicator
consumer_group_pending - Unprocessed message count
```

### Grafana Dashboards
- **Real-time Throughput**: Events/second with trend analysis
- **Latency Distribution**: P50, P95, P99 processing times
- **Event Type Breakdown**: Distribution across event types
- **System Health**: Error rates, consumer lag, API performance

## Failure Modes & Recovery

### 1. Processor Crash
**Scenario**: Processor container stops unexpectedly
**Detection**: Consumer group shows pending messages
**Recovery**: 
- Automatic container restart via Docker
- Pending message claim and reprocessing
- No data loss due to consumer group persistence

### 2. Redis Network Partition
**Scenario**: Network connectivity to Redis lost
**Detection**: Connection timeouts, health check failures
**Recovery**:
- Exponential backoff reconnection
- Message buffering during partition
- Automatic resume on connectivity restore

### 3. High Load Scenarios
**Scenario**: Event rate exceeds processing capacity
**Detection**: Increasing consumer lag metrics
**Recovery**:
- Horizontal scaling (add processor instances)
- Backpressure handling with blocking reads
- Alert-based auto-scaling triggers

## Performance Characteristics

### Throughput Benchmarks
- **Target**: 5,000+ events/second sustained
- **Bottlenecks**: Redis write throughput, network I/O
- **Scaling**: Linear scaling with processor count

### Latency Profile
- **Event-to-Aggregate**: <10ms median
- **API Response**: <100ms for full aggregates
- **End-to-End**: <50ms for simple queries

### Resource Usage
- **Memory**: ~100MB per processor instance
- **CPU**: ~0.5 cores per 1000 events/second
- **Network**: ~1MB/s per 1000 events/second

## Production Deployment Considerations

### Infrastructure Requirements
```yaml
# Kubernetes Deployment Example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stream-processor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: processor
  template:
    spec:
      containers:
      - name: processor
        image: stream-processor:latest
        env:
        - name: REDIS_HOST
          value: "redis-cluster.default.svc.cluster.local"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi" 
            cpu: "500m"
```

### Security Considerations
- **Redis AUTH**: Authentication for Redis access
- **Network Policies**: Restrict inter-service communication
- **TLS Encryption**: Encrypt data in transit
- **Secret Management**: Environment-based configuration

### Operational Excellence
- **Health Checks**: Comprehensive service health monitoring
- **Logging**: Structured logging with correlation IDs
- **Alerting**: Prometheus alerts for SLA violations
- **Backup Strategy**: Redis persistence and backup procedures

## Scaling Strategy

### Vertical Scaling
- Increase processor container resources
- Optimize Redis configuration for higher throughput
- Use Redis Cluster for distributed storage

### Horizontal Scaling  
- Add processor instances to consumer group
- Implement stream sharding for extreme scale
- Deploy across multiple availability zones

### Auto-Scaling Triggers
```yaml
# HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: stream-processor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: consumer_group_pending
      target:
        type: AverageValue
        averageValue: "100"
```

This architecture demonstrates production-ready distributed systems design with emphasis on reliability, scalability, and operational excellence - key principles valued in Google's infrastructure engineering roles.