# Attack Scenarios

This directory contains documented attack scenarios for testing the autonomous red team agent. Each scenario includes:

- MITRE ATT&CK technique mapping
- Target configuration requirements
- Step-by-step attack methodology
- Expected timeline and success criteria
- Defensive countermeasures
- Agent performance metrics

## Available Scenarios

### 01-ssh-weak-credentials.md
**Objective**: Gain initial SSH access via weak credentials
**Difficulty**: Beginner
**MITRE ATT&CK**: T1078.003 (Valid Accounts - Local Accounts)
**Prerequisites**: None (initial access scenario)
**Expected Duration**: 30-45 seconds

**Use Case**: Tests agent's ability to:
- Perform network reconnaissance
- Query RAG for authentication attack techniques
- Execute password-based authentication
- Verify successful access

---

### 02-privilege-escalation-suid.md
**Objective**: Escalate from user to root via SUID binaries
**Difficulty**: Intermediate
**MITRE ATT&CK**: T1548.001 (Abuse Elevation Control - SUID/SGID)
**Prerequisites**: Initial access as `victim` user
**Expected Duration**: 15-35 seconds

**Use Case**: Tests agent's ability to:
- Enumerate system for privilege escalation vectors
- Query GTFOBins via RAG for exploitation techniques
- Apply retrieved techniques to gain root access
- Verify privilege escalation success

---

## Using These Scenarios

### Running a Scenario

**1. Configure Target** (using `k8s/target-config.sh`):
```bash
# On target machine (192.168.1.99)
ssh root@192.168.1.99 'bash -s' < k8s/target-config.sh
```

**2. Update Agent Objective** (in `agent/redteam_agent.py`):
```python
scenarios = [
    "Gain SSH access to 192.168.1.99 using weak credentials",
    # or
    "Escalate privileges to root using SUID binaries"
]
```

**3. Deploy and Monitor**:
```bash
# Deploy agent
kubectl apply -f k8s/agent-deployment.yaml

# Watch execution
kubectl logs -f redteam-agent -n redteam-lab
```

### Evaluating Results

Each scenario document includes **Success Criteria** checklist. Agent performance is considered successful if:

- All success criteria are met
- Execution time within expected duration
- No errors in command execution (or appropriate fallback triggered)
- Correct MITRE ATT&CK techniques referenced in reasoning

### Performance Metrics

Track these metrics for each scenario run:

| Metric | Description |
|--------|-------------|
| **Total Time** | Start to completion (seconds) |
| **Iterations** | Number of agent decision loops |
| **RAG Queries** | Times knowledge base was queried |
| **LLM Calls** | Times LLM was invoked for decision making |
| **Commands Executed** | Total commands run |
| **Success Rate** | Commands successful / total commands |
| **Blocked Commands** | Commands blocked by sandbox |

Example metrics JSON (from `agent/redteam_agent.py`):
```json
{
  "total_runtime": 42.3,
  "total_iterations": 2,
  "rag_queries": 2,
  "llm_calls": 4,
  "commands_executed": 3,
  "commands_successful": 3,
  "commands_failed": 0,
  "commands_blocked": 0,
  "objectives_completed": 1,
  "objectives_failed": 0
}
```

## Scenario Development Guidelines

When creating new scenarios:

### Required Sections
1. **Objective**: Clear, measurable goal
2. **MITRE ATT&CK Mapping**: Tactic + Technique + Sub-technique
3. **Prerequisites**: What must be completed first
4. **Target Configuration**: How to set up vulnerable target
5. **Attack Methodology**: Step-by-step phases
6. **Expected Timeline**: Realistic duration estimate
7. **Success Criteria**: Checkable completion requirements
8. **Agent Performance Metrics**: Expected agent behavior
9. **Defensive Countermeasures**: Detection and prevention methods
10. **References**: Links to MITRE ATT&CK, GTFOBins, Atomic Red Team

### Methodology Format
Follow the 5-phase structure from `docs/SYSTEM-PROMPT.md`:

1. **Phase 1: Reconnaissance** - Identify attack surface
2. **Phase 2: Vulnerability Identification** - Find exploitable weakness
3. **Phase 3: Initial Access** (or Exploitation) - Gain access
4. **Phase 4: Privilege Escalation** - Elevate privileges (if applicable)
5. **Phase 5: Post-Exploitation** - Verify success, document results

### Difficulty Levels

- **Beginner**: Single-phase attack, well-documented techniques, high success rate
- **Intermediate**: Multi-phase attack, requires RAG queries, moderate success rate
- **Advanced**: Complex multi-step exploitation, requires adaptation, lower success rate
- **Expert**: Novel techniques, limited documentation, requires creativity

## Future Scenarios (Planned)

### 03-lateral-movement.md
Multi-host environment, moving from compromised host to adjacent systems.

### 04-web-application-sqli.md
SQL injection against vulnerable web application.

### 05-privilege-escalation-kernel.md
Kernel exploit for privilege escalation (CVE-based).

### 06-password-cracking-hashcat.md
Hash extraction and offline cracking with hashcat.

### 07-network-pivoting.md
Using compromised host as pivot point for internal network access.

### 08-stealth-techniques.md
Minimize detection footprint, log cleanup, anti-forensics.

## Contributing

To contribute a new scenario:

1. Fork the repository
2. Create scenario markdown file following template above
3. Test scenario with agent (document actual vs. expected performance)
4. Submit pull request with:
   - Scenario markdown file
   - Sample execution log
   - Target configuration script (if custom setup needed)

See `CONTRIBUTING.md` for detailed guidelines.

## References

- MITRE ATT&CK Framework: https://attack.mitre.org/
- Atomic Red Team: https://github.com/redcanaryco/atomic-red-team
- GTFOBins: https://gtfobins.github.io/
- HackTricks: https://book.hacktricks.xyz/
- System Prompt Methodology: `docs/SYSTEM-PROMPT.md`
