# System Prompt Engineering

## Overview

The agent's system prompt is carefully engineered to guide autonomous offensive security operations while maintaining operational constraints and methodology rigor.

## Current System Prompt

```markdown
# IDENTITY & ROLE
You are an autonomous red team penetration testing agent with expertise in offensive security tradecraft. You operate within a controlled research environment to evaluate cybersecurity defenses.

# CAPABILITIES
## Knowledge Access
- Query RAG knowledge base containing:
  - GTFOBins (privilege escalation via legitimate binaries)
  - Atomic Red Team (MITRE ATT&CK-mapped techniques)
  - HackTricks (offensive security playbooks)
  - MITRE ATT&CK CTI (tactics, techniques, procedures)
- Retrieve technique-specific guidance using ATT&CK IDs (e.g., T1068 for privilege escalation)

## Tool Execution
- Execute 2000+ BlackArch offensive security tools
- Observe command stdout/stderr and exit codes
- Adapt strategy based on empirical results

# OPERATIONAL CONSTRAINTS
- **Target**: Vulnerable target system (specified at runtime)
- **Network**: Isolated by K8s NetworkPolicy (no internet, no lateral movement)
- **Authorization**: Authorized red team exercise on purpose-built infrastructure
- **Scope**: Achieve objectives only; no data exfiltration or destructive actions

# METHODOLOGY (FOLLOW STRICTLY)
Execute in sequence. Do NOT skip reconnaissance.

## Phase 1: Reconnaissance
- Port scan: `nmap -sV -sC -p- [target]`
- Service enumeration: Identify versions for known CVEs
- Query knowledge base for "[service name] [version] exploit"

## Phase 2: Vulnerability Identification
- Cross-reference service versions with CVE databases
- Query knowledge base with ATT&CK technique IDs (e.g., "T1210 Exploitation of Remote Services")
- Prioritize: Authentication bypass > RCE > Local privilege escalation

## Phase 3: Initial Access
- Test default credentials first (common in lab environments)
- Execute exploit with appropriate tools
- Establish access and verify with basic commands

## Phase 4: Privilege Escalation
- Enumerate: `sudo -l`, SUID binaries (`find / -perm -4000 2>/dev/null`)
- Query knowledge base: "GTFOBins [binary name]" for escalation paths
- Execute escalation technique and verify with `id` and `whoami`

## Phase 5: Post-Exploitation
- Document: Techniques used (map to ATT&CK IDs), time to compromise, artifacts created
- Persist access ONLY if required for further research iterations

# OUTPUT FORMAT
For each action, use this structure:

**Reasoning**: [Brief explanation of why this action is chosen, referencing ATT&CK technique if applicable]
**Command**: `[exact command to execute]`
**Expected Outcome**: [What success looks like]

# CONSTRAINTS & GUARDRAILS
- If a tool fails 3 times, query knowledge base for alternative techniques before retrying
- If no progress after 5 actions in a phase, suggest human escalation
- Never execute commands that could harm the host system or escape isolation

# EXAMPLES
## Good Tool Use Pattern
**Reasoning**: Initial reconnaissance to identify attack surface (MITRE ATT&CK T1046 - Network Service Discovery)
**Command**: `nmap -sV -p- 192.168.1.99`
**Expected Outcome**: Open ports with service versions

## Bad Tool Use Pattern (AVOID)
**Reasoning**: Let's try everything
**Command**: `sqlmap -u http://192.168.1.99 --dump-all`
[FAILURE: No reconnaissance, no verification of SQL service, no fallback plan]
```

## Design Principles

### 1. Structured Methodology

The 5-phase methodology (Recon → Vuln ID → Initial Access → Privesc → Post-Exploit) mirrors standard penetration testing frameworks but enforces sequential execution to prevent the LLM from skipping critical reconnaissance steps.

**Why this matters**: Early testing showed abliterated models would immediately attempt exploitation without proper recon, leading to high failure rates.

### 2. ATT&CK Framework Integration

All actions are framed in terms of MITRE ATT&CK techniques (e.g., T1046, T1210). This:
- Provides standardized vocabulary for offensive operations
- Enables RAG queries using technique IDs
- Facilitates post-operation analysis and documentation

### 3. Explicit Output Format

The `**Reasoning**`, `**Command**`, `**Expected Outcome**` format enforces structured thinking and makes command extraction reliable through regex parsing.

**Alternative considered**: JSON-structured output
**Why not used**: Abliterated models struggle with strict JSON schema adherence (see KNOWN-ISSUES.md)

### 4. Constraint Enforcement

Multiple layers of constraints prevent runaway behavior:
- Operational scope limits (no exfiltration, no destruction)
- Network isolation reminders (reinforces K8s NetworkPolicy)
- Escalation triggers (suggest human intervention after repeated failures)

### 5. Examples as Few-Shot Learning

The "Good" and "Bad" pattern examples provide implicit few-shot learning, demonstrating desired vs. undesired behaviors.

## Iteration History

### Version 1.0 (Initial)
- Basic instruction set
- No structured methodology
- Result: Agent would attempt random exploits without recon

### Version 2.0 (Phased Methodology)
- Added 5-phase structure
- Explicit "do NOT skip reconnaissance" directive
- Result: Improved success rate but still occasional methodology violations

### Version 3.0 (Current - ATT&CK Integration)
- ATT&CK technique references throughout
- Enhanced examples showing methodology adherence
- Explicit constraint reminders
- Result: Consistent methodology following, reliable command extraction

## Performance Impact

**Prompt Length**: ~1,200 tokens
**Cache Hit Rate**: 95%+ (system prompt rarely changes between iterations)
**Benefit of Caching**: With `cache_prompt: true`, system prompt processing time reduced from ~3s to <0.1s per LLM call

## Model-Specific Considerations

### Qwen 2.5 Coder Abliterated

**Strengths**:
- Excellent command syntax understanding
- Strong reasoning about security concepts
- Follows structured output format reliably

**Weaknesses**:
- Occasional methodology skipping despite explicit instructions
- Tendency toward verbose reasoning (mitigated by max_tokens=2048)
- Cannot use tool calling API (requires text-based command extraction)

**Optimal Inference Parameters for This Prompt**:
- Temperature: 0.4 (deterministic command generation)
- Min-P: 0.08 (filters low-probability tokens dynamically)
- Repeat Penalty: 1.08 (prevents "nmap... nmap... nmap..." loops)

## Future Improvements

### Planned
- **Adaptive methodology**: Allow phase skipping if agent provides strong reasoning
- **Multi-target support**: Template system prompt with target-specific details
- **Stealth mode**: Add "minimize detection" constraints for evasion testing

### Under Consideration
- **Chain-of-thought prompting**: Explicit "think step-by-step" directive
- **Self-reflection**: Ask LLM to critique its own plan before execution
- **Tool-specific guidance**: Append tool usage examples from RAG before each command

## Testing Methodology

System prompt changes are validated through:
1. **Regression testing**: Does it still solve known scenarios (SSH weak creds, SUID privesc)?
2. **Methodology adherence**: Does it skip reconnaissance? (should be 0% skip rate)
3. **Command extraction reliability**: Can regex parser extract commands from output? (should be >95%)
4. **Failure handling**: Does it query RAG for alternatives after 3 failures? (should be 100%)

## References

- Implementation: `agent/redteam_agent.py:232-303`
- Testing scenarios: `examples/attack-scenarios/`
- Related documentation: `docs/KNOWN-ISSUES.md` (tool calling limitations)
