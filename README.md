<div align="center">
  <img src="docs/assets/logo.svg" width="112" alt="A2A SSH Skill Logo" style="max-width: 100%;" />
  <h1>A2A SSH Skill</h1>
  <p><strong>Agent-to-Agent delegation over SSH. Zero dependencies. Works today.</strong></p>
</div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/E2E_Tests-6%2F6_Passing-brightgreen?logo=github-actions" alt="Tests: 6/6" />
  <img src="https://img.shields.io/badge/Dependencies-Zero-orange" alt="Zero Deps" />
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-black" alt="Claude Code" />
  <img src="https://img.shields.io/badge/Codex-Compatible-black" alt="Codex" />
</p>

<p align="center">
  <sub>Inspired by <a href="https://github.com/a2aproject/A2A">Google Agent2Agent (A2A) Protocol</a> · Built for builders who need it working today</sub>
</p>

---

> 💬 **Tired of 100+ MCP tools burning tokens just to talk across machines?**
> Tired of deploying HTTP servers, Agent Cards, and JSON-RPC endpoints before your agents can even say hello?
>
> **A2A SSH Skill** is the answer. One script. Zero dependencies. Your AI agents start collaborating across machines in 5 minutes — over plain SSH.
>
> **Google A2A wants you to build an HTTP server. We just need your SSH key. 🔑**

<div align="center">
<table>
<tr>
<td align="center"><h3>💰 ~90% Less Tokens</h3><sub>No framework context, no MCP overhead.<br/>Only your prompt travels over the wire.</sub></td>
<td align="center"><h3>⚡ 5 Min Setup</h3><sub>Clone, edit JSON, send.<br/>No servers. No SDKs.</sub></td>
<td align="center"><h3>🔒 Zero Trust Surface</h3><sub>No HTTP endpoints exposed.<br/>SSH encryption by default.</sub></td>
</tr>
</table>
</div>

---

## What is A2A SSH Skill?

**A2A SSH Skill** is a practical, zero-dependency Python tool for [Agent2Agent (A2A)](https://github.com/a2aproject/A2A)-style delegation over SSH.

While Google A2A defines a protocol for how agents *should* talk (JSON-RPC, HTTP endpoints, Agent Cards), **A2A SSH Skill makes agents *actually work* across your machines right now** — using nothing but SSH, Python, and a CLI AI tool like [Claude Code](https://claude.ai/claude-code) or [Codex](https://openai.com/codex).

**No HTTP server.** No broker. No message queue. No SDK. No `pip install`. If you can SSH into a machine, your AI agents can delegate work to it.

### The Pitch

```
Others are writing protocol specifications.
Your agents are already getting work done.

Others are deploying Agent Cards and webhook endpoints.
Your agents already finished the task and sent back the results.

Others spent a week setting up interoperability.
You spent 5 minutes editing agents.json.
```

## Why A2A SSH Skill? (vs Google A2A)

A2A SSH Skill and Google A2A solve **different problems** at **different layers**. They're complementary, not competing:

- **Google A2A** answers: *"How should agents discover and talk to each other across the internet?"*
- **A2A SSH Skill** answers: *"How do I make my machines work together as an AI team right now?"*

<table>
<tr><th width="200"></th><th width="280">🔀 A2A SSH Skill</th><th width="280">🌐 Google A2A Protocol</th></tr>
<tr><td><b>What it is</b></td><td>A ready-to-use delegation tool</td><td>An interoperability protocol specification</td></tr>
<tr><td><b>Setup time</b></td><td>⚡ <b>5 minutes</b> (clone + edit JSON)</td><td>Hours to days (implement protocol endpoints)</td></tr>
<tr><td><b>Dependencies</b></td><td>Python standard library + SSH</td><td>HTTP server + JSON-RPC + language SDK</td></tr>
<tr><td><b>What you need</b></td><td>SSH access to your machines</td><td>Agent Cards, HTTP endpoints, webhooks</td></tr>
<tr><td><b>Transport</b></td><td>SSH (encrypted by default)</td><td>HTTP/HTTPS</td></tr>
<tr><td><b>Discovery</b></td><td>Simple <code>agents.json</code> config file</td><td>Agent Card metadata standard</td></tr>
<tr><td><b>Cross-machine</b></td><td>✅ Native design goal</td><td>Possible, but you build the infrastructure</td></tr>
<tr><td><b>Task artifacts</b></td><td>✅ Built-in (<code>reply.md</code>, <code>log.md</code>, <code>output/</code>)</td><td>Not provided by the protocol</td></tr>
<tr><td><b>Failure recovery</b></td><td>✅ Timeout cap, recursion guard, process-group kill, zombie cleanup</td><td>Up to the implementer</td></tr>
<tr><td><b>Token efficiency</b></td><td>✅ Only prompt text transmitted, no context</td><td>Depends on implementation</td></tr>
<tr><td><b>Explainability</b></td><td>✅ Full <code>log.md</code> with every step traced</td><td>Depends on implementation</td></tr>
<tr><td><b>Best for</b></td><td><b>2-5 machines that need to get work done today</b></td><td>Cross-vendor agent ecosystem interoperability</td></tr>
</table>

> **TL;DR**: If you need your laptop, your GPU server, and your Linux box to work as an AI team — **A2A SSH Skill gets you there in 5 minutes**. If you need to build a public agent marketplace — use Google A2A.

## Demo

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [Laptop] You type one command:                                 │
│                                                                 │
│  $ python agent.py send gpu-server \                            │
│      --cwd "/home/user/ml-project" \                            │
│      --text "Run the failing tests and fix them" \              │
│      --mode write --wait                                        │
│                                                                 │
│  ─── What happens behind the scenes ───                         │
│                                                                 │
│  1. agent.py creates job directory with prompt.md               │
│  2. Uploads via SCP to gpu-server                               │
│  3. Launches runner.py on remote machine via SSH                │
│  4. Remote Claude reads the code, runs tests, fixes bugs        │
│  5. Writes reply.md + log.md with results                       │
│  6. Results fetched back to your laptop                         │
│                                                                 │
│  [Laptop] ✅ Result:                                            │
│                                                                 │
│  [OK]                                                           │
│  Fixed 3 failing tests in src/utils.py:                         │
│  - test_parse_config: added missing default value               │
│  - test_validate_input: boundary check was off by one           │
│  - test_export_data: file path used wrong separator on Linux    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Python 3.10+** on all machines (already installed on most systems)
- **SSH access** between your machines (key-based auth recommended)
- **A CLI AI tool** on each remote machine ([Claude Code](https://claude.ai/claude-code), [Codex](https://openai.com/codex), or any tool with `-p` flag)

### Install in 30 Seconds

```bash
# 1. Clone
git clone https://github.com/YonganZhang/a2a-ssh-skill && cd a2a-ssh-skill

# 2. Configure your nodes (no pip install needed!)
cp agents.example.json agents.json
# Edit agents.json: set your SSH hosts, claude_path, python_path

# 3. Verify SSH works
ssh my-server "echo ok"

# 4. Send your first task!
python agent.py send my-server \
  --cwd "/home/user" \
  --text "What Python version is installed? Check disk usage too." \
  --mode read --wait

# That's it. No servers to start. No endpoints to deploy. No tokens wasted on setup.
```

### Use as a Claude Code Skill

A2A SSH Skill can also be installed directly as a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code) — just copy it to your skills directory and Claude will automatically use it when you ask it to delegate tasks to remote machines:

```bash
cp -r a2a-ssh-skill ~/.claude/skills/agent-task-delegate
```

## Use Cases

A2A SSH Skill is not limited to any specific setup. Here's what people use it for:

| Scenario | How |
|---|---|
| 🧪 **Remote testing** | "Run the test suite on the CI server and fix any failures" |
| 🔧 **Remote debugging** | "Check why the API is returning 500 errors on production" |
| 🤖 **GPU offloading** | "Train this model on the GPU server and report the metrics" |
| 📊 **Cross-machine inspection** | "Compare the configs between staging and production" |
| 🏗️ **Multi-node deployment** | "Update the service on server A, then verify it from server B" |
| 🐛 **Log analysis** | "Search the last 1000 lines of nginx logs for timeout errors" |
| 📦 **Build delegation** | "Compile the project on the Linux box, it's faster there" |
| 🔍 **Security audit** | "Check all open ports and running services on the server" |

## Features

| | Feature | Description |
|---|---|---|
| 🪶 | **Zero Dependencies** | Python standard library only. No `pip install`. No `npm`. No SDKs. Just copy and run. |
| 🖥️ | **Cross-Platform** | Windows, Linux, WSL, macOS. One unified Python runner handles all platforms identically. |
| ⚡ | **Fast Path** | Read-only tasks on Linux bypass the runner entirely — stream directly via SSH stdout for minimal latency. |
| 🛡️ | **Battle-Tested Reliability** | Recursion guard (`AGENT_DELEGATE_DEPTH`), timeout cap (1800s max), process-group kill (`os.setsid` + `os.killpg`), atomic file writes via temp+rename. |
| 📄 | **Full Observability** | Every job produces `prompt.md` (what was asked), `reply.md` (what was answered), `log.md` (how it was executed). Human-readable. `grep`-able. `diff`-able. |
| 🔀 | **Flexible Routing** | Direct SSH, relay through an intermediate node (A→B→C), or shared filesystem (Windows host + its WSL). |
| 🤖 | **AI-Agnostic** | Works with any CLI AI that accepts a `-p` prompt flag: Claude Code, Codex, Aider, and more. |
| 🔒 | **Anti-Loop Protection** | Environment variable `AGENT_DELEGATE_DEPTH` prevents A→B→A→B infinite delegation loops that burn tokens endlessly. |
| 💰 | **Token Efficient** | Only the prompt text is transmitted — no model context, no conversation history, no framework overhead. |

## Architecture

```
┌──────────────────┐           SSH            ┌──────────────────┐
│   Node A          │                          │   Node B          │
│   (Your Laptop)   │  ┌─────────────────┐    │   (GPU Server)    │
│                    │  │  1. Upload job  │    │                    │
│   agent.py         │──│     via SCP     │──► │   runner.py        │
│   (dispatcher)     │  └─────────────────┘    │   (executor)       │
│                    │                          │                    │
│   Creates:         │  ┌─────────────────┐    │   Invokes:         │
│   ├─ prompt.md     │  │  2. Launch      │    │   Claude CLI       │
│   ├─ meta.json     │──│     via SSH     │──► │   via stdin pipe   │
│   └─ runner.py     │  └─────────────────┘    │                    │
│                    │                          │   Produces:        │
│   Receives:        │  ┌─────────────────┐    │   ├─ reply.md      │
│   ├─ reply.md      │◄─│  3. Fetch       │────│   ├─ log.md        │
│   └─ log.md        │  │     via SCP     │    │   └─ output/       │
└──────────────────┘  └─────────────────┘    └──────────────────┘
```

### Execution Paths

A2A SSH Skill automatically chooses the optimal execution path:

| Target | Mode | Wait | Path | Why |
|--------|------|------|------|-----|
| Linux | read | yes | **Direct SSH stdout** ⚡ | Fastest — no runner overhead, just `ssh host "claude -p ..."` |
| Linux | read | no | Python runner | Background execution needs job directory protocol |
| Linux | write | * | Python runner | Write tasks need full tool access via runner |
| Windows | * | * | Python runner | stdin pipe ensures reliable prompt delivery on Windows |

### Scale to Any Topology

A2A SSH Skill works with **any number of nodes** — from two machines to a fleet. Here are common setups:

**Two-Node** — The simplest: your laptop delegates to a remote server.
```
💻 Laptop ──── SSH ────► 🖥️ Server
```

**Three-Node with Relay** — A Windows server relays to its WSL Linux environment:
```
💻 Laptop ──── SSH ────► 🖥️ Windows Server ──── WSL ────► 🐧 Linux
```

**Fan-Out** — One coordinator delegates to multiple workers in parallel:
```
                         ┌── SSH ──► 🖥️ Server A (Build)
💻 Coordinator ──────────┼── SSH ──► 🖥️ Server B (Test)
                         └── SSH ──► 🐧 GPU Box  (Train)
```

Just add entries to `agents.json`. Each node auto-detects its identity via hostname matching. Any node can be a sender, receiver, or both.

## How It Works

### The Job Protocol

Every delegation creates a **job directory** — a self-contained folder with everything the remote agent needs:

```
jobs/20260319-014500-gpu-server-fix-tests-a1b2c3/
├── prompt.md      # 📝 Task instructions (what to do)
├── meta.json      # ⚙️ Metadata (target, mode, timeout, paths)
├── runner.py      # 🏃 Self-contained executor (bundled with every job)
├── reply.md       # ✅ Final result: [OK] or [FAILED] + details
├── log.md         # 📋 Execution trace: timestamps, errors, stderr
├── input/         # 📁 Input files (optional, for file-heavy tasks)
└── output/        # 📁 Generated files (optional, AI-produced artifacts)
```

**Everything is a plain text file.** No database. No message queue. No binary formats.
- Debug with `cat reply.md`
- Monitor with `watch -n5 ls jobs/`
- Archive with `tar`
- Search with `grep -r "FAILED" jobs/`

### Step-by-Step Flow

1. **You run** `python agent.py send <target> --text "do something" --wait`
2. **agent.py** auto-detects your node identity (via hostname matching)
3. **agent.py** creates a job directory with `prompt.md`, `meta.json`, and a bundled `runner.py`
4. **agent.py** uploads the job directory to the remote machine via SCP
5. **agent.py** launches `runner.py` on the remote node via SSH
6. **runner.py** reads the prompt, pipes it to Claude CLI via stdin
7. **Claude** executes the task using its tools (Read, Write, Bash, etc.)
8. **Claude** writes `reply.md` (result) and `log.md` (execution trace)
9. **agent.py** fetches the results back via SCP and displays them

### Safety Mechanisms

| Mechanism | What It Prevents |
|-----------|-----------------|
| `AGENT_DELEGATE_DEPTH` env var | Infinite A→B→A→B delegation loops (token drain) |
| `MAX_TIMEOUT_SEC = 1800` | Runaway processes (both dispatch-side and runner-side enforce) |
| `os.setsid` + `os.killpg` | Zombie processes after SSH disconnect (Linux) |
| Atomic file writes | Half-written `reply.md` being read as complete |
| Preflight checks | Verifying remote cwd, Claude CLI, system health before starting |
| D-state monitoring | Detecting unhealthy WSL instances (filesystem I/O stalls) |

## Token Efficiency: Why ~90% Less

Traditional multi-agent approaches waste tokens in several ways. A2A SSH Skill eliminates all of them:

| Token Waste Source | Traditional Approach | A2A SSH Skill |
|---|---|---|
| **Framework context** | Agent frameworks inject system prompts, tool schemas, conversation history (~2000-5000 tokens per call) | Only your task prompt is sent (~100-500 tokens) |
| **MCP tool overhead** | 100+ MCP tool definitions loaded into context (~3000-8000 tokens) | Zero MCP tools — AI uses its native tools on the remote machine |
| **Retry waste** | False retries on transient errors re-send entire context | Precise retry logic (stderr-only matching) avoids false triggers |
| **Loop waste** | No recursion protection → A→B→A burns infinite tokens | `AGENT_DELEGATE_DEPTH` blocks loops at first recursion |
| **Discovery overhead** | Protocol handshakes, Agent Card exchanges | Zero — `agents.json` is read locally, nothing sent to AI |

**Example**: To check disk usage on a remote server:
- **With MCP tools**: ~5000 tokens (tool schema loading) + ~500 tokens (prompt) = **~5500 tokens**
- **With A2A SSH Skill**: ~500 tokens (just the prompt) = **~500 tokens** → **~90% reduction**

The savings compound when you're delegating tasks throughout the day.

## End-to-End Test Results

We take reliability seriously. A2A SSH Skill has been battle-tested on a real multi-node production setup across Windows and Linux machines.

### Test Suite

Every test validates a different execution path and safety mechanism:

#### ✅ Test 1: Linux Read + Wait (Direct SSH Stdout)
**What it tests**: The fastest execution path — SSH directly streams Claude's response without any runner overhead. This is the path used for quick checks and inspections.
**How it works**: Sends a simple read-only task to the Linux node, verifies that the response comes back correctly via SSH stdout capture.
**Why it matters**: This is the most common operation. If this path fails, day-to-day delegation breaks.

#### ✅ Test 2: Linux Write + Wait (Python Runner)
**What it tests**: The full runner pipeline on Linux — SCP upload, remote runner.py launch, Claude execution with write permissions, reply.md creation, and result fetch.
**How it works**: Sends a write-mode task that creates a file on the remote machine, verifies the file was created and reply.md confirms success.
**Why it matters**: Write tasks are the core value proposition — actually modifying code, fixing bugs, creating files on remote machines.

#### ✅ Test 3: Timeout Cap Enforcement
**What it tests**: The safety mechanism that prevents runaway processes. When `--timeout-sec 99999` is passed, it should be silently clamped to 1800 seconds (30 minutes).
**How it works**: Sends a task with an absurdly high timeout, verifies the task completes normally (proving the clamp worked — if it actually waited 99999 seconds, the test would timeout).
**Why it matters**: Without this cap, a misconfigured or malicious timeout could let a remote Claude process run indefinitely, consuming API tokens for hours.

#### ✅ Test 4: Windows Read + Wait (Python Runner)
**What it tests**: Cross-platform compatibility — the Python runner executing on Windows. This covers the stdin pipe mechanism that was specifically designed to handle PowerShell + `.cmd` file argument passing issues.
**How it works**: Sends a read task to the Windows server, verifies reply.md is produced correctly.
**Why it matters**: Windows has fundamentally different process management (no `setsid`, different pipe behavior, `.cmd` batch wrapper for Claude). This test proves the unified Python runner handles all of it.

#### ✅ Test 5: Recursive Delegation Blocked
**What it tests**: The anti-loop protection. When a delegated agent is asked to re-delegate the task to another node, it must refuse — otherwise A→B→A→B loops would burn tokens infinitely.
**How it works**: Sends a task that explicitly asks the remote agent to "use agent.py to forward this task to another node." Verifies the remote agent refuses, citing the constraint.
**Why it matters**: Without this guard, a single misworded prompt could cause infinite delegation loops, each consuming a full Claude API call. This is the "token drain prevention" mechanism.

#### ✅ Test 6: No False Retry on stdout Content
**What it tests**: The retry logic's precision. The retry mechanism checks for API errors like "overloaded" — but only in stderr, not stdout. If a task's *output* contains the word "overloaded" (e.g., "the server was overloaded yesterday"), it should NOT trigger a retry.
**How it works**: Sends a task whose output naturally contains the word "overloaded", verifies it completes in one attempt without spurious retries.
**Why it matters**: False retries waste tokens and time. Previous versions checked both stdout and stderr, causing legitimate outputs to be retried 3 times unnecessarily.

### Our Test Environment

These tests were validated on a real three-node setup as an example:
- **Node A** (Coordinator): Windows 11 laptop
- **Node B** (Windows target): Windows Server with GPU
- **Node C** (Linux target): Ubuntu 24.04 running inside WSL2 on Node B

A2A SSH Skill supports **any combination** of Windows, Linux, and macOS nodes connected via SSH.

### Running the Tests

```bash
# Run all tests against your target node
./tests/e2e-test.sh my-server

# Or run individual tests manually
python agent.py send my-server --cwd "/" --mode read --wait --text 'echo "hello"'
```

## Configuration

### `agents.json` — Your Agent Network

```json
{
  "protocol_version": 2,
  "agents": {
    "my-laptop": {
      "hostname_patterns": ["MY-LAPTOP-*"],
      "platform": "windows",
      "claude_path": "claude",
      "python_path": "python",
      "job_root": "C:/Users/me/exchange/jobs",
      "ssh_from": { "gpu-server": "laptop-ssh" }
    },
    "gpu-server": {
      "hostname_patterns": ["GPU-*"],
      "platform": "linux",
      "claude_path": "/usr/local/bin/claude",
      "python_path": "python3",
      "job_root": "/home/user/exchange/jobs",
      "ssh_from": { "my-laptop": "gpu-ssh" }
    }
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `hostname_patterns` | Yes | Glob patterns to auto-detect which node this is (matched against `socket.gethostname()`) |
| `platform` | Yes | `"windows"` or `"linux"` — determines path normalization and process management |
| `claude_path` | Yes | Full path to the AI CLI executable on this node |
| `python_path` | Yes | Python interpreter for running the job runner |
| `job_root` | Yes | Directory where job folders are created |
| `ssh_from` | Yes | Map of `{source_agent: ssh_host_alias}`. `null` = same-machine access (WSL) |
| `exchange_root` | No | Root directory for the exchange filesystem |
| `relay_via` | No | Fallback relay node when direct SSH fails |
| `wsl_distro` | No | WSL distribution name (for Windows→WSL routing) |
| `capabilities` | No | Tags describing what this node can do |

See [agents.example.json](agents.example.json) for a fully commented template, and [examples/](examples/) for ready-to-use two-node and three-node setups.

## Commands

```bash
# Send a task
python agent.py send <target> --cwd <path> --text "task" --mode read|write [--wait] [--timeout-sec N]

# Check job status
python agent.py status <job-id> [--detail]

# Clean up old completed jobs
python agent.py cleanup [--days 7]
```

## Roadmap

- [ ] 📦 **Standalone CLI** — `pip install a2a-ssh-skill` for global installation
- [ ] 🤖 **More AI CLI adapters** — Codex, Gemini CLI, Aider, Ollama integration guides
- [ ] 📊 **Web dashboard** — Real-time job monitoring and history
- [ ] 🌐 **A2A protocol bridge** — Optional Google A2A compatibility layer
- [ ] 🔄 **Job chaining** — Automatic multi-step workflows (A→B→C)
- [ ] 📱 **Notification hooks** — Slack/Telegram alerts on job completion

### Design Principles We'll Never Compromise

| Principle | How We Achieve It |
|-----------|-------------------|
| 💰 **Low token consumption** | Only prompt text is transmitted — no model context, no conversation history, no framework overhead |
| 🎯 **High accuracy** | Task results delivered as structured files (`reply.md`), not chat-style fuzzy output |
| 🔍 **Full explainability** | Every job has complete `log.md` with execution trace, timestamps, exit codes, and stderr capture |
| 🪶 **Zero bloat** | No dependencies today, no dependencies tomorrow. Python stdlib is enough. |

## FAQ

<details>
<summary><b>💡 How is this different from Google A2A?</b></summary>
<br/>
Google A2A is a <b>protocol specification</b> for agent interoperability — like HTTP for agents. It defines how agents should discover each other (Agent Cards), communicate (JSON-RPC), and exchange tasks.

A2A SSH Skill is a <b>practical tool</b> that makes agents delegate work right now, using SSH. No protocol endpoints to implement, no Agent Cards to publish.

Think of it as: A2A is the spec for the future. A2A SSH Skill is the tool for today. They're complementary — you could use A2A for discovery and A2A SSH Skill for execution.
</details>

<details>
<summary><b>🤖 Does it only work with Claude Code?</b></summary>
<br/>
No! A2A SSH Skill works with <b>any CLI AI tool</b> that accepts a <code>-p</code> (prompt) flag and can use file tools (Read, Write, Bash). This includes Claude Code, OpenAI Codex, Aider, and potentially others.

The <code>claude_path</code> in your config can point to any compatible CLI binary.
</details>

<details>
<summary><b>☁️ Do I need cloud services?</b></summary>
<br/>
No. A2A SSH Skill runs entirely over SSH between your own machines. No cloud APIs (beyond the AI model API itself), no SaaS platforms, no third-party services. Your prompts and task results stay on your machines.
</details>

<details>
<summary><b>🔄 How is this different from just SSH-ing and running commands?</b></summary>
<br/>
A2A SSH Skill adds structured task delivery (<code>prompt.md</code>), result collection (<code>reply.md</code>), execution logging (<code>log.md</code>), automatic routing, timeout protection, recursion guards, and cross-platform compatibility.

It's the difference between raw TCP sockets and HTTP — same transport, much better protocol.
</details>

<details>
<summary><b>➕ Can I add more nodes?</b></summary>
<br/>
Yes! Just add entries to <code>agents.json</code>. Each node auto-detects its identity via hostname matching. A2A SSH Skill supports direct SSH connections, relay routing through intermediate nodes (A→B→C), and shared filesystem access (Windows host + its WSL).
</details>

<details>
<summary><b>🔒 Is it secure?</b></summary>
<br/>
A2A SSH Skill inherits SSH's security model — all communication is encrypted. No additional ports need to be opened. No HTTP endpoints are exposed. The <code>--dangerously-skip-permissions</code> flag is used for non-interactive AI execution on remote nodes, which is an architectural necessity for headless agent operation, not a security bypass.
</details>

## Contributing

Contributions are welcome! Whether it's bug reports, feature requests, documentation improvements, or code contributions.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT](LICENSE) — use it however you want.

---

<div align="center">
  <br/>
  <strong>If your agent can SSH, your agent can scale. 🚀</strong>
  <br/><br/>
  <sub>Not an official Google A2A implementation.<br/>Inspired by the <a href="https://github.com/a2aproject/A2A">Agent2Agent</a> vision, built for builders who need it working today.</sub>
  <br/><br/>
  <a href="https://github.com/YonganZhang/a2a-ssh-skill">⭐ Star this repo</a> if it saved you from deploying an HTTP server.
</div>
