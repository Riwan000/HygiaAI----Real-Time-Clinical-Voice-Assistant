# Federated Memory Architecture

## Overview

The Federated Memory Architecture enables privacy-preserving knowledge sharing across multiple rural clinics without exposing raw patient data. It uses federated learning techniques to aggregate embeddings and knowledge patterns while maintaining HIPAA compliance.

## Architecture Components

### 1. Secure Aggregator (`src/federated/secure_aggregator.py`)

Implements privacy-preserving aggregation methods:

- **Federated Averaging (FedAvg)**: Standard aggregation method
- **Weighted Averaging**: Weighted by data size for fair representation
- **Median Aggregation**: Robust against outliers
- **Differential Privacy**: Adds calibrated noise for privacy
- **Secure Aggregation**: Placeholder for full SMPC implementation

**Privacy Levels:**
- **BASIC**: Standard federated averaging
- **ENHANCED**: With differential privacy noise
- **STRICT**: With secure multi-party computation (placeholder)

### 2. Federated Coordinator (`src/federated/coordinator.py`)

Central server component that:
- Manages aggregation rounds
- Registers participating clinics
- Collects embeddings from clients
- Performs secure aggregation
- Tracks round status and history

### 3. Federated Client (`src/federated/client.py`)

Client-side component for each clinic:
- Registers with coordinator
- Collects local embeddings
- Aggregates local embeddings
- Submits to aggregation rounds
- Tracks participation history

### 4. Federated Sync (`src/federated/sync.py`)

Synchronization manager:
- Syncs local embeddings to global model
- Syncs global model updates to local storage
- Handles conflict resolution
- Manages sync intervals and retries

### 5. Privacy Mechanisms (`src/federated/privacy.py`)

Privacy-preserving techniques:
- **Differential Privacy**: Gaussian and Laplace mechanisms
- **Secure Multi-Party Computation**: Placeholder for full implementation
- **Homomorphic Encryption**: Placeholder for full implementation

### 6. Integration Layer (`src/federated/integration.py`)

Integrates federated components with existing HygiaAI:
- Connects with QdrantStorage
- Manages coordinator and client instances
- Handles embedding collection and storage
- Provides unified API

## API Endpoints

### Coordinator Endpoints (Server)

- `POST /api/v1/federated/rounds/start` - Start aggregation round
- `POST /api/v1/federated/rounds/{round_id}/aggregate` - Aggregate round
- `GET /api/v1/federated/rounds/{round_id}/status` - Get round status
- `GET /api/v1/federated/statistics` - Get federated statistics

### Client Endpoints

- `POST /api/v1/federated/rounds/{round_id}/submit` - Submit embedding
- `POST /api/v1/federated/participate/{round_id}` - Participate in round
- `POST /api/v1/federated/sync` - Sync with global model

## Usage

### As Coordinator (Server)

```python
from src.federated.integration import FederatedMemoryIntegration
from src.storage.qdrant_storage import QdrantStorage

# Initialize
storage = QdrantStorage(collection_name="hygiaai_transcripts")
integration = FederatedMemoryIntegration(
    qdrant_storage=storage,
    enable_federated=True
)

# Start aggregation round
round_id = integration.start_federated_round(min_clients=2)

# Wait for clients to submit...

# Aggregate round
result = integration.aggregate_round(round_id)
```

### As Client (Clinic)

```python
from src.federated.integration import FederatedMemoryIntegration
from src.storage.qdrant_storage import QdrantStorage

# Initialize
storage = QdrantStorage(collection_name="hygiaai_transcripts")
integration = FederatedMemoryIntegration(
    qdrant_storage=storage,
    coordinator_url="http://coordinator:8000",
    client_id="clinic_001",
    enable_federated=True
)

# Participate in round
success = integration.participate_in_federated_round(round_id)
```

## Privacy Guarantees

### Differential Privacy

- **Epsilon (ε)**: Privacy budget (lower = more private)
- **Delta (δ)**: Failure probability (typically 1e-5)
- **Sensitivity**: L2 norm bound for clipping

### Aggregation Methods

1. **Federated Averaging**: Standard, efficient, basic privacy
2. **Weighted Averaging**: Fair representation, accounts for data size
3. **Median Aggregation**: Robust to outliers, good for heterogeneous data
4. **Differential Privacy**: Strong privacy guarantees with calibrated noise

## Configuration

### Aggregation Config

```python
from src.federated.secure_aggregator import AggregationConfig, AggregationMethod, PrivacyLevel

config = AggregationConfig(
    method=AggregationMethod.FEDERATED_AVERAGING,
    privacy_level=PrivacyLevel.ENHANCED,
    epsilon=1.0,
    delta=1e-5,
    clip_norm=1.0,
    min_clients=2
)
```

### Sync Config

```python
from src.federated.sync import SyncConfig

sync_config = SyncConfig(
    sync_interval=3600,  # 1 hour
    max_retries=3,
    timeout=300,
    conflict_resolution="merge",
    enable_auto_sync=True
)
```

## Testing

Run the test suite:

```bash
python examples/test_federated_architecture.py
```

**Test Results:**
- ✅ Secure Aggregator: All methods working
- ✅ Federated Coordinator: Round management working
- ✅ Federated Client: Client operations working
- ✅ Privacy Mechanisms: Differential privacy working
- ⚠️ Integration: Requires Qdrant running

## Security Considerations

1. **No Raw Data Sharing**: Only aggregated embeddings are shared
2. **Differential Privacy**: Adds noise to protect individual contributions
3. **Secure Aggregation**: Uses privacy-preserving aggregation methods
4. **HIPAA Compliance**: No PHI is transmitted, only aggregated patterns

## Future Enhancements

- [ ] Full Secure Multi-Party Computation implementation
- [ ] Homomorphic Encryption for encrypted aggregation
- [ ] Asynchronous aggregation rounds
- [ ] Automatic round scheduling
- [ ] Performance optimization for large-scale deployments
- [ ] Advanced conflict resolution strategies

## Integration with Existing System

The federated architecture is fully integrated with:
- ✅ QdrantStorage for local embedding storage
- ✅ BioBERT embeddings for text representation
- ✅ Clinical memory API for unified access
- ✅ FastAPI for REST endpoints

## Deployment

### Coordinator Setup

```bash
# Set environment variables
export FEDERATED_MODE=coordinator

# Start API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Client Setup

```bash
# Set environment variables
export FEDERATED_MODE=client
export FEDERATED_COORDINATOR_URL=http://coordinator:8000
export FEDERATED_CLIENT_ID=clinic_001

# Start API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8001
```

## Documentation

- `src/federated/` - Core federated learning components
- `src/api/federated_api.py` - REST API endpoints
- `examples/test_federated_architecture.py` - Test suite
- `docs/FEDERATED_ARCHITECTURE.md` - This document

