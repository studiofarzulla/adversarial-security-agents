# Autonomous Red Team: Multi-Agent Adversarial Security Testing

**Kubernetes-native framework for autonomous adversarial security competition using LLMs**

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17614726-blue.svg)](https://doi.org/10.5281/zenodo.17614726)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Status](https://img.shields.io/badge/Status-Preprint-green.svg)](https://doi.org/10.5281/zenodo.17614726)

**Working Paper DAI-2513** | [Dissensus AI](https://dissensus.ai)

## Abstract

This technical report presents a framework for autonomous adversarial security competition using large language models (LLMs). We introduce a dual-agent architecture where autonomous red team and blue team agents compete in isolated environments: the red team attempts to compromise target systems while the blue team defends, detects, and remediates in real time. Phase 1 established the red team infrastructure -- a four-layer architecture combining LLM-guided decision making, retrieval-augmented generation (RAG) over offensive knowledge bases, containerized security toolkits, and kernel-level network isolation. Phase 2, presented in this updated report, introduces the blue team agent with a five-phase defensive methodology (Audit, Detect, Analyze, Remediate, Harden), an LLM-assisted patch generation framework with rollback support, and a competition scoring engine that evaluates red vs. blue performance across weighted security dimensions. Key architectural decisions include agent-orchestrated control flow (addressing limitations in abliterated models' structured output capabilities), NetworkPolicy-based isolation, command sandboxing with defensive tool whitelisting, and MITRE D3FEND integration for defensive knowledge retrieval. The red team agent achieves autonomous SSH compromise in approximately 90 seconds; the blue team agent implements a DefenseSandbox restricting operations to whitelisted defensive tools (auditd, fail2ban, iptables, lynis, rkhunter, chkrootkit, aide, ossec). The competition scoring framework evaluates time-to-compromise vs. time-to-detect, patch effectiveness, and stealth metrics. We describe the full implementation and discuss implications for autonomous security testing at scale.

## Key Findings

| Finding | Result |
|---------|--------|
| Red team speed | Autonomous SSH compromise in ~90 seconds |
| Knowledge base | 5,395 offensive security documents (GTFOBins, Atomic Red Team, HackTricks) |
| RAG latency | <100ms query latency (FAISS L2 search over 327 MITRE ATT&CK techniques) |
| Blue team tools | DefenseSandbox with 8 whitelisted defensive tools |
| Scoring dimensions | Time-to-compromise vs. time-to-detect, patch effectiveness, stealth metrics |
| Isolation | Kernel-level network enforcement via Kubernetes NetworkPolicy |

## Keywords

autonomous agents, adversarial AI, red team, blue team, LLM, RAG, Kubernetes, patch generation, scoring framework

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LLM Inference (Development Host)                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  LM Studio                                        │  │
│  │  • Model: qwen2.5-coder-14b-instruct-abliterated  │  │
│  │  • Optimized inference parameters                  │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Kubernetes Cluster (K3s)                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MCP RAG Server                                   │  │
│  │  • FAISS vector index (5,395 documents)           │  │
│  │  • Semantic search over offensive techniques      │  │
│  │  • MITRE ATT&CK technique mapping                 │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↑                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Red Team Agent Pod (ISOLATED)                    │  │
│  │  • BlackArch toolkit (2000+ security tools)       │  │
│  │  • Command sandbox (whitelist/blacklist)           │  │
│  │  • Repetition detection and fallback logic         │  │
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

### Implementation Status

**Phase 1: Red Team Infrastructure (Complete)**
- Autonomous attack agent with full decision-making capability
- MCP RAG server with offensive security knowledge base
- Kubernetes-native isolation and resource management

**Phase 2: Blue Team Development (Complete)**
- Autonomous defensive agent (Audit, Detect, Analyze, Remediate, Harden)
- LLM-assisted patch generation with rollback support
- Competition scoring framework (red vs. blue evaluation)
- MITRE D3FEND integration for defensive knowledge retrieval

**Phase 3: Ecosystem Integration (Planned)**
- Package repository hooks (npm, PyPI, AUR)
- Parallel competition execution at scale
- Distributed result aggregation

### Repository Structure

```
adversarial-security-agents/
├── agent/
│   ├── redteam_agent.py          # Main agent implementation
│   ├── Dockerfile                # BlackArch container image
│   └── requirements.txt          # Python dependencies
├── mcp-server/
│   ├── server.py                 # MCP RAG server implementation
│   ├── Dockerfile                # Server container image
│   └── deployment.yaml           # Kubernetes deployment manifest
├── k8s/
│   ├── agent-deployment.yaml     # Agent pod + NetworkPolicy
│   ├── deploy-agent.sh           # Deployment script
│   └── target-config.sh          # Target vulnerability setup
├── docs/
│   ├── ARCHITECTURE.md           # Detailed system design
│   ├── MCP-PROTOCOL.md           # MCP implementation details
│   ├── SAFETY.md                 # Network isolation documentation
│   ├── KNOWN-ISSUES.md           # Tool calling limitations, workarounds
│   └── CONFIGURATION.md          # Setup and configuration guide
├── examples/
│   ├── attack-scenarios/         # Example objectives
│   └── logs/                     # Sample agent output
└── README.md
```

## Getting Started

### Prerequisites

- Kubernetes cluster (K3s v1.33+ recommended)
- LM Studio with Qwen 2.5 Coder abliterated model
- Python 3.10+
- Target system with intentional vulnerabilities for testing

### Deployment

**1. Deploy MCP RAG Server**

```bash
cd mcp-server/
kubectl apply -f deployment.yaml
```

**2. Configure LM Studio**

- Load model: [`Qwen2.5-Coder-14B-Instruct-abliterated-GGUF`](https://huggingface.co/bartowski/Qwen2.5-Coder-14B-Instruct-abliterated-GGUF)
- Start server on port 1234
- Temperature: 0.4, Min-P: 0.08, Repeat Penalty: 1.08, Context: 16384

**3. Deploy Red Team Agent**

```bash
cd k8s/
./deploy-agent.sh
```

**4. Monitor Execution**

```bash
kubectl logs -f redteam-agent -n redteam-lab
```

### Local Testing

```bash
pip install -r agent/requirements.txt

export MCP_URL="http://<mcp-server>:30800"
export LLM_URL="http://<lm-studio>:1234"
export TARGET="<target-ip>"

python agent/redteam_agent.py
```

### Safety Guarantees

- **Network isolation**: Kubernetes NetworkPolicy enforces kernel-level egress rules
- **Command sandbox**: Whitelist/blacklist prevents destructive operations
- **Resource limits**: 1 CPU, 1GB RAM, non-root execution (UID 1000)
- **Ethical use only**: Only test systems you own or have explicit authorization to assess

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) -- System design and implementation
- [`docs/MCP-PROTOCOL.md`](docs/MCP-PROTOCOL.md) -- Model Context Protocol implementation
- [`docs/SAFETY.md`](docs/SAFETY.md) -- Network isolation and security analysis
- [`docs/KNOWN-ISSUES.md`](docs/KNOWN-ISSUES.md) -- Tool calling limitations and workarounds
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) -- Setup and deployment guide

## Citation

```bibtex
@techreport{farzulla2025redteam,
  author    = {Farzulla, Murad and Maksakov, Andrew},
  title     = {Autonomous Red Team: Multi-Agent Adversarial Security Testing},
  year      = {2025},
  institution = {Dissensus AI},
  type      = {Working Paper},
  number    = {DAI-2513},
  doi       = {10.5281/zenodo.17614726}
}
```

## Authors

- **Murad Farzulla** -- [Dissensus AI](https://dissensus.ai) & King's College London
  - ORCID: [0009-0002-7164-8704](https://orcid.org/0009-0002-7164-8704)
  - Email: murad@dissensus.ai
- **Andrew Maksakov** -- [Dissensus AI](https://dissensus.ai)

## License

Paper content: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | Code: [MIT](LICENSE)
