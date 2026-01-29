#!/usr/bin/env python3
"""
Autonomous Blue Team Agent - Defensive Security Edition
Monitors, detects, and remediates security vulnerabilities and active attacks.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from common import MCPClient, LLMClient
from patch_generator import PatchGenerator


class DefenseSandbox:
    """Sandboxed command execution with defensive security tools"""

    WHITELIST = [
        # Monitoring & detection
        'auditctl', 'ausearch', 'aureport',
        'ss', 'netstat', 'lsof', 'ps', 'top',
        'tcpdump', 'tshark',
        'journalctl', 'dmesg',
        'last', 'lastb', 'lastlog', 'who', 'w',

        # Integrity & scanning
        'aide', 'rkhunter', 'chkrootkit', 'lynis',
        'tripwire',
        'clamscan', 'freshclam',

        # Hardening & remediation
        'iptables', 'ip6tables', 'nft',
        'fail2ban-client',
        'systemctl', 'service',
        'chmod', 'chown', 'chattr',
        'passwd', 'usermod', 'userdel',
        'visudo',

        # File inspection
        'cat', 'head', 'tail', 'grep', 'awk', 'sed',
        'find', 'ls', 'stat', 'file', 'diff',
        'md5sum', 'sha256sum',
        'strings', 'xxd',

        # System info
        'id', 'whoami', 'uname', 'hostname',
        'df', 'du', 'mount',
        'sysctl',

        # Network tools (defensive use)
        'nmap', 'ping', 'traceroute', 'dig', 'host',
        'curl', 'wget',

        # Package management (for patching)
        'apt', 'apt-get', 'dpkg',
        'pacman', 'yum', 'dnf',

        # Basic utilities
        'python3', 'python', 'bash', 'sh',
        'echo', 'pwd', 'which', 'whereis',
        'base64', 'date', 'wc', 'sort', 'uniq', 'tee',
        'ssh', 'scp',
    ]

    BLACKLIST_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'dd\s+if=.*of=/dev/',
        r':[(][)]',
        r'>\s*/dev/sd',
        r'mkfs',
        r'shutdown',
        r'reboot',
        r'init\s+0',
    ]

    def __init__(self, log_file: str = "/var/log/agent/defense_commands.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def is_safe(self, command: str) -> Tuple[bool, str]:
        """Check if command is safe to execute"""
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False, "Empty command"

        base_cmd = cmd_parts[0].split('/')[-1]

        if base_cmd not in self.WHITELIST:
            return False, f"Command '{base_cmd}' not in defensive whitelist"

        for pattern in self.BLACKLIST_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked pattern: {pattern}"

        return True, "OK"

    def execute(self, command: str, timeout: int = 30) -> Tuple[str, int]:
        """Execute command with safety checks and logging"""
        safe, reason = self.is_safe(command)
        if not safe:
            self.log(command, blocked=True, reason=reason)
            return f"BLOCKED: {reason}", -1

        self.log(command)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                text=True
            )

            self.log(command, output=result.stdout, stderr=result.stderr, code=result.returncode)
            return result.stdout, result.returncode

        except subprocess.TimeoutExpired:
            msg = f"[TIMEOUT] Command exceeded {timeout}s"
            self.log(command, output=msg, code=-2)
            return msg, -2

        except Exception as e:
            msg = f"ERROR: {str(e)}"
            self.log(command, output=msg, code=-3)
            return msg, -3

    def log(self, command: str, output: str = "", stderr: str = "", code: int = 0,
            blocked: bool = False, reason: str = ""):
        """Log command execution"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "command": command,
            "blocked": blocked,
            "reason": reason,
            "output": output[:1024] if output else "",
            "stderr": stderr[:512] if stderr else "",
            "return_code": code
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')


class BlueTeamAgent:
    """Autonomous defensive security agent"""

    SYSTEM_PROMPT = """# IDENTITY & ROLE
You are an autonomous blue team defensive security agent. You protect systems by detecting vulnerabilities, monitoring for attacks, and applying security hardening measures.

# CAPABILITIES
## Knowledge Access
- Query RAG knowledge base containing:
  - MITRE D3FEND (defensive techniques taxonomy)
  - CIS Benchmarks (system hardening guidelines)
  - NIST SP 800-53 (security controls)
  - Linux hardening guides and best practices

## Tool Execution
- Execute defensive security tools (auditd, fail2ban, lynis, rkhunter, aide, etc.)
- Inspect system configurations and file permissions
- Apply hardening patches and configuration fixes
- Monitor network connections and process activity

# OPERATIONAL CONSTRAINTS
- **Target**: System to defend (configured via environment)
- **Network**: Isolated by K8s NetworkPolicy
- **Authorization**: Authorized defensive exercise on purpose-built infrastructure
- **Scope**: Detect, harden, and patch only; do not disrupt legitimate services

# METHODOLOGY (FOLLOW STRICTLY)
Execute in sequence. Be thorough but non-destructive.

## Phase 1: Audit & Baseline
- Run system audit: `lynis audit system --quick`
- Check listening services: `ss -tlnp`
- Enumerate users: `cat /etc/passwd | grep -v nologin`
- Check SUID binaries: `find / -perm -4000 2>/dev/null`
- Review sudo config: `cat /etc/sudoers`
- Check SSH config: `cat /etc/ssh/sshd_config`

## Phase 2: Vulnerability Detection
- Identify weak SSH configurations (password auth enabled, root login allowed)
- Find unnecessary SUID binaries
- Detect sudo misconfigurations (dangerous commands allowed)
- Check file permission issues (world-writable files, insecure cron jobs)
- Scan for rootkits: `rkhunter --check --skip-keypress`

## Phase 3: Threat Analysis
- Map findings to MITRE ATT&CK techniques (what could an attacker exploit?)
- Map defenses to MITRE D3FEND (what defensive technique applies?)
- Prioritize: Critical (remote access) > High (privilege escalation) > Medium (persistence)

## Phase 4: Remediation
- Generate patches for identified vulnerabilities
- Apply patches with rollback capability
- Validate that patches resolve the vulnerability without breaking services

## Phase 5: Hardening & Monitoring
- Apply defense-in-depth measures
- Configure monitoring (auditd rules, fail2ban jails)
- Document all changes with before/after state

# OUTPUT FORMAT
For each action, use this structure:

**Finding**: [Description of vulnerability or security issue]
**D3FEND Technique**: [MITRE D3FEND ID and name if applicable]
**Command**: `[exact command to execute]`
**Expected Outcome**: [What success looks like]

# CONSTRAINTS & GUARDRAILS
- Always create rollback commands before applying changes
- Never disable services without confirming they are not legitimate
- If unsure whether a finding is a real vulnerability, flag it for review
- Prioritize detection accuracy over speed (avoid false positives)

# EXAMPLES
## Good Defensive Pattern
**Finding**: SSH allows password authentication (weak credential attack vector)
**D3FEND Technique**: D3-MAN (Multi-factor Authentication)
**Command**: `grep -n "PasswordAuthentication" /etc/ssh/sshd_config`
**Expected Outcome**: Shows current SSH password auth setting

## Bad Defensive Pattern (AVOID)
**Finding**: Something looks wrong
**Command**: `iptables -F`
[FAILURE: Flushing all firewall rules without backup is destructive]"""

    def __init__(self, mcp_url: str, llm_url: str, llm_model: str, target: str):
        print("[AGENT] Initializing Blue Team Agent (Defensive Edition)...")
        self.mcp = MCPClient(mcp_url, client_name="blueteam-agent", client_version="1.0.0")
        self.llm = LLMClient(llm_url, llm_model)
        self.sandbox = DefenseSandbox()
        self.patch_gen = PatchGenerator(self.llm, self.sandbox)
        self.target = target
        self.command_history = []
        self.findings = []
        self.patches_applied = []

        self.metrics = {
            "start_time": time.time(),
            "end_time": None,
            "total_iterations": 0,
            "commands_executed": 0,
            "commands_successful": 0,
            "commands_failed": 0,
            "commands_blocked": 0,
            "rag_queries": 0,
            "llm_calls": 0,
            "vulnerabilities_detected": 0,
            "patches_generated": 0,
            "patches_applied": 0,
            "patches_validated": 0,
            "patches_failed": 0,
            "hardening_actions": 0,
            "false_positives": 0,
            "iteration_times": [],
        }

        print(f"[AGENT] Target to defend: {target}")
        print(f"[AGENT] Defensive tools: LOADED")

    def query_knowledge_base(self, query: str) -> str:
        """Query MCP defensive knowledge base"""
        print(f"\n[RAG] Querying defensive knowledge base: {query}")
        self.metrics["rag_queries"] += 1
        results = self.mcp.search(query, top_k=3)

        if not results:
            return "No relevant defensive techniques found."

        context = ""
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            if "[Rank" in text:
                text = text.split("\n\n", 2)[-1] if "\n\n" in text else text
            context += f"\n--- Source {i} ---\n{text[:800]}\n"

        print(f"[RAG] Found {len(results)} relevant sources")
        return context

    def ask_llm(self, prompt: str, context: str = "") -> str:
        """Ask LLM for defensive strategy"""
        full_prompt = prompt
        if context:
            full_prompt = f"""Relevant defensive techniques from knowledge base:
{context}

{prompt}"""

        print("\n[LLM] Consulting defensive decision engine...")
        self.metrics["llm_calls"] += 1
        response = self.llm.generate(full_prompt, system=self.SYSTEM_PROMPT)
        print(f"[LLM] Response received ({len(response)} chars)")
        return response

    def execute_command(self, command: str) -> Tuple[str, int]:
        """Execute command through defensive sandbox"""
        print(f"\n[EXEC] Running: {command}")
        output, code = self.sandbox.execute(command)

        self.metrics["commands_executed"] += 1
        if code == 0:
            self.metrics["commands_successful"] += 1
        elif code == -1:
            self.metrics["commands_blocked"] += 1
        else:
            self.metrics["commands_failed"] += 1

        if output:
            lines = output.split('\n')
            preview = '\n'.join(lines[:10])
            if len(lines) > 10:
                preview += f"\n... ({len(lines)-10} more lines)"
            print(f"[OUTPUT]:\n{preview}")

        print(f"[EXEC] Exit code: {code}")
        return output, code

    def defend_cycle(self, objective: str, max_iterations: int = 10):
        """Main defensive loop"""
        print(f"\n{'='*60}")
        print(f"[AGENT] DEFENSIVE OBJECTIVE: {objective}")
        print(f"{'='*60}\n")

        cycle_start = time.time()
        iteration = 0
        objective_met = False

        while iteration < max_iterations and not objective_met:
            iteration_start = time.time()
            iteration += 1
            self.metrics["total_iterations"] += 1
            print(f"\n{'─'*60}")
            print(f"[CYCLE] ITERATION {iteration}/{max_iterations}")
            print(f"{'─'*60}")

            # Query defensive knowledge base
            knowledge = self.query_knowledge_base(objective)

            # Build context with previous findings
            findings_context = ""
            if self.findings:
                findings_context = "\n\nPrevious findings this session:\n"
                for f in self.findings[-5:]:  # Last 5 findings
                    findings_context += f"- {f['description']} (severity: {f['severity']})\n"

            plan_prompt = f"""Objective: {objective}
Target: {self.target}
Iteration: {iteration}
{findings_context}

Based on the defensive knowledge base above, provide ONE specific diagnostic or remediation command.
Focus on the most critical unaddressed vulnerability first.
Be concise."""

            plan = self.ask_llm(plan_prompt, context=knowledge)
            print(f"\n[PLAN]:\n{plan}\n")

            # Extract commands
            commands = self._extract_commands(plan)

            if not commands:
                print("[WARN] No executable commands found in response")
                continue

            command = commands[0]

            # Repetition detection
            if self._is_repeating(command):
                print(f"\n[WARN] REPETITION DETECTED: '{command[:50]}...'")
                print("   Querying for alternative defensive approach...")
                alt_knowledge = self.query_knowledge_base(f"{objective} alternative defensive technique")
                alt_prompt = f"Previous approach already tried: {command}\n\nSuggest a DIFFERENT defensive technique."
                plan = self.ask_llm(alt_prompt, context=alt_knowledge)
                print(f"\n[PLAN] Alternative:\n{plan}\n")
                commands = self._extract_commands(plan)
                if not commands:
                    print("[WARN] No alternative commands found")
                    break
                command = commands[0]

            self.command_history.append(command)
            output, code = self.execute_command(command)

            # Analyze output for findings
            finding = self._analyze_output(command, output, code)
            if finding:
                self.findings.append(finding)
                self.metrics["vulnerabilities_detected"] += 1
                print(f"\n[FINDING] {finding['severity'].upper()}: {finding['description']}")

                # Generate and apply patch if vulnerability found
                if finding["severity"] in ("critical", "high"):
                    patch_result = self.patch_gen.generate_and_apply(
                        vulnerability=finding["description"],
                        context=output,
                        target=self.target
                    )
                    if patch_result["status"] == "applied":
                        self.metrics["patches_generated"] += 1
                        self.metrics["patches_applied"] += 1
                        self.patches_applied.append(patch_result)
                        print(f"[PATCH] Applied: {patch_result['description']}")

                        if patch_result.get("validated"):
                            self.metrics["patches_validated"] += 1
                            print(f"[PATCH] Validated successfully")
                        else:
                            self.metrics["patches_failed"] += 1
                            print(f"[PATCH] Validation pending")
                    elif patch_result["status"] == "generated":
                        self.metrics["patches_generated"] += 1
                        print(f"[PATCH] Generated but not applied: {patch_result['description']}")
                    else:
                        print(f"[PATCH] Generation failed: {patch_result.get('error', 'unknown')}")

            # Check if objective is met (all critical vulns patched)
            critical_unpatched = [
                f for f in self.findings
                if f["severity"] == "critical" and not f.get("patched")
            ]
            if self.findings and not critical_unpatched and iteration >= 3:
                self.metrics["hardening_actions"] += 1
                objective_met = True

            # Feedback to LLM
            status = "[OK]" if code == 0 else "[FAIL]"
            feedback_prompt = f"""Previous defensive action results:

Command: {command}
Exit code: {code} {status}
Output (truncated):
{output[:1024]}

Findings so far: {len(self.findings)}
Patches applied: {len(self.patches_applied)}

What should I check or fix next? Provide ONE specific command."""

            next_action = self.ask_llm(feedback_prompt)
            print(f"\n[NEXT]: {next_action[:200]}")

            iteration_time = time.time() - iteration_start
            self.metrics["iteration_times"].append(iteration_time)

            time.sleep(2)

        cycle_time = time.time() - cycle_start
        if objective_met:
            print(f"\n{'='*60}")
            print("[SUCCESS] DEFENSIVE OBJECTIVE ACHIEVED")
            print(f"[TIME] {cycle_time:.1f}s ({iteration} iterations)")
            print(f"[STATS] {len(self.findings)} findings, {len(self.patches_applied)} patches applied")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print(f"[INFO] Max iterations reached ({max_iterations})")
            print(f"[TIME] {cycle_time:.1f}s")
            print(f"[STATS] {len(self.findings)} findings, {len(self.patches_applied)} patches applied")
            print(f"{'='*60}\n")

        return objective_met

    def _extract_commands(self, text: str) -> List[str]:
        """Extract executable commands from LLM response"""
        commands = []

        code_blocks = re.findall(r'```(?:bash|sh)?\n(.*?)\n```', text, re.DOTALL)
        for block in code_blocks:
            commands.extend([line.strip() for line in block.split('\n')
                           if line.strip() and not line.strip().startswith('#')])

        cmd_lines = re.findall(r'^[$#]\s*(.+)$', text, re.MULTILINE)
        commands.extend(cmd_lines)

        if not commands:
            tool_commands = re.findall(
                r'((?:lynis|rkhunter|auditctl|fail2ban-client|ss|nmap|find|grep|cat|iptables|chmod|chown|systemctl).*)',
                text, re.IGNORECASE
            )
            commands.extend(tool_commands)

        return [cmd.strip() for cmd in commands if cmd.strip()]

    def _is_repeating(self, command: str, window: int = 3) -> bool:
        """Detect if same command has been tried multiple times recently"""
        if len(self.command_history) < window:
            return False

        recent_commands = self.command_history[-window:]
        normalized_cmd = command.split()[0] if command.split() else command

        repetitions = sum(1 for cmd in recent_commands if cmd.split()[0] == normalized_cmd)
        return repetitions >= window

    def _analyze_output(self, command: str, output: str, code: int) -> Optional[Dict]:
        """Analyze command output for security findings"""
        if code != 0:
            return None

        finding = None

        # SSH misconfigurations
        if "sshd_config" in command or "ssh" in command.lower():
            if "PasswordAuthentication yes" in output:
                finding = {
                    "type": "misconfiguration",
                    "severity": "critical",
                    "description": "SSH password authentication enabled (brute force attack vector)",
                    "attack_technique": "T1110 - Brute Force",
                    "defense_technique": "D3-MAN - Multi-factor Authentication",
                    "evidence": "PasswordAuthentication yes in sshd_config",
                }
            elif "PermitRootLogin yes" in output:
                finding = {
                    "type": "misconfiguration",
                    "severity": "critical",
                    "description": "SSH root login permitted (direct root access attack vector)",
                    "attack_technique": "T1078 - Valid Accounts",
                    "defense_technique": "D3-ACH - Account Hardening",
                    "evidence": "PermitRootLogin yes in sshd_config",
                }

        # SUID binaries
        if "find" in command and "-perm" in command and "4000" in command:
            suspicious_suids = []
            for line in output.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Flag SUID binaries in unusual locations
                if any(p in line for p in ['/tmp/', '/home/', '/var/tmp/']):
                    suspicious_suids.append(line)
            if suspicious_suids:
                finding = {
                    "type": "vulnerability",
                    "severity": "high",
                    "description": f"Suspicious SUID binaries found: {', '.join(suspicious_suids)}",
                    "attack_technique": "T1548.001 - Abuse Elevation Control: SUID",
                    "defense_technique": "D3-FE - File Encryption / Permission Hardening",
                    "evidence": output[:512],
                }

        # Sudo misconfigurations
        if "sudoers" in command or "sudo -l" in command:
            dangerous_entries = []
            for line in output.strip().split('\n'):
                if any(cmd in line.lower() for cmd in ['nopasswd', 'all=(all)', '/bin/cat', '/bin/find', '/usr/bin/find']):
                    dangerous_entries.append(line.strip())
            if dangerous_entries:
                finding = {
                    "type": "misconfiguration",
                    "severity": "high",
                    "description": f"Dangerous sudo configuration: {'; '.join(dangerous_entries[:3])}",
                    "attack_technique": "T1548.003 - Sudo and Sudo Caching",
                    "defense_technique": "D3-ACH - Account Hardening",
                    "evidence": output[:512],
                }

        # World-writable files
        if "find" in command and ("777" in command or "-writable" in command or "world" in command.lower()):
            writable_files = [l.strip() for l in output.strip().split('\n') if l.strip()]
            if writable_files:
                finding = {
                    "type": "vulnerability",
                    "severity": "medium",
                    "description": f"World-writable files found: {', '.join(writable_files[:5])}",
                    "attack_technique": "T1222 - File and Directory Permissions Modification",
                    "defense_technique": "D3-FE - File Permission Hardening",
                    "evidence": output[:512],
                }

        # Weak users / password issues
        if "/etc/passwd" in command or "/etc/shadow" in command:
            if output and "password" not in command.lower():
                shell_users = [l for l in output.strip().split('\n')
                              if l.strip() and '/bin/bash' in l and 'root' not in l.split(':')[0]]
                if shell_users:
                    finding = {
                        "type": "informational",
                        "severity": "low",
                        "description": f"Users with shell access: {len(shell_users)} found",
                        "attack_technique": "T1078.003 - Local Accounts",
                        "defense_technique": "D3-UAM - User Account Management",
                        "evidence": '\n'.join(shell_users[:5]),
                    }

        return finding

    def print_summary(self):
        """Print comprehensive defensive metrics summary"""
        self.metrics["end_time"] = time.time()
        total_time = self.metrics["end_time"] - self.metrics["start_time"]

        print("\n" + "="*70)
        print("BLUE TEAM AGENT - DEFENSIVE PERFORMANCE SUMMARY")
        print("="*70)

        print(f"\n[TIMING]:")
        print(f"   Total runtime: {total_time:.1f}s")
        if self.metrics["iteration_times"]:
            avg_iteration = sum(self.metrics["iteration_times"]) / len(self.metrics["iteration_times"])
            print(f"   Average iteration: {avg_iteration:.1f}s")
            print(f"   Fastest iteration: {min(self.metrics['iteration_times']):.1f}s")
            print(f"   Slowest iteration: {max(self.metrics['iteration_times']):.1f}s")

        print(f"\n[DETECTION]:")
        print(f"   Vulnerabilities detected: {self.metrics['vulnerabilities_detected']}")
        print(f"   False positives: {self.metrics['false_positives']}")
        if self.metrics['vulnerabilities_detected'] > 0:
            fp_rate = (self.metrics['false_positives'] / self.metrics['vulnerabilities_detected']) * 100
            print(f"   False positive rate: {fp_rate:.1f}%")

        print(f"\n[PATCHING]:")
        print(f"   Patches generated: {self.metrics['patches_generated']}")
        print(f"   Patches applied: {self.metrics['patches_applied']}")
        print(f"   Patches validated: {self.metrics['patches_validated']}")
        print(f"   Patches failed: {self.metrics['patches_failed']}")
        if self.metrics['patches_generated'] > 0:
            success_rate = (self.metrics['patches_validated'] / self.metrics['patches_generated']) * 100
            print(f"   Patch success rate: {success_rate:.1f}%")

        print(f"\n[COMMANDS]:")
        print(f"   Total executed: {self.metrics['commands_executed']}")
        print(f"   Successful (exit 0): {self.metrics['commands_successful']}")
        print(f"   Failed (exit != 0): {self.metrics['commands_failed']}")
        print(f"   Blocked by sandbox: {self.metrics['commands_blocked']}")

        print(f"\n[AI OPERATIONS]:")
        print(f"   RAG queries: {self.metrics['rag_queries']}")
        print(f"   LLM calls: {self.metrics['llm_calls']}")
        print(f"   Total iterations: {self.metrics['total_iterations']}")

        print(f"\n[FINDINGS]:")
        for finding in self.findings:
            status = "PATCHED" if finding.get("patched") else "OPEN"
            print(f"   [{status}] {finding['severity'].upper()}: {finding['description'][:80]}")

        print(f"\n[LOGS]:")
        print(f"   Command log: {self.sandbox.log_file}")

        # Save metrics to JSON
        metrics_file = self.sandbox.log_file.replace('defense_commands.log', 'defense_metrics.json')
        try:
            metrics_output = {**self.metrics, "findings": self.findings, "patches": self.patches_applied}
            with open(metrics_file, 'w') as f:
                json.dump(metrics_output, f, indent=2)
            print(f"   Metrics JSON: {metrics_file}")
        except Exception:
            pass

        print("\n" + "="*70)


def main():
    """Main entry point"""
    print("""
+===========================================================+
|       AUTONOMOUS BLUE TEAM AGENT v1.0 - DEFENSIVE          |
|          Security Monitoring & Hardening Toolkit            |
+===========================================================+
    """)

    MCP_URL = os.getenv("MCP_URL", "http://mcp-rag-server.default.svc.cluster.local:8080")
    LLM_URL = os.getenv("LLM_URL", "http://192.168.1.84:1234")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder-14b-instruct-abliterated")
    TARGET = os.getenv("TARGET", "192.168.1.99")

    print(f"Configuration:")
    print(f"  MCP Server: {MCP_URL}")
    print(f"  LLM Server: {LLM_URL}")
    print(f"  LLM Model: {LLM_MODEL}")
    print(f"  Target: {TARGET}")
    print()

    agent = BlueTeamAgent(
        mcp_url=MCP_URL,
        llm_url=LLM_URL,
        llm_model=LLM_MODEL,
        target=TARGET
    )

    scenarios = [
        "Audit target system for vulnerabilities and apply security hardening",
        "Detect and remediate SSH security weaknesses",
        "Find and fix privilege escalation vectors (SUID, sudo misconfigs)",
    ]

    for scenario in scenarios:
        success = agent.defend_cycle(scenario, max_iterations=10)
        if not success:
            print(f"\n[INFO] Partial completion: {scenario}")

    print("\n[DONE] Blue team defensive exercise complete!")
    agent.print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
