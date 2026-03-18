# Architecture

## Overview

AgentRelay connects AI agents across machines using SSH. There are no servers, brokers, or message queues — just direct SSH connections and a simple file-based job protocol.

```
┌──────────────────┐         SSH          ┌──────────────────┐
│  Node A (Laptop) │ ──────────────────►  │  Node B (Server) │
│                  │                      │                  │
│  agent.py        │  Upload job dir      │  runner.py       │
│  (dispatcher)    │  via SCP             │  (executor)      │
│                  │                      │                  │
│  Creates:        │                      │  Runs:           │
│  - prompt.md     │                      │  - Claude CLI    │
│  - meta.json     │                      │  - via stdin     │
│  - runner.py     │  Fetch results       │                  │
│                  │ ◄──────────────────  │  Produces:       │
│  Reads:          │  via SCP             │  - reply.md      │
│  - reply.md      │                      │  - log.md        │
│  - log.md        │                      │  - output/       │
└──────────────────┘                      └──────────────────┘
```

## Execution Paths

AgentRelay chooses the optimal execution path based on the target platform, mode, and wait flag:

| Target | Mode | Wait | Execution Path | Description |
|--------|------|------|----------------|-------------|
| Linux | read | yes | **Direct SSH stdout** | Fastest. SSH runs Claude directly, captures stdout. No runner.py involved. |
| Linux | read | no | Python runner | Runner bundled in job dir, launched in background. |
| Linux | write | * | Python runner | Runner handles Claude invocation with full tool access. |
| Windows | * | * | Python runner | Always uses runner.py (stdin pipe for reliable prompt delivery). |

### Direct SSH stdout (Fast Path)

For Linux read+wait tasks, AgentRelay skips the runner entirely:

```
agent.py → SSH → "claude -p 'prompt'" → stdout captured → displayed locally
```

This is the fastest path with the lowest overhead.

### Python Runner (Standard Path)

For all other combinations:

```
agent.py → SCP job dir → SSH "python runner.py job_dir"
                                    │
                                    ├── Read meta.json + prompt.md
                                    ├── Build delegated prompt
                                    ├── Popen(claude, stdin=prompt)
                                    ├── Timer(timeout) → killpg
                                    ├── Write reply.md + log.md
                                    └── SCP results back (if callback configured)
```

## Routing

### Direct
Node A has SSH access to Node B. Most common case.

### Relay
Node A cannot reach Node C directly, but Node B can. A sends to B, B forwards to C via WSL or local access.

```
Node A ──SSH──► Node B ──WSL──► Node C
(laptop)       (Windows)       (Linux/WSL)
```

### Shared Filesystem
When two nodes share a filesystem (e.g., Windows host + its own WSL), no SCP is needed. The job directory is directly accessible from both sides.

## Job Directory Structure

Every job creates a directory with this structure:

```
jobs/<job-id>/
├── meta.json      # Job metadata (target, mode, timeout, paths)
├── prompt.md      # Task instructions for the remote AI
├── runner.py      # Bundled runner (copied from agent.py's directory)
├── input/         # Input files (optional)
├── output/        # Output files produced by the AI
├── reply.md       # Final result ([OK] or [FAILED] on first line)
├── log.md         # Execution log (timestamps, errors, stderr)
└── dispatch.log   # Dispatch-side log (routing decisions, preflight)
```

## Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| `AGENT_DELEGATE_DEPTH` | Environment variable set to 1 by runner. agent.py refuses to send if ≥1. Prevents A→B→A infinite loops. |
| `MAX_TIMEOUT_SEC=1800` | Hard cap on timeout. Both agent.py and runner.py enforce it. |
| `os.setsid` | Linux runner detaches Claude from controlling TTY. Prevents SIGHUP zombies on SSH disconnect. |
| `os.killpg` | Timeout kills the entire process group, not just the parent. |
| Atomic writes | reply.md written via temp file + rename to prevent reading half-written content. |
| Preflight checks | Verifies remote cwd exists, Claude CLI is available, and system health (D-state check on Linux). |
