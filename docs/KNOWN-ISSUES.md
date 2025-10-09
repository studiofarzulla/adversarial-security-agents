# Known Issues and Workarounds
## Session: October 9, 2025

This document tracks bugs, limitations, and workarounds discovered during development.

---

## Issue #1: LM Studio Tool Calling Broken on Abliterated Models

### Summary
LM Studio's OpenAI-compatible tool calling API returns grammar parsing errors when using abliterated Qwen2.5-Coder models, even with properly formatted tool definitions.

### Details

**Environment:**
- LM Studio version: 0.3.23+ (inferred from available features)
- Model: `qwen2.5-coder-14b-instruct-abliterated`
- API endpoint: `http://192.168.1.84:1234/v1/chat/completions`

**Error:**
```json
{"error":"Unexpected empty grammar stack after accepting piece: {\""}
```

**Tested Request Format:**
```json
{
  "model": "qwen2.5-coder-14b-instruct-abliterated",
  "messages": [{"role": "user", "content": "Use the execute_command tool to run: nmap -sV 192.168.1.99"}],
  "tools": [{
    "type": "function",
    "function": {
      "name": "execute_command",
      "description": "Execute BlackArch tool with validation",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {"type": "string", "description": "Shell command to execute"},
          "reasoning": {"type": "string", "description": "Why this command advances the objective"}
        },
        "required": ["command", "reasoning"],
        "additionalProperties": false
      }
    }
  }],
  "stream": false
}
```

**What We Tried:**
- ✅ Added `additionalProperties: false` to parameters schema (recommended best practice)
- ✅ Used strict JSON schema format per LM Studio docs
- ✅ Set `stream: false` (required for tool calling)
- ❌ Still returns grammar parsing error

### Root Cause (Hypothesis)

**Abliteration damaged tool calling capability:**
- Abliteration removes safety guardrails by modifying model weights
- This process can degrade structured output capabilities (JSON schema following)
- Base `qwen2.5-coder-14b-instruct` (non-abliterated) has native tool calling support per Qwen docs
- None of the abliterated Qwen models in our LM Studio instance are available in non-abliterated form for comparison

**Available models:**
- `qwen2.5-coder-14b-instruct-abliterated` ❌ (tool calling broken)
- `qwen2.5-coder-32b-instruct-abliterated` (not tested, likely broken)
- `qwen2.5-coder-1.5b-instruct-abliterated` (not tested, likely broken)
- `qwen2.5-coder-3b-instruct-abliterated` (not tested, likely broken)
- No non-abliterated Qwen2.5-Coder models available ⚠️

### Impact

**Cannot use LLM-orchestrated architecture:**
```python
# This pattern doesn't work with abliterated models
response = llm.chat(messages, tools=[...])
for tool_call in response.tool_calls:
    execute_tool(tool_call.function.name, tool_call.function.arguments)
```

**Must use agent-orchestrated architecture:**
```python
# This pattern works (what we implemented)
rag_results = query_mcp(objective)
llm_response = llm.generate(prompt_with_rag_context)
commands = extract_commands_from_text(llm_response)
execute(commands[0])
```

### Workaround (IMPLEMENTED)

**Use agent-orchestrated pattern with optimized prompts:**

1. **Agent controls the loop** (not the LLM)
2. **Parse freeform text responses** instead of structured tool calls
3. **Optimize inference parameters** to make text more deterministic:
   ```python
   {
       "temperature": 0.4,        # Low = deterministic commands
       "min_p": 0.08,             # Dynamic sampling (better than top_p for Qwen2.5)
       "top_p": 1.0,              # Disabled when using min_p
       "top_k": 0,                # Disabled
       "repeat_penalty": 1.08,    # Prevent repetition loops
       "stream": False,           # Required for reliable parsing
       "cache_prompt": True       # Cache system prompt
   }
   ```
4. **Use comprehensive system prompt** with structured output format:
   ```
   **Reasoning**: [explanation with ATT&CK ID]
   **Command**: `[exact command]`
   **Expected Outcome**: [success criteria]
   ```
5. **Add exit code feedback** so LLM learns from failures:
   ```python
   feedback = f"Exit code: {code} {'✅' if code == 0 else '❌'}\nOutput: {output[:1024]}"
   ```

### Benefits of Workaround

**Actually superior for our use case:**
- ✅ **Works with abliterated models** (essential for uncensored security research)
- ✅ **More transparent** (can inspect/debug exact prompts and responses)
- ✅ **More flexible** (can adjust command extraction patterns without model changes)
- ✅ **Easier to debug** (print/log every step of the loop)
- ✅ **Lower latency** (no tool call overhead)

### Alternative Solutions (NOT IMPLEMENTED)

**Option 1: Use non-abliterated model**
- ❌ Would refuse security-related queries
- ❌ None available in our LM Studio instance
- ❌ Defeats purpose of using abliterated model

**Option 2: Use different LLM provider**
- ❌ Requires internet (cluster is air-gapped)
- ❌ Costs money
- ❌ Privacy concerns (sending offensive security data to external API)

**Option 3: Use Ollama instead of LM Studio**
- ❌ Research shows Ollama has worse tool calling reliability than LM Studio
- ❌ Still likely broken on abliterated models
- ❌ Would require reconfiguring entire stack

### Testing Procedure (For Future Reference)

**To test if a model supports tool calling:**

```bash
cat > /tmp/test_tool_call.json << 'EOF'
{
  "model": "<MODEL_NAME>",
  "messages": [{"role": "user", "content": "Use the test_tool to echo 'hello'"}],
  "tools": [{
    "type": "function",
    "function": {
      "name": "test_tool",
      "description": "A test tool that echoes input",
      "parameters": {
        "type": "object",
        "properties": {
          "message": {"type": "string", "description": "Message to echo"}
        },
        "required": ["message"],
        "additionalProperties": false
      }
    }
  }],
  "stream": false
}
EOF

curl http://192.168.1.84:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @/tmp/test_tool_call.json
```

**Expected success response:**
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "test_tool",
          "arguments": "{\"message\":\"hello\"}"
        }
      }]
    },
    "finish_reason": "tool_calls"
  }]
}
```

**Expected failure (grammar error):**
```json
{"error":"Unexpected empty grammar stack after accepting piece: {\""}
```

### Related Research

**From research notes (2025-10-09):**
- LM Studio 0.3.23+ has improved in-app chat tool calling reliability
- Qwen2.5-Coder family officially supports tool calling natively
- Tool calling works better with structured schemas (`additionalProperties: false`)
- `min_p` sampling is superior to `top_p` for Qwen2.5-Coder specifically

**However:** None of this research anticipated abliteration breaking tool calling.

### Recommendations

1. **Keep using agent-orchestrated pattern** - it's working great
2. **Document this limitation** - future researchers should know abliteration breaks tool calling
3. **Consider requesting non-abliterated Qwen2.5-Coder** - for comparison testing only (not for actual use)
4. **Monitor LM Studio updates** - grammar parser improvements might fix this

---

## Issue #2: (Reserved for future issues)

---

**Document Created**: October 9, 2025
**Last Updated**: October 9, 2025
**Status**: Active workaround implemented, no blocker for research
