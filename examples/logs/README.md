# Execution Logs

This directory contains sanitized execution logs from agent runs demonstrating successful attack scenarios.

## Log Format

Logs are sanitized versions of actual agent output with:
- Real IP addresses replaced with placeholder IPs (192.168.1.99 → TARGET_IP)
- Timestamps normalized for clarity
- Sensitive information redacted
- Comments added for educational context

## Available Logs

### sample-ssh-compromise.log
Demonstrates successful SSH access via weak credentials (Scenario 01).

**Key Highlights**:
- Complete agent decision loop
- RAG query for SSH brute force techniques
- LLM reasoning and command generation
- Successful authentication in 1-2 iterations

**Metrics** (typical):
- Total time: ~30-45 seconds
- Iterations: 1-2
- RAG queries: 1-2
- Commands executed: 2-3

---

## Understanding the Logs

### Log Structure

Each agent iteration follows this pattern:

```
[ITERATION N]
├─ [RAG] Querying knowledge base: <query>
├─ [RAG] Found N relevant sources
├─ [LLM] Consulting decision engine...
├─ [LLM] Response received (X chars)
├─ [PLAN]: <LLM reasoning and command>
├─ [EXEC] Executing: <command>
├─ [OUTPUT]: <command output>
└─ [EXEC] Exit code: N
```

### Key Log Markers

| Marker | Meaning |
|--------|---------|
| `[AGENT]` | Agent initialization or status |
| `[RAG]` | RAG knowledge base query or result |
| `[LLM]` | LLM inference request or response |
| `[PLAN]` | LLM-generated attack plan |
| `[EXEC]` | Command execution |
| `[OUTPUT]` | Command stdout/stderr |
| `[MCP]` | MCP protocol communication |
| `[SUCCESS]` | Objective achieved |
| `[ERROR]` | Error occurred |
| `[WARN]` | Warning (repetition detected, etc.) |

### Example: Successful Iteration

```
[ITERATION 1]
[RAG] Querying knowledge base: SSH brute force weak password
[RAG] Found 3 relevant sources
[LLM] Consulting decision engine...
[LLM] Response received (342 chars)

[PLAN]:
**Reasoning**: Initial access via SSH using common credentials (MITRE ATT&CK T1078.003).
The knowledge base suggests using hydra for password guessing.
**Command**: `sshpass -p 'password123' ssh victim@192.168.1.99 whoami`
**Expected Outcome**: Successful SSH authentication with output showing username

[EXEC] Executing: sshpass -p 'password123' ssh victim@192.168.1.99 whoami
[OUTPUT]:
victim

[EXEC] Exit code: 0
[SUCCESS] Gained SSH access
```

### Example: Failed Iteration with Fallback

```
[ITERATION 1]
[RAG] Querying knowledge base: SSH access
[RAG] Found 3 relevant sources
[LLM] Consulting decision engine...

[PLAN]:
**Reasoning**: Try default SSH credentials
**Command**: `ssh admin@192.168.1.99`

[EXEC] Executing: ssh admin@192.168.1.99
[OUTPUT]:
Permission denied (publickey,password).

[EXEC] Exit code: 255

[ITERATION 2]
[RAG] Querying knowledge base: SSH brute force alternative methods
[RAG] Found 3 relevant sources
[LLM] Consulting decision engine...

[PLAN]:
**Reasoning**: Previous attempt failed. Try password-based brute force with hydra.
**Command**: `hydra -l victim -p password123 ssh://192.168.1.99`

[EXEC] Executing: hydra -l victim -p password123 ssh://192.168.1.99
[OUTPUT]:
[22][ssh] host: 192.168.1.99   login: victim   password: password123

[EXEC] Exit code: 0
[SUCCESS] Credentials discovered
```

## Metrics JSON Format

The agent produces detailed metrics in JSON format:

```json
{
  "start_time": 1696800000.0,
  "end_time": 1696800042.3,
  "total_runtime": 42.3,
  "total_iterations": 2,
  "commands_executed": 3,
  "commands_successful": 3,
  "commands_failed": 0,
  "commands_blocked": 0,
  "rag_queries": 2,
  "llm_calls": 4,
  "objectives_completed": 1,
  "objectives_failed": 0,
  "iteration_times": [15.2, 27.1],
  "success_rate": 100.0
}
```

## Collecting Your Own Logs

### Method 1: kubectl logs
```bash
# Stream live logs
kubectl logs -f redteam-agent -n redteam-lab

# Save to file
kubectl logs redteam-agent -n redteam-lab > agent-run-$(date +%Y%m%d-%H%M%S).log
```

### Method 2: Command Log File
```bash
# From within agent pod
kubectl exec redteam-agent -n redteam-lab -- cat /var/log/agent/commands.log
```

### Method 3: Metrics JSON
```bash
# Extract metrics JSON
kubectl exec redteam-agent -n redteam-lab -- cat /var/log/agent/metrics.json
```

## Sanitization Guidelines

Before committing logs to repository:

1. **Replace sensitive IPs**:
   ```
   192.168.1.99 → TARGET_IP
   192.168.1.84 → LLM_HOST
   192.168.1.181 → MCP_SERVER
   ```

2. **Remove sensitive output**:
   - Password hashes
   - SSH keys
   - Session tokens
   - Actual vulnerability details (if real CVE)

3. **Normalize timestamps**:
   - Use relative time (T+0s, T+15s, etc.)
   - Or normalize to epoch 0 for clarity

4. **Add context comments**:
   ```
   # Agent recognized weak credentials from RAG query
   [LLM] Response received (342 chars)
   ```

## Note on Reproducibility

These logs represent actual agent behavior but:
- LLM responses may vary between runs (even at temp=0.4)
- RAG query results depend on index state
- Timing varies based on infrastructure load
- Target configuration must match scenario exactly

For reproducible testing, see `examples/attack-scenarios/` for step-by-step methodology.

## Contributing Logs

To contribute execution logs:

1. Run agent against documented scenario
2. Capture full output (kubectl logs)
3. Sanitize sensitive information
4. Add comments explaining key decisions
5. Include metrics JSON
6. Submit pull request with:
   - Sanitized log file
   - Scenario reference
   - Metrics summary

See `CONTRIBUTING.md` for detailed guidelines.
