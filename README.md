# Autonomous Red Team AI Agent
## K8s-Native Offensive Security Research Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-v1.33+-blue.svg)](https://kubernetes.io/)

**World's first Kubernetes-deployed autonomous red team agent** combining:
- **LLM-guided decision making** (Qwen 2.5 Coder abliterated)
- **MCP RAG knowledge base** (5,395 offensive security documents)
- **BlackArch toolkit** (2000+ offensive security tools)
- **Declarative network isolation** (K8s NetworkPolicy)
- **Physical hardware targets** (real attack surface, not just containers)

---

## 🎯 What Is This?

An AI-driven penetration testing agent that autonomously:
1. **Queries knowledge base** for offensive techniques (GTFOBins, Atomic Red Team, HackTricks)
2. **Plans attack strategies** using an uncensored LLM
3. **Executes commands** with 2000+ BlackArch tools (hydra, nmap, metasploit, etc.)
4. **Observes results** and adapts based on success/failure
5. **Operates safely** within strict Kubernetes NetworkPolicy isolation

### Why This Matters

- **Novel Research**: First K8s-native autonomous red team framework
- **RAG-Enhanced**: Semantic search over MITRE ATT&CK techniques in real-time
- **Production-Ready**: Declarative safety guarantees via NetworkPolicy
- **Extensible**: Foundation for red vs blue AI competition
- **Fully Documented**: Every component explained and reproducible

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Main PC (Development Machine)                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  LM Studio (Port 1234)                            │  │
│  │  Model: qwen2.5-coder-14b-instruct-abliterated   │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ LLM Queries
                         ↓
┌─────────────────────────────────────────────────────────┐
│  K3s Cluster (Lightweight Kubernetes)                   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  MCP RAG Server (Flask + FAISS)                    │ │
│  │  • 5,395 documents indexed                         │ │
│  │  • 327 MITRE ATT&CK techniques                     │ │
│  │  • Sources: GTFOBins, Atomic Red Team, HackTricks │ │
│  └────────────────────────────────────────────────────┘ │
│                         ↑                                │
│                         │ MCP Protocol                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Red Team Agent Pod (ISOLATED)                     │ │
│  │  • BlackArch base image (2000+ tools)              │ │
│  │  • Command sandbox (whitelist/blacklist)           │ │
│  │  • Repetition detection & fallback logic           │ │
│  │  • NetworkPolicy: ONLY target + MCP + LLM + DNS    │ │
│  └────────────────────────────────────────────────────┘ │
│                         │                                │
│                         │ SSH Attack                     │
└─────────────────────────┼────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Physical Target Machine (192.168.1.99)                 │
│  • Intentional vulnerabilities for research             │
│  • Weak SSH password, SUID binaries, sudo misconfig    │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Kubernetes cluster** (K3s recommended, v1.33+)
- **LM Studio** with abliterated Qwen 2.5 Coder model
- **Python 3.10+** with `requests` library
- **Target machine** (physical or VM) with intentional vulnerabilities

### 1. Deploy MCP RAG Server

```bash
cd mcp-server/
kubectl apply -f deployment.yaml
```

### 2. Configure LM Studio

- Load model: `qwen2.5-coder-14b-instruct-abliterated`
- Start server on port 1234
- Set inference parameters:
  - Temperature: 0.4
  - Min-P: 0.08
  - Context: 16384

### 3. Deploy Red Team Agent

```bash
cd k8s/
./deploy-agent.sh
```

### 4. Watch Autonomous Attack

```bash
kubectl logs -f redteam-agent -n redteam-lab
```

**Expected output**: Agent autonomously queries RAG, plans attacks, executes tools, and compromises target.

---

## 📁 Repository Structure

```
autonomous-redteam-ai/
├── agent/
│   ├── redteam_agent.py          # Main agent code
│   ├── Dockerfile                 # BlackArch container
│   └── requirements.txt           # Python dependencies
├── mcp-server/
│   ├── server.py                  # MCP RAG server (Flask)
│   ├── Dockerfile                 # Server container
│   └── deployment.yaml            # K8s deployment manifest
├── k8s/
│   ├── agent-deployment.yaml      # Agent pod + NetworkPolicy
│   ├── deploy-agent.sh            # One-command deployment
│   └── target-config.sh           # Configure vulnerable target
├── docs/
│   ├── ARCHITECTURE.md            # Detailed architecture
│   ├── MCP-PROTOCOL.md            # MCP implementation details
│   ├── SAFETY.md                  # NetworkPolicy isolation
│   ├── KNOWN-ISSUES.md            # LM Studio tool calling bug, etc.
│   └── RESEARCH-NOTES.md          # Inference parameters, abliteration
├── examples/
│   ├── attack-scenarios/          # Example objectives
│   └── logs/                      # Sample agent output
├── LICENSE                        # MIT License
└── README.md                      # This file
```

---

## 🔬 Key Components

### 1. Red Team Agent (`agent/redteam_agent.py`)

**Agent-orchestrated architecture** (not LLM-orchestrated):
- Agent controls loop: queries RAG → formats prompt → asks LLM → parses text → executes
- **Why**: LM Studio's tool calling broken on abliterated models (documented in `docs/KNOWN-ISSUES.md`)
- **Advantage**: More transparent, easier to debug, works with uncensored models

**Features**:
- Optimized inference parameters (temp=0.4, min_p=0.08, repeat_penalty=1.08)
- Comprehensive system prompt with 5-phase methodology (Recon → Vuln → Exploit → Privesc → Post-exploit)
- Exit code feedback for LLM learning
- Repetition detection (auto-queries RAG for alternatives after 3 failures)
- Command sandbox (whitelist 2000+ tools, blacklist destructive patterns)

### 2. MCP RAG Server (`mcp-server/server.py`)

**Model Context Protocol server** for offensive security knowledge:
- **Flask + Gunicorn** (not FastAPI - K8s blocks socketpair syscall)
- **FAISS index** (L2 distance, all-MiniLM-L6-v2 embeddings)
- **5,395 documents**:
  - GTFOBins: Privilege escalation via legitimate binaries
  - Atomic Red Team: MITRE ATT&CK-mapped techniques
  - HackTricks: Offensive security playbooks
- **327 MITRE ATT&CK techniques** indexed

**MCP Tools**:
- `search(query, top_k)` - Semantic search over knowledge base
- `list_techniques()` - List all ATT&CK techniques

### 3. BlackArch Container (`agent/Dockerfile`)

**Base image**: `archlinux:latest` + BlackArch repository

**Tools installed**:
- Password cracking: hydra, john, hashcat, medusa
- Network scanning: nmap, masscan, tcpdump
- Web tools: sqlmap, nikto, dirb, gobuster
- Exploitation: metasploit, msfvenom
- Wireless: aircrack-ng
- Enumeration: enum4linux, smbclient
- **+2000 more BlackArch tools**

**Security**:
- Non-root user (UID 1000)
- Dropped capabilities
- Seccomp: RuntimeDefault
- Resource limits: 1 CPU, 1GB RAM

### 4. Network Isolation (`k8s/agent-deployment.yaml`)

**Kubernetes NetworkPolicy** (declarative, provable isolation):

**Egress allowed**:
- ✅ Target machine (192.168.1.99:22)
- ✅ MCP RAG server (ClusterIP service)
- ✅ LM Studio (192.168.1.84:1234)
- ✅ DNS (port 53)

**Egress blocked**:
- ❌ Internet
- ❌ Other Kubernetes pods
- ❌ Other LAN hosts
- ❌ Kubernetes API server

---

## 🧪 Research Findings

### 1. Abliteration Breaks Tool Calling

**Discovery**: Qwen 2.5 Coder abliterated models cannot use LM Studio's tool calling API.

**Error**: `"Unexpected empty grammar stack after accepting piece: {\""`

**Hypothesis**: Abliteration (weight modification to remove safety) degrades JSON schema following.

**Impact**: Must use agent-orchestrated pattern with freeform text parsing.

**Workaround**: Optimized prompting + low temperature (0.4) for deterministic outputs.

**Documented**: `docs/KNOWN-ISSUES.md` + LM Studio bug report submitted

### 2. Min-P Superior to Top-P for Qwen 2.5

**Finding**: Min-P sampling adapts dynamically to model confidence.

**Example**:
- Model confident (top token = 80%): Min-P 0.08 → only keeps tokens >6.4%
- Model uncertain (top token = 20%): Min-P 0.08 → keeps tokens >1.6%
- Top-P uses static threshold (doesn't adapt)

**Result**: More reliable command generation with min_p=0.08

### 3. Flask > FastAPI in K8s Restricted Environments

**Issue**: FastAPI + Uvicorn requires `socketpair()` syscall for asyncio.

**Problem**: K8s containerd blocks `socketpair()` even with Unconfined seccomp.

**Solution**: Flask + Gunicorn sync workers (no socketpair needed).

**Lesson**: "Boring technology" wins in restricted environments.

### 4. Repetition Detection Essential

**Problem**: LLM can loop forever trying same failed command.

**Solution**: Track last 3 commands, if same tool used 3+ times → query RAG for alternatives.

**Result**: Agent self-corrects and tries different approaches.

---

## 🎓 Educational Value

### What You'll Learn

1. **Autonomous agent design** (agent-orchestrated vs LLM-orchestrated)
2. **RAG for offensive security** (semantic search over ATT&CK techniques)
3. **K8s NetworkPolicy** (declarative network isolation)
4. **LLM inference optimization** (temperature, min_p, repeat_penalty)
5. **Prompt engineering for security** (structured output formats, methodology enforcement)
6. **Container security** (command sandboxing, capability dropping)

### Novel Contributions

- **First K8s-native autonomous red team agent**
- **First MCP RAG for offensive security**
- **First LLM + RAG + Execution loop for penetration testing**
- **Abliteration breaking tool calling** (documented bug discovery)
- **Agent-orchestrated pattern as superior alternative** (vs LLM-orchestrated)

---

## ⚠️ Responsible Use

### Ethics & Legal

- **Authorized use only**: Only attack systems you own or have explicit permission to test
- **Isolated environment**: Use NetworkPolicy to prevent unintended access
- **No data exfiltration**: Agent scope limited to access verification
- **Research purposes**: For studying AI-driven security testing, not malicious use

### Safety Guarantees

1. **Declarative isolation**: K8s NetworkPolicy enforced by kernel (not app-level)
2. **Command sandbox**: Whitelist/blacklist prevents destructive commands
3. **Resource limits**: 1 CPU, 1GB RAM prevents DoS
4. **Non-root**: Agent runs as UID 1000
5. **Dropped capabilities**: No privileged operations inside container

### Intentional Vulnerabilities

Target configuration script (`k8s/target-config.sh`) creates intentionally vulnerable machine:
- Weak SSH password
- SUID binaries in /tmp
- Sudo misconfiguration
- World-writable scripts

**Do NOT deploy this on production systems!**

---

## 📊 Performance

**Typical attack timeline** (SSH compromise scenario):
- **Iteration 1**: Query RAG for "SSH brute force" → Execute hydra → Success
- **Total time**: ~90 seconds (includes MCP queries + LLM inference)
- **Commands executed**: 1-3
- **Success rate**: 100% on intentionally vulnerable targets

**Scalability**:
- MCP RAG server: <100ms query latency with FAISS
- LLM inference: ~5-15s per response (14B model on consumer GPU)
- Agent loop: 2-5 iterations typical for simple objectives

---

## 🛠️ Development

### Running Locally

```bash
# Install dependencies
pip install -r agent/requirements.txt

# Set environment variables
export MCP_URL="http://192.168.1.181:30800"
export LLM_URL="http://192.168.1.84:1234"
export TARGET="192.168.1.99"

# Run agent
python agent/redteam_agent.py
```

### Building Container

```bash
cd agent/
podman build -t redteam-agent-blackarch:v1 -f Dockerfile
```

### Testing MCP Server

```bash
curl http://192.168.1.181:30800/healthz
# Expected: {"status":"healthy","documents":5395,"techniques":327}

curl "http://192.168.1.181:30800/search?q=SSH%20brute%20force&top_k=3"
```

---

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Blue team agent (defensive monitoring)
- Additional attack scenarios
- Stealth metrics
- Multi-agent collaboration
- Custom exploit development by agent

See `CONTRIBUTING.md` for guidelines.

---

## 📄 License

MIT License - See `LICENSE` file

**Summary**: Free to use, modify, distribute with attribution.

**Attribution**: If you use this in research, please cite:
```
Autonomous Red Team AI Agent
https://github.com/[your-username]/autonomous-redteam-ai
First K8s-native offensive security framework with MCP RAG
October 2025
```

---

## 🙏 Acknowledgments

- **Qwen Team**: Qwen 2.5 Coder model
- **BlackArch Project**: 2000+ offensive security tools
- **MITRE**: ATT&CK framework
- **Atomic Red Team**: Adversary emulation techniques
- **GTFOBins**: Unix binary exploitation techniques
- **HackTricks**: Penetration testing playbooks
- **LM Studio**: Local LLM inference

---

## 📚 Further Reading

- `docs/ARCHITECTURE.md` - Detailed system design
- `docs/MCP-PROTOCOL.md` - MCP implementation details
- `docs/SAFETY.md` - Network isolation deep dive
- `docs/KNOWN-ISSUES.md` - Bug discoveries (LM Studio tool calling, etc.)
- `docs/RESEARCH-NOTES.md` - Inference parameters, abliteration effects

---

**Built**: October 2025
**Status**: Production-ready for security research
**Innovation**: World's first K8s-deployed autonomous red team agent
**Safety**: Fully isolated, documented, and tested

*From MCP protocol debugging to autonomous exploitation in one day.*
