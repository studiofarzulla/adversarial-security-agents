# Adversarial Security Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-v1.33+-blue.svg)](https://kubernetes.io/)

A Kubernetes-native framework for autonomous adversarial security testing, combining LLM-driven decision making with offensive security tooling and retrieval-augmented generation (RAG) knowledge bases.

**Project Status**: Experimental framework built over 48 hours (October 2025). This repository documents the implementation, technical decisions, challenges encountered, and lessons learned from deploying autonomous security agents on heterogeneous infrastructure.

## Overview

This project implements an autonomous red team agent deployed on Kubernetes for security testing research. The system combines:

- **LLM-guided decision making** using locally-hosted inference (Qwen 2.5 Coder)
- **RAG knowledge base** with 5,395 offensive security documents (GTFOBins, Atomic Red Team, HackTricks)
- **BlackArch toolkit** providing 2000+ offensive security tools in an isolated environment
- **Declarative network isolation** via Kubernetes NetworkPolicy

The agent autonomously queries the knowledge base, formulates attack strategies, executes commands, and adapts based on observed results—all while operating within strict network and resource constraints enforced at the kernel level.

## Research Context

This framework explores autonomous adversarial testing using dual-LLM methodology: separate red team and blue team agents with distinct knowledge bases competing in isolated environments.

### Motivation

Open-source security faces scalability challenges:
- Thousands of packages published daily across ecosystems (npm: 1.3M+, PyPI: 400K+, AUR: 85K+)
- Manual code review cannot scale to match publication velocity
- Vulnerabilities remain undiscovered for months or years
- Attackers maintain timing advantage in zero-day exploitation

### Approach: Dual-LLM Adversarial Competition

This framework tests a methodology where:

1. **Red Team Agent**: Autonomous attack execution with offensive security knowledge base
2. **Blue Team Agent** (planned): Defensive monitoring with hardening and patch generation capabilities
3. **Information Asymmetry**: Separate knowledge bases and objectives create realistic adversarial dynamics
4. **Automated Workflow**: Mirrors real-world bug bounty processes (discovery → reporting → patching → validation)

The hypothesis: dual-LLM adversarial competition with separate knowledge bases produces more realistic security testing than single-model approaches, while enabling automated patch deployment workflows similar to existing bug bounty systems.

### Vision

At scale with enterprise infrastructure (datacenters, large models, distributed execution), this methodology could enable:
- Automated vulnerability discovery in newly published packages
- Genuine zero-day identification before public exploitation
- Detection of human errors in security-critical code
- Shift from reactive patching to proactive vulnerability prevention

**Current Status**: This repository implements Phase 1 (red team infrastructure) to validate core technical feasibility.

### Current Implementation Status

**Phase 1: Red Team Infrastructure (COMPLETE)**
- Autonomous attack agent with full decision-making capability
- MCP RAG server with offensive security knowledge base
- Kubernetes-native isolation and resource management
- Physical hardware exploitation demonstration (SSH compromise)

**Phase 2: Blue Team Development (IN PROGRESS)**
- Defensive knowledge base (MITRE D3FEND, hardening guides)
- Patch generation capabilities
- Automated patch testing and validation
- Competition scoring framework

**Phase 3: Ecosystem Integration (PLANNED)**
- Package repository hooks (npm, PyPI, AUR)
- Parallel competition execution at scale
- Distributed result aggregation
- Public security scoring system

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│  LLM Inference (Development Host)                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  LM Studio                                         │  │
│  │  • Model: qwen2.5-coder-14b-instruct-abliterated │  │
│  │  • Optimized inference parameters                 │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Kubernetes Cluster (K3s)                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MCP RAG Server                                    │  │
│  │  • FAISS vector index (5,395 documents)           │  │
│  │  • Semantic search over offensive techniques      │  │
│  │  • MITRE ATT&CK technique mapping                 │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↑                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Red Team Agent Pod (ISOLATED)                    │  │
│  │  • BlackArch toolkit (2000+ security tools)       │  │
│  │  • Command sandbox (whitelist/blacklist)          │  │
│  │  • Repetition detection and fallback logic        │  │
│  │  • NetworkPolicy: Target + MCP + LLM + DNS only   │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Target System                                          │
│  • Intentionally vulnerable configuration               │
│  • Isolated attack surface for research                 │
└─────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**Agent-Orchestrated Pattern**: The agent controls the decision loop rather than relying on LLM function calling. This design choice emerged from discovering that abliterated (uncensored) models exhibit degraded performance with structured tool calling APIs. The agent-orchestrated approach provides greater transparency, easier debugging, and compatibility with uncensored models essential for security research.

**Knowledge Base Architecture**: The MCP (Model Context Protocol) server implements RAG over offensive security documentation, enabling semantic search across GTFOBins privilege escalation techniques, Atomic Red Team adversary emulation, and HackTricks penetration testing methodologies. FAISS indexing with L2 distance provides sub-100ms query latency.

**Network Isolation**: Kubernetes NetworkPolicy provides kernel-level enforcement of allowed traffic. The agent pod can only communicate with the designated target, MCP server, LLM inference endpoint, and DNS—preventing unintended lateral movement or internet access.

## Technical Approach

This framework tests whether autonomous agents with LLM decision-making can effectively conduct security testing in isolated environments. Key technical questions explored:

- Can LLMs reliably orchestrate offensive security tools through decision loops?
- Does RAG-enhanced context improve attack strategy formulation?
- How do abliterated (uncensored) models perform in structured tool-use scenarios?
- What isolation guarantees are needed for safe autonomous agent execution?

The implementation documents findings, architectural decisions, and discovered limitations.

## Quick Start

### Prerequisites

- Kubernetes cluster (K3s v1.33+ recommended)
- LM Studio with Qwen 2.5 Coder abliterated model
- Python 3.10+
- Target system with intentional vulnerabilities for testing

### Configuration

Before deployment, configure your infrastructure endpoints:

```bash
# Copy configuration template
cp config.template.yaml config.local.yaml

# Edit with your actual infrastructure IPs
vim config.local.yaml
```

See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for detailed configuration options.

### Deployment

**1. Deploy MCP RAG Server**

```bash
cd mcp-server/
kubectl apply -f deployment.yaml
```

**2. Configure LM Studio**

- Load model: [`Qwen2.5-Coder-14B-Instruct-abliterated-GGUF`](https://huggingface.co/bartowski/Qwen2.5-Coder-14B-Instruct-abliterated-GGUF)
  - Alternative: [`Qwen2.5-Coder-3B-Instruct-abliterated-GGUF`](https://huggingface.co/bartowski/Qwen2.5-Coder-3B-Instruct-abliterated-GGUF) (lower resource requirements)
- LM Studio version: 0.3.29 (Build 1) or later
- Start server on port 1234
- Configure inference parameters:
  - Temperature: 0.4 (deterministic command generation)
  - Min-P: 0.08 (dynamic sampling)
  - Repeat Penalty: 1.08 (prevents loops)
  - Context Length: 16384
  - Max Tokens: 2048
  - Cache Prompt: enabled (speeds up system prompt reuse)
- Configure performance optimizations:
  - Flash Attention: enabled
  - K/V Cache Quantization: Q8_0
  - Speculative Decoding: enabled
    - Min Draft Size: 4
    - Draft Probability Cutoff: 0.7
    - Max Draft Tokens: 10

**3. Deploy Red Team Agent**

```bash
cd k8s/
./deploy-agent.sh
```

**4. Monitor Execution**

```bash
kubectl logs -f redteam-agent -n redteam-lab
```

The agent will autonomously query the knowledge base, formulate attack strategies, and execute commands against the target.

## Repository Structure

```
adversarial-security-agents/
├── agent/
│   ├── redteam_agent.py          # Main agent implementation
│   ├── Dockerfile                 # BlackArch container image
│   └── requirements.txt           # Python dependencies
├── mcp-server/
│   ├── server.py                  # MCP RAG server implementation
│   ├── Dockerfile                 # Server container image
│   └── deployment.yaml            # Kubernetes deployment manifest
├── k8s/
│   ├── agent-deployment.yaml      # Agent pod + NetworkPolicy
│   ├── deploy-agent.sh            # Deployment script
│   └── target-config.sh           # Target vulnerability setup
├── docs/
│   ├── ARCHITECTURE.md            # Detailed system design
│   ├── MCP-PROTOCOL.md            # MCP implementation details
│   ├── SAFETY.md                  # Network isolation documentation
│   ├── KNOWN-ISSUES.md            # Tool calling limitations, workarounds
│   └── CONFIGURATION.md           # Setup and configuration guide
├── examples/
│   ├── attack-scenarios/          # Example objectives
│   └── logs/                      # Sample agent output
└── README.md                      # This file
```

## Key Features

### Autonomous Decision Making

The agent implements a complete OODA (Observe, Orient, Decide, Act) loop:

1. **Query knowledge base** for relevant offensive techniques
2. **Plan attack strategy** using LLM reasoning over retrieved context
3. **Execute commands** through sandboxed toolkit access
4. **Observe results** and adapt based on success/failure feedback
5. **Iterate** until objective achieved or maximum attempts reached

### Comprehensive Security Toolkit

Built on BlackArch Linux, the agent has access to 2000+ offensive security tools including:

- Password cracking: hydra, john, hashcat, medusa
- Network scanning: nmap, masscan, tcpdump
- Web assessment: sqlmap, nikto, dirb, gobuster
- Exploitation: metasploit, msfvenom
- Wireless: aircrack-ng
- Enumeration: enum4linux, smbclient

### Safety Guarantees

**Command Sandbox**: Multi-layer validation prevents destructive operations:
- Tool whitelist (2000+ approved security tools)
- Pattern blacklist (blocks destructive commands like `rm -rf /`, disk wiping)
- Execution logging with timestamps and exit codes

**Network Isolation**: Kubernetes NetworkPolicy enforces egress rules:
- Allowed: Target system, MCP server, LLM endpoint, DNS
- Blocked: Internet, other pods, Kubernetes API, other LAN hosts

**Resource Limits**: Pod-level constraints prevent resource exhaustion:
- 1 CPU maximum
- 1GB RAM maximum
- Non-root execution (UID 1000)
- Dropped capabilities
- RuntimeDefault seccomp profile

## Implementation Findings

This section documents technical discoveries and decisions made during development.

### LLM Tool Calling Behavior

**Observation**: Abliterated Qwen 2.5 Coder models produced grammar stack errors when using LM Studio's structured tool calling API during JSON generation.

**Hypothesis**: Weight modifications during abliteration may affect structured output reliability.

**Implementation**: Agent-orchestrated pattern with freeform text parsing. Low temperature (0.4) with optimized prompting for deterministic command extraction.

See `docs/KNOWN-ISSUES.md` for details.

### Sampling Strategy

**Observation**: Min-P sampling produced more reliable tool-use behavior than Top-P in testing.

Min-P dynamically adjusts token threshold based on top token probability:
- High confidence (top token 80%): Min-P 0.08 → keep tokens >6.4%
- Low confidence (top token 20%): Min-P 0.08 → keep tokens >1.6%

This adaptive behavior appeared to improve command generation consistency.

### Infrastructure Constraints

**Issue**: K3s containerd blocks `socketpair()` syscall, breaking async Python frameworks.

**Discovery**: FastAPI + Uvicorn failed even with Unconfined seccomp profiles due to socketpair dependency in asyncio initialization.

**Solution**: Flask + Gunicorn with synchronous workers avoids socketpair entirely.

**Takeaway**: Simpler technology stacks often have better compatibility in restricted execution environments.

### Agent Loop Design

**Challenge**: LLM could enter repetitive loops with the same failed command.

**Implementation**: Command history tracking with automatic fallback. If the same tool is used 3+ times consecutively, agent queries RAG for alternative techniques.

**Result**: Enables exploration of different attack vectors when initial approaches fail.

## Performance

**Typical Attack Timeline** (SSH compromise scenario):
- Iteration 1: Query RAG for "SSH brute force" → Execute hydra → Success
- Total time: ~90 seconds (including MCP queries and LLM inference)
- Commands executed: 1-3
- Success rate: 100% on intentionally vulnerable targets

**Scalability Metrics**:
- MCP RAG server: <100ms query latency (FAISS L2 search)
- LLM inference: 5-15s per response (14B model, consumer GPU)
- Agent loop: 2-5 iterations typical for simple objectives

## Responsible Use

### Ethical Guidelines

- **Authorized use only**: Only test systems you own or have explicit permission to assess
- **Isolated environments**: Use NetworkPolicy to prevent unintended access
- **Research scope**: Limited to authorized security testing and research
- **No data exfiltration**: Agent validates access without extracting sensitive information

### Safety Implementation

1. **Declarative isolation**: Kubernetes NetworkPolicy enforced at kernel level (not application level)
2. **Command sandbox**: Whitelist/blacklist prevents destructive operations
3. **Resource limits**: 1 CPU, 1GB RAM prevents denial of service
4. **Non-root execution**: Agent runs as UID 1000
5. **Dropped capabilities**: No privileged operations within container

### Target Configuration

The included `k8s/target-config.sh` creates an intentionally vulnerable system for research purposes with weak credentials, SUID binaries, and sudo misconfigurations.

**WARNING**: Never deploy this configuration on production systems.

## Development

### Local Testing

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

### Building Containers

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

## Contributing

Contributions are welcome. Areas of particular interest:

- Blue team agent development (defensive monitoring and patch generation)
- Additional attack scenarios and objectives
- Stealth metrics and detectability analysis
- Multi-agent collaboration patterns
- Automated exploit development capabilities

See `CONTRIBUTING.md` for guidelines.

## License

MIT License - See `LICENSE` file for details.

### Citation

If you use this framework in your research, please cite:

```
Adversarial Security Agents
https://github.com/studiofarzulla/adversarial-security-agents
Kubernetes-native autonomous red team framework with RAG-enhanced decision making
October 2025
```

## Acknowledgments

- **Qwen Team**: Qwen 2.5 Coder foundation models
- **Bartowski**: Abliterated model quantizations (GGUF format)
- **LM Studio**: Local LLM inference platform (v0.3.29+)
- **BlackArch Project**: Comprehensive offensive security toolkit
- **MITRE**: ATT&CK framework and D3FEND knowledge base
- **Atomic Red Team**: Adversary emulation testing library
- **GTFOBins**: Unix binary exploitation techniques
- **HackTricks**: Penetration testing methodologies

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - Detailed system design and implementation
- [`docs/SYSTEM-PROMPT.md`](docs/SYSTEM-PROMPT.md) - System prompt engineering and methodology
- [`docs/MCP-PROTOCOL.md`](docs/MCP-PROTOCOL.md) - Model Context Protocol implementation
- [`docs/SAFETY.md`](docs/SAFETY.md) - Network isolation and security analysis
- [`docs/KNOWN-ISSUES.md`](docs/KNOWN-ISSUES.md) - Tool calling limitations and workarounds
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) - Setup and deployment guide

---

**Status**: Experimental framework for autonomous security testing research
**Development**: October 2025 (48-hour rapid prototyping cycle)
**Focus**: Technical validation of dual-LLM adversarial methodology on heterogeneous infrastructure

**Note**: This repository documents the implementation, architecture, and technical findings from building autonomous security agents. Core components are functional for research purposes. The codebase serves as technical documentation of the approach, challenges encountered, and lessons learned.
