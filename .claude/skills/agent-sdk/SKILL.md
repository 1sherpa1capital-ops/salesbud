---
name: agent-sdk
description: |
  Build production AI agents using the Claude Agent SDK. Use this skill whenever the user wants to create AI agents that autonomously read files, run commands, search the web, edit code, or any task requiring programmatic Claude automation. Includes when user mentions: "agent sdk", "claude agent", "build an agent", "automate with claude", "sdk agent", "python agent", "typescript agent", "subagent", "mcp server", "custom tools", "agent sessions", "query function", "claude sdk client", or any request involving the Claude Agent SDK API. Also use for hook customization, permission modes, session management, structured outputs, or connecting to external systems via MCP.
---

# Claude Agent SDK Skill

Reference: https://platform.claude.com/docs/en/agent-sdk/overview

This skill provides comprehensive guidance on building production AI agents with the Claude Agent SDK. The SDK gives you the same tools, agent loop, and context management that power Claude Code, programmable in Python and TypeScript.

## Installation

```bash
# TypeScript
npm install @anthropic-ai/claude-agent-sdk

# Python
pip install claude-agent-sdk
```

Set your API key:
```bash
export ANTHROPIC_API_KEY=your-api-key
```

---

## Core Concepts

### The `query()` Function

The main entry point that creates the agentic loop. Returns an async iterator that streams messages as Claude works.

**Python:**
```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")

asyncio.run(main())
```

**TypeScript:**
```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Find and fix the bug in auth.py",
  options: { allowedTools: ["Read", "Edit", "Bash"] }
})) {
  if (message.type === "assistant") {
    console.log(message.message?.content);
  } else if (message.type === "result") {
    console.log(`Done: ${message.subtype}`);
  }
}
```

### ClaudeAgentOptions / Options Configuration

The main configuration class for agent behavior:

| Option | Description |
|--------|-------------|
| `allowed_tools` | Tools to auto-approve without prompting |
| `system_prompt` | Custom system prompt |
| `permission_mode` | Control approval behavior |
| `mcp_servers` | External MCP server connections |
| `agents` | Subagent definitions |
| `hooks` | Event interceptors |
| `resume` | Resume a specific session |
| `continue_conversation` | Continue the most recent session |
| `max_turns` | Maximum agentic turns |
| `max_budget_usd` | Maximum budget for the session |
| `model` | Claude model to use |
| `cwd` | Working directory |

---

## Tool Definition and Registration

### Built-in Tools

The SDK includes built-in tools for reading files, running commands, and editing code:

| Tool | Description |
|------|-------------|
| `Read` | Read any file in the working directory |
| `Write` | Create new files |
| `Edit` | Make precise edits to existing files |
| `Bash` | Run terminal commands, scripts, git operations |
| `Glob` | Find files by pattern (`**/*.ts`, `src/**/*.py`) |
| `Grep` | Search file contents with regex |
| `WebSearch` | Search the web for current information |
| `WebFetch` | Fetch and parse web page content |
| `AskUserQuestion` | Ask the user clarifying questions |

### Custom Tools with MCP

Create custom tools using the MCP (Model Context Protocol):

**Python:**
```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {"content": [{"type": "text", "text": f"Sum: {args['a'] + args['b']}"}]}

calculator = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[add],
)

options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add"],
)
```

**TypeScript:**
```typescript
import { tool, createMcpServer } from "@anthropic-ai/claude-agent-sdk";

const myTool = tool({
  name: "greet",
  description: "Greet a user",
  inputSchema: { name: "string" }
}, async (args) => {
  return { content: [{ type: "text", text: `Hello, ${args.name}!` }] };
});

const server = createMcpServer({
  name: "greeter",
  tools: [myTool]
});
```

### MCP Server Connections

Connect to external MCP servers (databases, browsers, APIs):

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}
    }
)
```

---

## Agent Orchestration and Handoff Patterns

### Subagents

Spawn specialized agents to handle focused subtasks:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async for message in query(
    prompt="Use the code-reviewer agent to review this codebase",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Agent"],  # Agent tool required!
        agents={
            "code-reviewer": AgentDefinition(
                description="Expert code reviewer for quality and security reviews.",
                prompt="Analyze code quality and suggest improvements.",
                tools=["Read", "Glob", "Grep"],  # Tool restrictions
                model="sonnet",  # Optional model override
            )
        },
    ),
):
    print(message)
```

**AgentDefinition fields:**
- `description` (required): When to use this agent
- `prompt` (required): System prompt defining behavior
- `tools`: Array of allowed tool names
- `model`: Model override (`sonnet`, `opus`, `haiku`, `inherit`)

**Important:** Subagents cannot spawn their own subagents. Don't include `Agent` in subagent tools.

### Tool Restrictions

Subagents can be limited to specific tools:

```python
# Read-only analysis agent
"analyzer": AgentDefinition(
    prompt="Analyze code structure...",
    tools=["Read", "Grep", "Glob"],  # No Edit, Write, or Bash
)

# Test execution agent
"test-runner": AgentDefinition(
    prompt="Run tests...",
    tools=["Bash", "Read", "Grep"],
)
```

---

## Context and Memory Management

### Sessions

Maintain context across multiple exchanges:

**Python (ClaudeSDKClient):**
```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # First query
    await client.query("Read the auth module")
    async for message in client.receive_response():
        print(message)
    
    # Second query - continues same session automatically
    await client.query("Now refactor it")
    async for message in client.receive_response():
        print(message)
```

**TypeScript (continue flag):**
```typescript
// First query - creates session
for await (const message of query({
  prompt: "Read the auth module",
  options: { allowedTools: ["Read", "Glob"] }
})) { }

// Second query - continues
for await (const message of query({
  prompt: "Refactor it",
  options: { continue: true, allowedTools: ["Read", "Edit"] }
})) { }
```

### Resume Specific Session

```python
# Capture session ID from result
session_id = None
async for message in query(prompt="Analyze auth module", options=...):
    if hasattr(message, "session_id"):
        session_id = message.session_id

# Resume with that specific session
async for message in query(
    prompt="Now implement the refactoring",
    options=ClaudeAgentOptions(resume=session_id)
):
    print(message)
```

### Fork Sessions

Create a branch while keeping the original:

```python
async for message in query(
    prompt="Try OAuth2 instead",
    options=ClaudeAgentOptions(resume=session_id, fork_session=True)
):
    print(message)
```

---

## Error Handling and Retry Logic

### Handle Result Messages

```python
from claude_agent_sdk import ResultMessage

async for message in query(prompt="Process files", options=...):
    if isinstance(message, ResultMessage):
        if message.subtype == "success":
            print(f"Done: {message.result}")
        elif message.subtype == "error_max_turns":
            print("Hit turn limit - resume to continue")
        elif message.subtype == "error_max_budget_usd":
            print("Hit budget limit")
        else:
            print(f"Error: {message.subtype}")
```

### Permission Modes

Control how tool approval works:

```python
ClaudeAgentOptions(
    permission_mode="acceptEdits",  # Auto-approve file edits
    # permission_mode="bypassPermissions",  # No prompts (CI/sandbox)
    # permission_mode="default",  # Normal prompts
    # permission_mode="plan",  # Planning mode - no execution
)
```

### Custom Permission Handlers

```python
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

async def custom_handler(tool_name, input_data, context):
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/etc"):
        return PermissionResultDeny(message="System directory write not allowed")
    return PermissionResultAllow(updated_input=input_data)

options = ClaudeAgentOptions(can_use_tool=custom_handler)
```

---

## Hooks

Run custom code at key points in the agent lifecycle:

### Available Hooks

| Hook | When it fires |
|------|---------------|
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool execution |
| `PostToolUseFailure` | Tool execution failed |
| `UserPromptSubmit` | User prompt submitted |
| `Stop` | Agent execution stops |
| `SubagentStart` | Subagent starts |
| `SubagentStop` | Subagent completes |
| `Notification` | Agent status messages |

### Using Hooks

```python
from claude_agent_sdk import HookMatcher

async def log_file_change(input_data, tool_use_id, context):
    file_path = input_data.get("tool_input", {}).get("file_path", "unknown")
    print(f"Modified: {file_path}")
    return {}  # Allow the operation

options = ClaudeAgentOptions(
    hooks={
        "PostToolUse": [
            HookMatcher(matcher="Edit|Write", hooks=[log_file_change])
        ]
    }
)
```

### Hook Outputs

Return control instructions from hooks:

```python
return {
    "systemMessage": "Context to inject",  # Visible to model
    "hookSpecificOutput": {
        "permissionDecision": "deny",  # "allow", "deny", "ask"
        "updatedInput": {...},  # Modify tool input
    }
}
```

---

## Structured Outputs

Force the model to output specific formats:

```python
options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "bug_count": {"type": "integer"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["bug_count", "severity"]
        }
    }
)
```

---

## Best Practices

### 1. Choose the Right Tools

| Use Case | Tools |
|----------|-------|
| Read-only analysis | `Read`, `Glob`, `Grep` |
| Code modification | `Read`, `Edit`, `Write`, `Glob` |
| Full automation | `Read`, `Edit`, `Bash`, `Glob`, `Grep` |

### 2. Use Subagents for Parallelization

Run multiple analyses concurrently:

```python
# Main agent spawns style-checker, security-scanner, test-coverage simultaneously
# Each subagent runs independently, results aggregated at the end
```

### 3. Leverage Context Isolation

Subagents run in fresh conversation context - use this to:
- Explore files without bloating main conversation
- Run parallel tasks cleanly
- Apply specialized instructions without conflicts

### 4. Session Management

- Use `ClaudeSDKClient` (Python) or `continue: true` (TypeScript) for multi-turn conversations
- Capture `session_id` for resumption after process restarts
- Use `fork_session` to explore alternatives without losing original

### 5. Error Recovery

```python
# Resume after hitting limits
async for message in query(
    prompt="Continue the work",
    options=ClaudeAgentOptions(
        resume=session_id,
        max_turns=200  # Higher limit
    )
):
    print(message)
```

### 6. MCP for External Systems

Connect to databases, browsers, APIs via MCP:

```python
# Playwright for browser automation
# Filesystem for file operations
# GitHub for PR management
# Slack for notifications
```

---

## Common Patterns

### Pattern 1: Read-Only Code Reviewer

```python
async for message in query(
    prompt="Review auth.py for security issues",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        system_prompt="You are a security expert.",
    )
):
    if hasattr(message, "result"):
        print(message.result)
```

### Pattern 2: Automated Bug Fixer

```python
async for message in query(
    prompt="Find and fix bugs in utils.py",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Glob"],
        permission_mode="acceptEdits",
    )
):
    pass  # Auto-fixes
```

### Pattern 3: Research Agent with Web Access

```python
async for message in query(
    prompt="Research the latest AI trends",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "WebSearch", "WebFetch"],
    )
):
    pass
```

### Pattern 4: Multi-Step Workflow with Checkpoints

```python
async with ClaudeSDKClient() as client:
    await client.query("Analyze codebase structure")
    # ... process ...
    
    checkpoint_id = client.get_server_info().session_id
    
    await client.query("Implement feature X")
    # ... if something goes wrong ...
    
    await client.rewind_files(checkpoint_id)  # Revert to checkpoint
```

---

## Version-Specific Notes

- **Tool name change**: Older SDK versions use `"Task"` for subagent invocation; current versions use `"Agent"`. Check both for compatibility.
- **Session hooks**: `SessionStart` and `SessionEnd` are TypeScript-only in SDK hooks.
- **MCP tool naming**: Tools follow pattern `mcp__<server>__<action>`

---

## Related Resources

- [Quickstart](https://platform.claude.com/docs/en/agent-sdk/quickstart)
- [Python SDK Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [TypeScript SDK Reference](https://platform.claude.com/docs/en/agent-sdk/typescript)
- [Hooks Guide](https://platform.claude.com/docs/en/agent-sdk/hooks)
- [Subagents Guide](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Sessions Guide](https://platform.claude.com/docs/en/agent-sdk/sessions)
- [Example Agents](https://github.com/anthropics/claude-agent-sdk-demos)
