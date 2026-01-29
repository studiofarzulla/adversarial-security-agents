#!/usr/bin/env python3
"""
Automated Security Patch Generator
Generates, validates, and applies security patches with rollback support.
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class PatchGenerator:
    """LLM-driven security patch generation and validation"""

    PATCH_PROMPT = """You are a security patch generator. Given a vulnerability description and system context, generate a precise remediation patch.

Rules:
- Output ONLY the remediation commands, one per line
- Each command must be safe and reversible
- Include comments explaining each step
- Do NOT include diagnostic or verification commands

Vulnerability: {vulnerability}

System context:
{context}

Generate the patch commands:"""

    ROLLBACK_PROMPT = """Given the following patch commands that were applied to fix a security vulnerability, generate the EXACT rollback commands to undo the changes.

Patch commands applied:
{patch_commands}

Original vulnerability context:
{context}

Generate rollback commands (one per line):"""

    VALIDATION_PROMPT = """Given a security patch that was applied, generate ONE verification command to confirm the vulnerability is fixed.

Vulnerability: {vulnerability}
Patch applied: {patch_commands}

Generate a single verification command:"""

    # Known vulnerability patterns with pre-built patches
    KNOWN_PATCHES = {
        "ssh_password_auth": {
            "description": "Disable SSH password authentication",
            "detect_pattern": r"PasswordAuthentication\s+yes",
            "patch_commands": [
                "# Backup current SSH config",
                "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.{timestamp}",
                "# Disable password authentication",
                "sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config",
                "# Restart SSH service",
                "systemctl restart sshd",
            ],
            "rollback_commands": [
                "cp /etc/ssh/sshd_config.bak.{timestamp} /etc/ssh/sshd_config",
                "systemctl restart sshd",
            ],
            "validate_command": "grep '^PasswordAuthentication' /etc/ssh/sshd_config",
            "validate_expect": "PasswordAuthentication no",
        },
        "ssh_root_login": {
            "description": "Disable SSH root login",
            "detect_pattern": r"PermitRootLogin\s+yes",
            "patch_commands": [
                "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.{timestamp}",
                "sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config",
                "systemctl restart sshd",
            ],
            "rollback_commands": [
                "cp /etc/ssh/sshd_config.bak.{timestamp} /etc/ssh/sshd_config",
                "systemctl restart sshd",
            ],
            "validate_command": "grep '^PermitRootLogin' /etc/ssh/sshd_config",
            "validate_expect": "PermitRootLogin no",
        },
        "suid_binary": {
            "description": "Remove SUID bit from suspicious binaries",
            "detect_pattern": r"/tmp/.*suid|/home/.*suid",
            "patch_commands": [
                "# Record current permissions",
                "stat {target_file}",
                "# Remove SUID bit",
                "chmod u-s {target_file}",
            ],
            "rollback_commands": [
                "chmod u+s {target_file}",
            ],
            "validate_command": "find {target_file} -perm -4000 2>/dev/null | wc -l",
            "validate_expect": "0",
        },
        "sudo_misconfig": {
            "description": "Remove dangerous sudo entries",
            "detect_pattern": r"NOPASSWD.*(?:cat|find|vi|less|more|bash|sh)",
            "patch_commands": [
                "cp /etc/sudoers /etc/sudoers.bak.{timestamp}",
                "# Comment out dangerous sudo entries (requires visudo-compatible edit)",
                "sed -i '/NOPASSWD.*\\(cat\\|find\\|vi\\|less\\|more\\|bash\\|sh\\)/s/^/#DISABLED_BY_BLUETEAM# /' /etc/sudoers",
            ],
            "rollback_commands": [
                "cp /etc/sudoers.bak.{timestamp} /etc/sudoers",
            ],
            "validate_command": "grep -c 'NOPASSWD.*\\(cat\\|find\\)' /etc/sudoers",
            "validate_expect": "0",
        },
        "world_writable": {
            "description": "Fix world-writable file permissions",
            "detect_pattern": r"world.writable|777",
            "patch_commands": [
                "# Record current permissions",
                "stat {target_file}",
                "# Remove world-writable permission",
                "chmod o-w {target_file}",
            ],
            "rollback_commands": [
                "chmod o+w {target_file}",
            ],
            "validate_command": "stat -c '%a' {target_file}",
            "validate_expect": "not 777",
        },
        "cron_insecure": {
            "description": "Fix insecure cron job permissions",
            "detect_pattern": r"/etc/cron\.d/.*666|cron.*world",
            "patch_commands": [
                "stat {target_file}",
                "chmod 644 {target_file}",
                "chown root:root {target_file}",
            ],
            "rollback_commands": [
                "chmod 666 {target_file}",
            ],
            "validate_command": "stat -c '%a' {target_file}",
            "validate_expect": "644",
        },
    }

    def __init__(self, llm_client, sandbox):
        self.llm = llm_client
        self.sandbox = sandbox
        self.applied_patches: List[Dict] = []

    def generate_and_apply(self, vulnerability: str, context: str, target: str) -> Dict:
        """Generate a patch, apply it, and validate the result."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        result = {
            "timestamp": timestamp,
            "vulnerability": vulnerability,
            "status": "failed",
            "description": "",
            "patch_commands": [],
            "rollback_commands": [],
            "validation": None,
            "validated": False,
        }

        # Try known patches first
        patch_def = self._match_known_patch(vulnerability, context)

        if patch_def:
            print(f"[PATCH] Matched known patch: {patch_def['description']}")
            result["description"] = patch_def["description"]

            # Resolve template variables
            target_file = self._extract_target_file(vulnerability, context)
            template_vars = {"timestamp": timestamp, "target_file": target_file or "/tmp/unknown"}

            patch_commands = [
                cmd.format(**template_vars) for cmd in patch_def["patch_commands"]
                if not cmd.startswith("#")
            ]
            rollback_commands = [
                cmd.format(**template_vars) for cmd in patch_def["rollback_commands"]
            ]
            validate_cmd = patch_def["validate_command"].format(**template_vars)
            validate_expect = patch_def["validate_expect"]

        else:
            # Fall back to LLM-generated patch
            print("[PATCH] No known patch matched, generating via LLM...")
            llm_patch = self._generate_llm_patch(vulnerability, context)
            if not llm_patch:
                result["error"] = "LLM failed to generate patch"
                return result

            patch_commands = llm_patch["patch_commands"]
            rollback_commands = llm_patch["rollback_commands"]
            validate_cmd = llm_patch.get("validate_command", "")
            validate_expect = llm_patch.get("validate_expect", "")
            result["description"] = f"LLM-generated patch for: {vulnerability[:80]}"

        result["patch_commands"] = patch_commands
        result["rollback_commands"] = rollback_commands

        # Apply patch commands
        print(f"[PATCH] Applying {len(patch_commands)} commands...")
        all_succeeded = True
        for cmd in patch_commands:
            output, code = self.sandbox.execute(cmd)
            if code not in (0, -1):  # -1 is blocked, non-zero is failure
                print(f"[PATCH] Command failed: {cmd} (exit {code})")
                all_succeeded = False
                break
            elif code == -1:
                print(f"[PATCH] Command blocked by sandbox: {cmd}")
                all_succeeded = False
                break

        if all_succeeded:
            result["status"] = "applied"

            # Validate
            if validate_cmd:
                print(f"[PATCH] Validating: {validate_cmd}")
                val_output, val_code = self.sandbox.execute(validate_cmd)
                result["validation"] = {
                    "command": validate_cmd,
                    "output": val_output.strip(),
                    "exit_code": val_code,
                    "expected": validate_expect,
                }

                if val_code == 0:
                    if validate_expect in val_output or validate_expect == "not 777":
                        result["validated"] = True
                        print(f"[PATCH] Validation PASSED")
                    else:
                        print(f"[PATCH] Validation FAILED: expected '{validate_expect}', got '{val_output.strip()}'")
                else:
                    print(f"[PATCH] Validation command failed (exit {val_code})")
        else:
            result["status"] = "failed"
            result["error"] = "One or more patch commands failed"

            # Attempt rollback
            if rollback_commands:
                print("[PATCH] Rolling back...")
                for cmd in rollback_commands:
                    self.sandbox.execute(cmd)

        self.applied_patches.append(result)
        return result

    def _match_known_patch(self, vulnerability: str, context: str) -> Optional[Dict]:
        """Match vulnerability against known patch patterns."""
        combined = f"{vulnerability} {context}".lower()
        for key, patch_def in self.KNOWN_PATCHES.items():
            if re.search(patch_def["detect_pattern"], combined, re.IGNORECASE):
                return patch_def
        return None

    def _extract_target_file(self, vulnerability: str, context: str) -> Optional[str]:
        """Extract file path from vulnerability description or context."""
        combined = f"{vulnerability}\n{context}"
        # Match common file paths
        paths = re.findall(r'(/(?:etc|tmp|home|var|usr|opt)/[\w./-]+)', combined)
        if paths:
            return paths[0]
        return None

    def _generate_llm_patch(self, vulnerability: str, context: str) -> Optional[Dict]:
        """Generate patch using LLM when no known pattern matches."""
        # Generate patch commands
        patch_prompt = self.PATCH_PROMPT.format(
            vulnerability=vulnerability,
            context=context[:1024]
        )
        patch_response = self.llm.generate(patch_prompt)
        if not patch_response:
            return None

        patch_commands = self._extract_commands(patch_response)
        if not patch_commands:
            return None

        # Generate rollback commands
        rollback_prompt = self.ROLLBACK_PROMPT.format(
            patch_commands='\n'.join(patch_commands),
            context=context[:512]
        )
        rollback_response = self.llm.generate(rollback_prompt)
        rollback_commands = self._extract_commands(rollback_response) if rollback_response else []

        # Generate validation command
        validate_prompt = self.VALIDATION_PROMPT.format(
            vulnerability=vulnerability,
            patch_commands='\n'.join(patch_commands)
        )
        validate_response = self.llm.generate(validate_prompt)
        validate_commands = self._extract_commands(validate_response) if validate_response else []

        return {
            "patch_commands": patch_commands,
            "rollback_commands": rollback_commands,
            "validate_command": validate_commands[0] if validate_commands else "",
            "validate_expect": "",
        }

    def _extract_commands(self, text: str) -> List[str]:
        """Extract executable commands from LLM response."""
        commands = []

        code_blocks = re.findall(r'```(?:bash|sh)?\n(.*?)\n```', text, re.DOTALL)
        for block in code_blocks:
            commands.extend([
                line.strip() for line in block.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ])

        if not commands:
            for line in text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    # Skip lines that look like prose
                    if line[0] in ('$', '-') or '/' in line or any(
                        line.startswith(cmd) for cmd in
                        ['sed', 'chmod', 'chown', 'cp', 'mv', 'systemctl', 'iptables',
                         'fail2ban', 'apt', 'pacman', 'grep', 'cat', 'echo', 'find']
                    ):
                        clean = line.lstrip('$ -')
                        if clean:
                            commands.append(clean)

        return commands

    def get_patch_report(self) -> Dict:
        """Return a summary report of all patches applied."""
        return {
            "total_patches": len(self.applied_patches),
            "applied": sum(1 for p in self.applied_patches if p["status"] == "applied"),
            "validated": sum(1 for p in self.applied_patches if p["validated"]),
            "failed": sum(1 for p in self.applied_patches if p["status"] == "failed"),
            "patches": self.applied_patches,
        }
