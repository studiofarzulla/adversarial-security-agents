#!/usr/bin/env python3
"""
Shared components for Adversarial Security Agents.
Provides MCP client and LLM client used by both red and blue team agents.
"""

import json
from typing import Dict, List

import requests


class MCPClient:
    """Client for Model Context Protocol server"""

    def __init__(self, mcp_url: str, client_name: str = "security-agent", client_version: str = "2.0.0"):
        self.mcp_url = mcp_url
        self.session_id = 0
        self.client_name = client_name
        self.client_version = client_version
        self._initialize()

    def _initialize(self):
        """Perform MCP handshake"""
        print(f"[MCP] Connecting to knowledge base...")

        resp = requests.post(self.mcp_url, json={
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": self.client_name, "version": self.client_version}
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
        print(f"[MCP] Connected: {len(self.tools)} tools available")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search the knowledge base"""
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
                print(f"[WARN] MCP search error: {result}")
                return []

            return result.get("content", [])
        except Exception as e:
            print(f"[ERROR] MCP search failed: {e}")
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
                "stream": False,
                "temperature": 0.4,
                "min_p": 0.08,
                "top_p": 1.0,
                "top_k": 0,
                "repeat_penalty": 1.08,
                "max_tokens": max_tokens,
                "cache_prompt": True
            }, timeout=60)

            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            return ""
