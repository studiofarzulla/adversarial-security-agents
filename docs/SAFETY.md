# Safety & Network Isolation

## NetworkPolicy Isolation

This agent uses Kubernetes NetworkPolicy for **declarative, kernel-level network isolation**. This is NOT application-level security - it's enforced by the Linux kernel via iptables/eBPF.

### What's Allowed

- ✅ Target machine (SSH port 22 only)
- ✅ MCP RAG server (ClusterIP service)
- ✅ LM Studio (port 1234)
- ✅ DNS (port 53)

### What's Blocked

- ❌ Internet (no 0.0.0.0/0 route)
- ❌ Other Kubernetes pods
- ❌ Other LAN hosts
- ❌ Kubernetes API server

### Command Sandbox

- Whitelist: 2000+ BlackArch tools approved
- Blacklist: Destructive patterns (`rm -rf /`, `dd`, `mkfs`, etc.)
- Logging: All commands recorded
- Non-root: Runs as UID 1000

### Testing Isolation

```bash
# Should FAIL (internet blocked)
kubectl exec redteam-agent -n redteam-lab -- curl https://google.com

# Should SUCCEED (MCP allowed)
kubectl exec redteam-agent -n redteam-lab -- curl http://mcp-rag-server.default.svc.cluster.local:8080/healthz
```

## Ethical Use

**This tool is for authorized security research ONLY.**

- Only attack systems you own or have written permission to test
- Use NetworkPolicy isolation to prevent unintended access
- Document all testing in controlled lab environments
- Do not exfiltrate data or cause destructive damage

**Legal disclaimer**: Unauthorized computer access is illegal. User assumes all responsibility for ethical use.
