# Configuration Guide

## Overview

This project uses a **layered configuration system** for maximum flexibility and security:

1. **`config.template.yaml`** - Template with all options documented (committed to git)
2. **`config.example.yaml`** - Safe example with RFC 5737 TEST-NET IPs (committed to git)
3. **`config.local.yaml`** - Your actual lab configuration (gitignored, never committed)

`★ Insight ─────────────────────────────────────`
**Why this approach is elegant:**
- Template shows all available options with comments
- Example is safe for public repo (documentation IPs)
- Local config is gitignored (your real IPs never leak)
- No risk of accidentally committing secrets
`─────────────────────────────────────────────────`

---

## Quick Start

### 1. Create Your Local Config

```bash
# Copy template
cp config.template.yaml config.local.yaml

# Edit with your actual IPs
vim config.local.yaml  # or nano, code, etc.
```

### 2. Customize for Your Lab

Replace the example IPs with your actual infrastructure:

```yaml
target:
  ip: "192.168.1.99"  # Your vulnerable VM

llm:
  url: "http://192.168.1.84:1234"  # Your LM Studio host

mcp:
  external_url: "http://192.168.1.181:30800"  # Your K8s node IP
```

### 3. Verify Config

```bash
# Check that config exists and is valid YAML
python3 -c "import yaml; yaml.safe_load(open('config.local.yaml'))"

# Make sure it's gitignored
git status  # Should NOT show config.local.yaml
```

---

## Configuration Sections

### Target Configuration

```yaml
target:
  ip: "192.168.1.99"          # Vulnerable machine IP
  port: 22                     # SSH port
  description: "Lab target"    # For your reference
```

**Used by:**
- Agent to determine attack target
- NetworkPolicy for egress rules
- Deployment scripts

### LLM Configuration

```yaml
llm:
  url: "http://192.168.1.84:1234"
  model: "qwen2.5-coder-14b-instruct-abliterated"

  inference:
    temperature: 0.4        # Low = deterministic commands
    min_p: 0.08             # Dynamic sampling threshold
    top_p: 1.0              # Disabled when using min_p
    top_k: 0                # Disabled
    repeat_penalty: 1.08    # Prevent repetition
    max_tokens: 2048
    stream: false
    cache_prompt: true
```

**Inference parameters explained:**
- `temperature: 0.4` - Lower = more focused, deterministic outputs
- `min_p: 0.08` - Keeps tokens with P ≥ 8% of top token (adaptive)
- `repeat_penalty: 1.08` - Slight penalty prevents "nmap... nmap... nmap..."

### MCP RAG Server

```yaml
mcp:
  internal_url: "http://mcp-rag-server.default.svc.cluster.local:8080"
  external_url: "http://192.168.1.181:30800"
  top_k: 3      # Number of documents to retrieve
  timeout: 30   # Query timeout (seconds)
```

**Internal vs External:**
- `internal_url`: Used by agent running **inside** K8s cluster
- `external_url`: Used for testing **from your PC**

### Agent Behavior

```yaml
agent:
  max_iterations: 5           # Max attempts per objective
  command_timeout: 30         # Seconds before command times out
  repetition_window: 3        # Check last N commands for loops
  log_file: "/var/log/agent/commands.log"
  max_output_length: 1024     # Chars sent to LLM (prevent context overflow)
```

**Tuning tips:**
- Increase `max_iterations` for complex objectives (10-20)
- Decrease `command_timeout` if tools hang (15s)
- Increase `max_output_length` for detailed error messages (2048)

### Kubernetes Resources

```yaml
kubernetes:
  namespace: "redteam-lab"
  resources:
    cpu: "1"
    memory: "1Gi"
  security:
    run_as_user: 1000
    run_as_non_root: true
    allow_privilege_escalation: false
```

**Resource tuning:**
- BlackArch container uses ~500MB base
- Increase CPU to "2" for faster tool execution
- Increase memory to "2Gi" if running large exploits

### NetworkPolicy

```yaml
network_policy:
  egress:
    - ip: "192.168.1.99"
      port: 22
      protocol: "TCP"
      description: "SSH to target"

    - ip: "192.168.1.84"
      port: 1234
      protocol: "TCP"
      description: "LLM inference"
```

**Adding targets:**
```yaml
# Multiple targets
- ip: "192.168.1.100"
  port: 22
  description: "Second target"

- ip: "192.168.1.101"
  port: 80
  description: "Web app target"
```

### Attack Scenarios

```yaml
scenarios:
  - name: "SSH Brute Force"
    description: "Gain SSH access using weak credentials"
    enabled: true

  - name: "Privilege Escalation"
    description: "Escalate to root"
    enabled: false
```

**Enable/disable scenarios:**
- Agent will run enabled scenarios sequentially
- Disable complex scenarios during development
- Add custom scenarios as YAML entries

---

## Using Config in Scripts

### Python (Agent Code)

```python
import yaml
import os

# Load config with fallback to template
config_file = "config.local.yaml" if os.path.exists("config.local.yaml") else "config.template.yaml"

with open(config_file) as f:
    config = yaml.safe_load(f)

# Access config
target_ip = config['target']['ip']
llm_url = config['llm']['url']
max_iterations = config['agent']['max_iterations']
```

### Bash (Deployment Scripts)

```bash
# Extract values using yq or python
TARGET_IP=$(python3 -c "import yaml; print(yaml.safe_load(open('config.local.yaml'))['target']['ip'])")
LLM_URL=$(python3 -c "import yaml; print(yaml.safe_load(open('config.local.yaml'))['llm']['url'])")

# Use in kubectl
kubectl set env deployment/redteam-agent TARGET=$TARGET_IP LLM_URL=$LLM_URL
```

---

## Environment Variable Overrides

Config can be overridden by environment variables (highest priority):

```bash
# Override target IP
export TARGET_IP="192.168.1.200"

# Override LLM URL
export LLM_URL="http://192.168.1.50:1234"

# Run agent with overrides
python agent/redteam_agent.py
```

**Priority order:**
1. Environment variables (highest)
2. `config.local.yaml` (if exists)
3. `config.template.yaml` (fallback)
4. Hardcoded defaults in code (lowest)

---

## Security Best Practices

### ✅ DO

- Copy `config.template.yaml` to `config.local.yaml` immediately
- Keep real IPs only in `config.local.yaml`
- Verify `config.local.yaml` is in `.gitignore`
- Use environment variables for CI/CD

### ❌ DON'T

- Never commit `config.local.yaml`
- Don't put real IPs in `config.template.yaml` or `config.example.yaml`
- Don't hardcode IPs in Python/Shell scripts
- Don't share `config.local.yaml` (contains your network topology)

### Verify Safety

```bash
# Check what's tracked by git
git ls-files | grep config

# Should show:
#   config.template.yaml  ✅
#   config.example.yaml   ✅
#
# Should NOT show:
#   config.local.yaml     ❌ (gitignored!)

# Check for accidental IP commits
git log --all --source --full-history -S '192.168.1.99'
```

---

## Troubleshooting

### "Config file not found"

```bash
# Agent looks for config.local.yaml first
ls config.local.yaml

# If missing, create it
cp config.template.yaml config.local.yaml
```

### "Invalid YAML syntax"

```python
# Validate YAML
python3 << EOF
import yaml
try:
    yaml.safe_load(open('config.local.yaml'))
    print("✅ Valid YAML")
except yaml.YAMLError as e:
    print(f"❌ YAML Error: {e}")
EOF
```

### "Config.local.yaml showing in git status"

```bash
# Check .gitignore
grep config.local.yaml .gitignore

# If missing, add it
echo "config.local.yaml" >> .gitignore

# Remove from git if already tracked
git rm --cached config.local.yaml
git commit -m "Stop tracking config.local.yaml"
```

---

## Advanced: Multiple Environments

For complex setups (dev, staging, prod labs):

```bash
# Create environment-specific configs
config.dev.yaml    # Development lab
config.staging.yaml  # Staging environment
config.prod.yaml   # Production red team lab

# Add all to .gitignore
echo "config.*.yaml" >> .gitignore

# Use with env var
export CONFIG_ENV=dev
python agent/redteam_agent.py --config "config.${CONFIG_ENV}.yaml"
```

---

**Document Version**: 1.0
**Last Updated**: October 9, 2025
**Status**: Configuration system implemented
