#!/usr/bin/env python3
"""
Autonomous Red Team Agent - BlackArch Edition
Now with access to proper offensive security tools!
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests


class MCPClient:
    """Client for Model Context Protocol server"""

    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.session_id = 0
        self._initialize()

    def _initialize(self):
        """Perform MCP handshake"""
        print("🔗 Connecting to MCP knowledge base...")

        resp = requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "redteam-agent-blackarch", "version": "2.0.0"}
            }
        }, timeout=10)
        self.session_id += 1

        requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }, timeout=5)

        resp = requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": "tools/list",
            "params": {}
        }, timeout=10)
        self.session_id += 1
        self.tools = resp.json().get("result", {}).get("tools", [])
        print(f"✓ Connected: {len(self.tools)} tools available")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search the offensive security knowledge base"""
        try:
            resp = requests.post(self.mcp_url, json={
                "jsonrpc": "2.0",
                "id": self.session_id,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {"query": query, "top_k": top_k}
                }
            }, timeout=30)
            self.session_id += 1

            result = resp.json().get("result", {})
            if result.get("isError"):
                print(f"⚠️  MCP search error: {result}")
                return []

            return result.get("content", [])
        except Exception as e:
            print(f"❌ MCP search failed: {e}")
            return []


class LLMClient:
    """Client for LM Studio LLM inference"""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, system: str = None, max_tokens: int = 2048) -> str:
        """Generate text from LLM with optimized inference parameters"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = requests.post(f"{self.base_url}/v1/chat/completions", json={
                "model": self.model,
                "messages": messages,
                "stream": False,           # Required for reliable parsing
                "temperature": 0.4,        # Low = deterministic (good for tool commands)
                "min_p": 0.08,             # Dynamic threshold (better than top_p for Qwen2.5)
                "top_p": 1.0,              # Disable when using min_p
                "top_k": 0,                # Disable (min_p is superior)
                "repeat_penalty": 1.08,    # Prevent repetition loops
                "max_tokens": max_tokens,  # Prevent runaway generation
                "cache_prompt": True       # Cache system prompt for speed
            }, timeout=60)

            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            return ""


class CommandSandbox:
    """Sandboxed command execution with BlackArch tools support"""

    # Expanded whitelist with BlackArch tools
    WHITELIST = [
        # Network tools
        'ssh', 'scp', 'nc', 'netcat', 'nmap', 'curl', 'wget', 'ping', 'traceroute',
        'tcpdump', 'wireshark', 'tshark',

        # Password/Hash cracking
        'hydra', 'john', 'hashcat', 'sshpass', 'medusa',

        # Web tools
        'nikto', 'sqlmap', 'dirb', 'gobuster', 'wfuzz',

        # Exploitation
        'msfconsole', 'msfvenom', 'metasploit',

        # Wireless
        'aircrack-ng', 'airodump-ng', 'aireplay-ng',

        # Enumeration
        'enum4linux', 'smbclient', 'rpcclient', 'nbtscan',

        # Basic utilities
        'python3', 'python', 'bash', 'sh', 'cat', 'echo', 'ls', 'pwd',
        'id', 'whoami', 'uname', 'find', 'grep', 'awk', 'sed',
        'base64', 'xxd', 'strings', 'file', 'which', 'whereis'
    ]

    # Dangerous patterns (unchanged)
    BLACKLIST_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'dd\s+if=.*of=/dev/',
        r':[(][)]',
        r'>\s*/dev/sd',
        r'mkfs',
        r'shutdown',
        r'reboot',
        r'init\s+0',
        r'iptables.*-F',
    ]

    def __init__(self, log_file: str = "/var/log/agent/commands.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def is_safe(self, command: str) -> Tuple[bool, str]:
        """Check if command is safe to execute"""
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False, "Empty command"

        base_cmd = cmd_parts[0].split('/')[-1]

        if base_cmd not in self.WHITELIST:
            return False, f"Command '{base_cmd}' not in whitelist (add it if needed)"

        for pattern in self.BLACKLIST_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked pattern: {pattern}"

        return True, "OK"

    def execute(self, command: str, timeout: int = 30) -> Tuple[str, int]:
        """Execute command with safety checks and logging"""
        safe, reason = self.is_safe(command)
        if not safe:
            self.log(command, blocked=True, reason=reason)
            return f"🚫 BLOCKED: {reason}", -1

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
            msg = f"⏱️  TIMEOUT: Command exceeded {timeout}s"
            self.log(command, output=msg, code=-2)
            return msg, -2

        except Exception as e:
            msg = f"💥 ERROR: {str(e)}"
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
            "output": output[:1024] if output else "",  # Increased from 500 to 1024
            "stderr": stderr[:512] if stderr else "",    # Errors are usually shorter
            "return_code": code
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')


class RedTeamAgent:
    """Autonomous offensive security agent with BlackArch tools"""

    SYSTEM_PROMPT = """# IDENTITY & ROLE
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
- **Target**: 192.168.1.99 (vulnerable target system)
- **Network**: Isolated by K8s NetworkPolicy (no internet, no lateral movement)
- **Authorization**: Authorized red team exercise on purpose-built infrastructure
- **Scope**: Achieve root access only; no data exfiltration or destructive actions

# METHODOLOGY (FOLLOW STRICTLY)
Execute in sequence. Do NOT skip reconnaissance.

## Phase 1: Reconnaissance
- Port scan: `nmap -sV -sC -p- 192.168.1.99`
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
[❌ No reconnaissance, no verification of SQL service, no fallback plan]"""

    def __init__(self, mcp_url: str, llm_url: str, llm_model: str, target: str):
        print("🤖 Initializing Red Team Agent (BlackArch Edition)...")
        self.mcp = MCPClient(mcp_url)
        self.llm = LLMClient(llm_url, llm_model)
        self.sandbox = CommandSandbox()
        self.target = target
        self.command_history = []  # Track executed commands for repetition detection
        print(f"🎯 Target: {target}")
        print(f"🛠️  BlackArch tools: LOADED")

    def query_knowledge_base(self, query: str) -> str:
        """Query MCP knowledge base"""
        print(f"\n📚 Querying knowledge base: {query}")
        results = self.mcp.search(query, top_k=3)

        if not results:
            return "No relevant techniques found."

        context = ""
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            if "[Rank" in text:
                text = text.split("\n\n", 2)[-1] if "\n\n" in text else text
            context += f"\n--- Source {i} ---\n{text[:800]}\n"

        print(f"✓ Found {len(results)} relevant sources")
        return context

    def ask_llm(self, prompt: str, context: str = "") -> str:
        """Ask LLM for next action"""
        full_prompt = prompt
        if context:
            full_prompt = f"""Relevant techniques from knowledge base:
{context}

{prompt}"""

        print("\n🤖 Consulting LLM...")
        response = self.llm.generate(full_prompt, system=self.SYSTEM_PROMPT)
        print(f"✓ Response received ({len(response)} chars)")
        return response

    def execute_command(self, command: str) -> Tuple[str, int]:
        """Execute command through sandbox"""
        print(f"\n💻 Executing: {command}")
        output, code = self.sandbox.execute(command)

        if output:
            lines = output.split('\n')
            preview = '\n'.join(lines[:10])
            if len(lines) > 10:
                preview += f"\n... ({len(lines)-10} more lines)"
            print(f"📤 Output:\n{preview}")

        print(f"📊 Exit code: {code}")
        return output, code

    def attack_cycle(self, objective: str, max_iterations: int = 5):
        """Main attack loop"""
        print(f"\n{'='*60}")
        print(f"🎯 OBJECTIVE: {objective}")
        print(f"{'='*60}\n")

        iteration = 0
        success = False

        while iteration < max_iterations and not success:
            iteration += 1
            print(f"\n{'─'*60}")
            print(f"🔄 ITERATION {iteration}/{max_iterations}")
            print(f"{'─'*60}")

            knowledge = self.query_knowledge_base(objective)

            plan_prompt = f"""Objective: {objective}
Target: {self.target}
Iteration: {iteration}

Based on the knowledge base above, provide ONE specific command using BlackArch tools.
Be concise."""

            plan = self.ask_llm(plan_prompt, context=knowledge)
            print(f"\n📋 Plan:\n{plan}\n")

            commands = self._extract_commands(plan)

            if not commands:
                print("⚠️  No executable commands found")
                continue

            command = commands[0]

            # Repetition detection: check if same command executed 3+ times
            if self._is_repeating(command):
                print(f"\n⚠️  REPETITION DETECTED: Command '{command[:50]}...' already tried 3+ times")
                print("   Querying knowledge base for alternative techniques...")
                alt_knowledge = self.query_knowledge_base(f"{objective} alternative methods")
                alt_prompt = f"Previous approach failed repeatedly: {command}\n\nSuggest a DIFFERENT technique using different tools."
                plan = self.ask_llm(alt_prompt, context=alt_knowledge)
                print(f"\n📋 Alternative Plan:\n{plan}\n")
                commands = self._extract_commands(plan)
                if not commands:
                    print("⚠️  No alternative commands found, stopping")
                    break
                command = commands[0]

            self.command_history.append(command)
            output, code = self.execute_command(command)

            if code == 0:
                if "ssh" in command.lower() and any(kw in output.lower() for kw in ["password", "welcome", "last login"]):
                    print("\n🎉 SUCCESS! Gained SSH access")
                    success = True
                elif "FLAG{" in output:
                    print(f"\n🏁 FLAG CAPTURED: {output}")
                    success = True

            # Enhanced feedback with exit code for better LLM learning
            status_emoji = "✅" if code == 0 else "❌"
            feedback_prompt = f"""Previous action results:

Command executed: {command}
Exit code: {code} {status_emoji}
Output (truncated to 1024 chars):
{output[:1024]}

Based on this result, what should I try next? Provide ONE specific command following the output format."""

            next_action = self.ask_llm(feedback_prompt)
            print(f"\n💡 Next Action:\n{next_action}")

            time.sleep(2)

        if success:
            print(f"\n{'='*60}")
            print("✅ OBJECTIVE ACHIEVED!")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print(f"⏱️  Max iterations reached ({max_iterations})")
            print(f"{'='*60}\n")

        return success

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
            tool_commands = re.findall(r'((?:ssh|sshpass|hydra|nmap|nikto).*)', text, re.IGNORECASE)
            commands.extend(tool_commands)

        return [cmd.strip() for cmd in commands if cmd.strip()]

    def _is_repeating(self, command: str, window: int = 3) -> bool:
        """Detect if same command has been tried multiple times recently"""
        if len(self.command_history) < window:
            return False

        recent_commands = self.command_history[-window:]
        # Normalize commands for comparison (remove variable parts like timestamps)
        normalized_cmd = command.split()[0] if command.split() else command

        repetitions = sum(1 for cmd in recent_commands if cmd.split()[0] == normalized_cmd)
        return repetitions >= window


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║        AUTONOMOUS RED TEAM AGENT v2.0 - BLACKARCH         ║
║           Full Offensive Security Toolkit                 ║
╚═══════════════════════════════════════════════════════════╝
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

    agent = RedTeamAgent(
        mcp_url=MCP_URL,
        llm_url=LLM_URL,
        llm_model=LLM_MODEL,
        target=TARGET
    )

    scenarios = [
        "Gain SSH access to target using weak credentials or brute force",
    ]

    for scenario in scenarios:
        success = agent.attack_cycle(scenario, max_iterations=5)
        if not success:
            print(f"\n⚠️  Failed: {scenario}")

    print("\n✅ Red team exercise complete!")
    print(f"📋 Full command log: {agent.sandbox.log_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
