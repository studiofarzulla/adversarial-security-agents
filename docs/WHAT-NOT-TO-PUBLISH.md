# What NOT to Publish

This document lists sensitive information that should NEVER be committed to the public GitHub repository.

---

## ⛔ NEVER Commit These

### 1. **IP Addresses & Network Configuration**

❌ **Don't publish**:
- Your actual target IPs (192.168.1.99, etc.)
- Your K8s cluster IPs (192.168.1.181, etc.)
- Your LM Studio host IP (192.168.1.84)
- Your home network topology

✅ **Instead**:
- Use placeholders: `192.168.1.99` → `TARGET_IP`
- Use environment variables: `TARGET=${TARGET:-192.168.1.99}`
- Document in README: "Replace with your target IP"

**Files to sanitize**:
- `k8s/agent-deployment.yaml` - Replace IPs with env vars
- `k8s/deploy-agent.sh` - Use config file for IPs
- Documentation examples - Use `example.com`, `192.0.2.1` (RFC 5737 TEST-NET)

### 2. **Credentials & Passwords**

❌ **Don't publish**:
- SSH passwords (even weak ones like "password123")
- API keys
- Database credentials
- Kubernetes secrets
- LM Studio API tokens (if you add authentication)

✅ **Instead**:
- Document: "Configure weak password for testing: `victim:password123`"
- Use Kubernetes Secrets (not in manifest, create separately)
- Reference: "See target-config.sh for vulnerability setup"

**Files to check**:
- `k8s/target-config.sh` - Document process, don't hardcode passwords
- Any secret YAML files - Use `kubectl create secret` instead

### 3. **Command Logs with Sensitive Data**

❌ **Don't publish**:
- `/var/log/agent/commands.log` - May contain target-specific info
- Attack success logs - Could reveal your network
- Actual exploitation attempts

✅ **Instead**:
- Sanitized example logs in `examples/logs/`
- Replace real IPs with placeholders
- Redact any unique identifiers

### 4. **Large Binary Files**

❌ **Don't publish**:
- Container images (`.tar` files)
- FAISS indexes (`.faiss` files)
- Complete MCP document database (`documents.json` if >1MB)
- Compiled binaries

✅ **Instead**:
- Link to HuggingFace/DockerHub for images
- Provide build scripts instead of binaries
- Document how to generate indexes from source data

**Already in .gitignore**:
- `*.tar`, `*.faiss`, `mcp-server/data/`, `mcp-server/indexes/`

### 5. **Personal Information**

❌ **Don't publish**:
- Your full name (unless you want to)
- Your physical location
- Your employer (if doing this for work)
- Personal email addresses
- Phone numbers

✅ **Instead**:
- Use GitHub username in attribution
- Use GitHub email or create dedicated research email
- License under personal name OR organization name (your choice)

### 6. **Proprietary/Confidential Research**

❌ **Don't publish**:
- Client penetration test results (if you do professional work)
- Undisclosed vulnerabilities (0-days)
- Attack techniques against specific vendors (without disclosure)
- Anything under NDA

✅ **Instead**:
- Only publish techniques against your own lab
- Responsible disclosure for any real vulns found
- Generic techniques applicable to authorized testing only

---

## ✅ SAFE to Publish

### Code & Architecture

- ✅ Agent Python code (no hardcoded IPs/passwords)
- ✅ Dockerfile (BlackArch installation)
- ✅ Kubernetes manifests (with placeholder IPs)
- ✅ MCP server code
- ✅ System prompts
- ✅ Deployment scripts (with configurable IPs)

### Documentation

- ✅ Architecture diagrams (with generic IPs)
- ✅ Research findings (abliteration breaking tool calling)
- ✅ Inference parameter recommendations
- ✅ MCP protocol implementation details
- ✅ Known issues and workarounds
- ✅ Educational explanations

### Examples

- ✅ Sanitized attack scenarios
- ✅ Example objectives ("Gain SSH access using weak credentials")
- ✅ Sample MCP queries
- ✅ Redacted command logs

---

## 🔍 Pre-Commit Checklist

Before running `git push`, check:

1. [ ] No real IP addresses (use placeholders or env vars)
2. [ ] No passwords/credentials (even test ones in plain text)
3. [ ] No command logs with target-specific info
4. [ ] No large binary files (check with `git ls-files --stage | awk '$4 > 1048576'`)
5. [ ] No personal information you don't want public
6. [ ] All code has generic examples, not your specific setup
7. [ ] Documentation refers to "your network" not specific IPs

---

## 🛠️ Sanitization Tools

### Find potential IP addresses

```bash
grep -r "192\.168\." ~/autonomous-redteam-ai/ --exclude-dir=.git
```

### Find potential passwords

```bash
grep -ri "password\|passwd\|secret\|key" ~/autonomous-redteam-ai/ --exclude-dir=.git
```

### Check file sizes

```bash
find ~/autonomous-redteam-ai/ -type f -size +1M
```

---

## 📝 Recommended Sanitization

### For K8s Manifests

**Before**:
```yaml
env:
  - name: TARGET
    value: "192.168.1.99"  # ❌ Your actual IP
```

**After**:
```yaml
env:
  - name: TARGET
    value: "${TARGET_IP}"  # ✅ Placeholder, document in README
```

### For Deployment Scripts

**Before**:
```bash
TARGET="192.168.1.99"  # ❌ Hardcoded
```

**After**:
```bash
TARGET="${TARGET:-192.168.1.99}"  # ✅ Default with override
echo "Set TARGET env var to your vulnerable machine IP"
```

### For Documentation

**Before**:
```
Target: 192.168.1.99 (my old laptop)  # ❌ Specific
```

**After**:
```
Target: 192.168.1.99 (example - use your own vulnerable VM)  # ✅ Generic
```

---

## ⚖️ Legal Considerations

### What's Legal to Publish

✅ **Generic offensive security tools** - As long as they're educational
✅ **Techniques from public sources** - GTFOBins, Atomic Red Team, etc.
✅ **Your own research** - On your own infrastructure
✅ **Vulnerability exploitation** - Against intentionally vulnerable systems you own

### What's Risky

⚠️ **Exploits for specific vendors** - Coordinate with vendor first (responsible disclosure)
⚠️ **Automated exploitation** - Make safety guardrails VERY clear
⚠️ **Dual-use tools** - Document ethical use, authorized testing only

### Ethical Use Statement (Include in README)

Must have:
- "Authorized use only" warning
- "Isolated environment" requirement
- "Research purposes" disclaimer
- Safety guarantees documentation

**Already included in README.md** ✅

---

## 📤 Publishing Checklist

Before making repo public:

1. [ ] Review all code for hardcoded IPs/passwords
2. [ ] Replace specific IPs with environment variables
3. [ ] Add clear "Authorized use only" warnings
4. [ ] Document safety guarantees (NetworkPolicy, sandbox)
5. [ ] Remove any personal info you don't want public
6. [ ] Check `.gitignore` includes all sensitive file types
7. [ ] Test that deployment scripts work with placeholders
8. [ ] Add LICENSE (MIT recommended ✅)
9. [ ] Write clear README with quick start (✅)
10. [ ] Document known issues (abliteration bug ✅)

---

**Remember**: Once published, it's public forever. When in doubt, don't publish it.
