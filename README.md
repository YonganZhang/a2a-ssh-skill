```
     _                    _   ____       _
    / \   __ _  ___ _ __ | |_|  _ \ ___ | | __ _ _   _
   / _ \ / _` |/ _ \ '_ \| __| |_) / _ \| |/ _` | | | |
  / ___ \ (_| |  __/ | | | |_|  _ <  __/| | (_| | |_| |
 /_/   \_\__, |\___|_| |_|\__|_| \_\___|_|\__,_|\__, |
         |___/                                   |___/
```

**A2A defines how agents should talk. AgentRelay makes them work across your machines — today.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Tests: 6/6 Passing](https://img.shields.io/badge/Tests-6%2F6_Passing-brightgreen)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-orange)

---

## What is AgentRelay?

AgentRelay is a practical, zero-dependency tool that lets AI agents delegate tasks to each other across different machines via SSH. Unlike protocol-based approaches like Google A2A, AgentRelay works with what you already have — SSH access and a CLI AI tool (Claude Code, Codex, etc.). It is a single Python script. No servers, no brokers, no SDKs. If you can SSH into a machine, you can delegate work to it.

## Why AgentRelay?

| | AgentRelay | Google A2A |
|---|---|---|
| **What it is** | Cross-node delegation tool | Interoperability protocol |
| **Setup time** | 5 minutes | Hours (implement protocol endpoints) |
| **Dependencies** | Python stdlib + SSH | HTTP server + JSON-RPC + SDK |
| **Infrastructure** | Your existing SSH | Agent Cards, HTTP endpoints, webhooks |
| **Cross-machine** | Native design goal | Possible, but you build the infra |
| **Task artifacts** | Built-in (`reply.md`, `log.md`, `output/`) | Not provided |
| **Failure recovery** | Built-in (timeout, recursion guard, zombie cleanup) | Up to implementer |
| **Best for** | Getting real work done across 2-5 machines | Cross-vendor agent ecosystem interop |

> **Note:** AgentRelay and A2A are complementary, not competing. A2A solves agent *discovery* and *interoperability*. AgentRelay solves agent *delegation* and *execution*. You could use both — A2A to find agents, AgentRelay to actually run the work.

## Demo

```
[Laptop] $ python agent.py send gpu-server --cwd "/home/user/project" \
    --text "Run the test suite and fix any failures" --mode write --wait

[GPU Server] Claude receives task, runs tests, fixes code, writes reply.md...

[Laptop] ✅ [OK]
Fixed 3 failing tests in src/utils.py:
- test_parse_config: fixed missing default value
- test_validate_input: added boundary check
- test_export_data: corrected file path
```

One command. The laptop agent delegates the task, the GPU server agent executes it, and the results come back as structured files.

## Quick Start

```bash
# Clone
git clone https://github.com/YonganZhang/agent-relay && cd agent-relay

# Configure your nodes
cp agents.example.json agents.json
# Edit agents.json: set SSH hosts, claude_path, python_path

# Send your first task
python agent.py send my-server \
    --cwd "/home/user" \
    --text "check disk usage" \
    --mode read \
    --wait
```

That's it. No `pip install`, no virtual environment, no Docker.

## Features

- **Zero Dependencies** — Python standard library only. No pip install. Runs anywhere Python 3.10+ exists.
- **Cross-Platform** — Windows, Linux, WSL, macOS. A unified Python runner handles platform differences so you don't have to.
- **Fast Path** — Read-only tasks bypass the runner entirely and stream results directly via SSH stdout. Minimum overhead.
- **Battle-Tested** — Recursion guard prevents infinite delegation loops. Timeout cap (1800s) kills runaway tasks. Process-group kill via `setsid` ensures no orphaned processes. Atomic file writes prevent corrupted results.
- **Observable** — Every job produces `prompt.md`, `reply.md`, and `log.md`. Human-readable, grep-able, diff-able. No black-box execution.
- **Flexible Routing** — Direct SSH, relay through an intermediate node, or use a shared filesystem. Mix and match per target.

## Architecture

```
┌─────────────┐    SSH     ┌─────────────┐
│  Laptop     │ ─────────► │  GPU Server  │
│  agent.py   │            │  runner.py   │
│  (dispatch) │ ◄───────── │  (execute)   │
│             │   SCP/SSH  │  Claude CLI  │
└─────────────┘            └─────────────┘
```

### Execution Paths

| Target | Mode | Wait | Path |
|--------|------|------|------|
| Linux | `read` | yes | Direct SSH stdout (fastest) |
| Linux | `write` | * | Python runner |
| Windows | * | * | Python runner |

The dispatcher automatically selects the optimal path based on target OS, mode, and wait preference.

## How It Works

The job protocol is deliberately simple and file-based:

1. **`agent.py`** creates a job directory containing `prompt.md`, `meta.json`, and a copy of `runner.py`.
2. The job directory is **uploaded via SCP** to the remote node (or placed in a shared filesystem).
3. **`runner.py`** is launched on the remote node via SSH.
4. `runner.py` invokes the **Claude CLI** with the prompt piped via stdin, applying the specified mode and timeout.
5. Claude executes the task and the runner captures the output, writing **`reply.md`** and **`log.md`**.
6. Results are **fetched back via SCP** and returned to the calling agent.

Every step is a plain file operation. No daemon, no message queue, no database.

## Test Results

```
✅ Linux read+wait (direct SSH stdout)
✅ Linux write+wait (Python runner)
✅ Timeout cap enforcement (99999 → 1800)
✅ Windows read+wait (Python runner)
✅ Recursive delegation blocked
✅ stdout content doesn't trigger false retry
```

**Tested on:** Windows 11 (laptop) ↔ Windows Server (i9 + RTX 4090) ↔ Ubuntu 24.04 WSL

## Configuration

All node configuration lives in a single `agents.json` file:

```json
{
  "agents": {
    "gpu-server": {
      "ssh_host": "my-gpu-box",
      "ssh_user": "admin",
      "os": "linux",
      "claude_path": "/usr/local/bin/claude",
      "python_path": "/usr/bin/python3",
      "jobs_dir": "/home/admin/agent-relay/jobs"
    },
    "windows-dev": {
      "ssh_host": "win-machine",
      "ssh_user": "User",
      "os": "windows",
      "claude_path": "C:/Users/User/AppData/Roaming/npm/claude.cmd",
      "python_path": "C:/Python312/python.exe",
      "jobs_dir": "E:/agent-relay/jobs"
    }
  }
}
```

Each entry defines how to reach a node and where its tools live. Add as many nodes as you need.

## Roadmap

- [ ] Standalone CLI (`pip install agent-relay`)
- [ ] More AI CLI adapters (Codex, Gemini CLI, Aider, Ollama)
- [ ] Web dashboard for job monitoring
- [ ] Optional A2A protocol bridge

### Design Principles

- **Low token consumption** — Only prompt text is transmitted, not model context. The remote agent starts fresh with a clean, focused prompt.
- **High accuracy** — Task results are delivered as structured files (`reply.md`), not chat-style fuzzy output that needs parsing.
- **Full explainability** — Every job has a complete `log.md` with execution trace. You can audit exactly what happened.

## FAQ

<details>
<summary><strong>How is this different from Google A2A?</strong></summary>

Google A2A is a protocol specification for how agents discover and communicate with each other across vendors and platforms. It requires implementing HTTP endpoints, Agent Cards, and JSON-RPC handlers. AgentRelay is a tool — one Python script that delegates work over SSH right now. A2A solves interoperability at scale; AgentRelay solves "I have 3 machines and want them to collaborate on real tasks today."
</details>

<details>
<summary><strong>Does it only work with Claude?</strong></summary>

Currently, AgentRelay is tested with Claude Code (Anthropic's CLI). However, the runner invokes the AI tool as a subprocess with a text prompt, so any CLI-based AI tool that accepts a prompt and produces text output can be adapted. Support for Codex, Gemini CLI, and others is on the roadmap.
</details>

<details>
<summary><strong>Do I need cloud services?</strong></summary>

No. AgentRelay runs entirely on your own machines. The only requirement is SSH access between nodes. Your data never leaves your infrastructure (beyond whatever the AI CLI tool itself does).
</details>

<details>
<summary><strong>Can agents on different machines talk to each other?</strong></summary>

Yes — that is the entire point. Agent A on your laptop can delegate a task to Agent B on a GPU server, which can further delegate subtasks to Agent C on a Linux box. The recursion guard prevents infinite delegation loops, and each hop produces its own observable job artifacts.
</details>

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes before submitting a PR.

```bash
# Run the test suite
python -m pytest tests/
```

## License

[MIT](LICENSE) — Use it however you want.

---

<p align="center">
Built for people who have real machines and want real agents to do real work on them.
</p>
