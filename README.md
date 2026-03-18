<div align="center">

  <img src="docs/assets/logo.svg" width="112" alt="A2A SSH Skill Logo" />

  <h1>A2A SSH Skill</h1>

  <p>
    <strong>Agent-to-Agent delegation over SSH.</strong><br/>
    <strong>Zero dependencies. Works today.</strong>
  </p>

  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT" /></a>
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/E2E_Tests-6%2F6_Passing-brightgreen" alt="Tests" />
    <img src="https://img.shields.io/badge/Dependencies-Zero-orange" alt="Deps" />
    <img src="https://img.shields.io/badge/Claude_Code-Compatible-black" alt="Claude" />
    <img src="https://img.shields.io/badge/Codex-Compatible-black" alt="Codex" />
  </p>

  <p>
    <sub>Inspired by <a href="https://github.com/a2aproject/A2A">Google Agent2Agent (A2A) Protocol</a> · Built for builders who need it working today</sub>
  </p>

</div>

<br/>

<div align="center">

> **💬 Tired of 100+ MCP tools burning tokens just to talk across machines?**<br/>
> **Google A2A wants you to build an HTTP server. We just need your SSH key. 🔑**

</div>

<br/>

<div align="center">
<table>
<tr>
<td align="center" width="260">
  <h3>💰 ~90% Less Tokens</h3>
  <p>No framework context. No MCP overhead.<br/>Only your prompt travels over the wire.</p>
</td>
<td align="center" width="260">
  <h3>⚡ 5 Min Setup</h3>
  <p>Clone → edit JSON → send task.<br/>No servers. No SDKs. No <code>pip install</code>.</p>
</td>
<td align="center" width="260">
  <h3>🔒 Zero Attack Surface</h3>
  <p>No HTTP endpoints exposed.<br/>SSH encryption out of the box.</p>
</td>
</tr>
</table>
</div>

---

## 📖 What is A2A SSH Skill?

**A2A SSH Skill** is a practical, zero-dependency Python tool for [Agent2Agent (A2A)](https://github.com/a2aproject/A2A)-style delegation over SSH.

Google A2A defines a protocol for how agents *should* talk (JSON-RPC, HTTP endpoints, Agent Cards). **A2A SSH Skill makes agents *actually work* across your machines right now** — using nothing but SSH, Python, and a CLI AI tool like [Claude Code](https://claude.ai/claude-code) or [Codex](https://openai.com/codex).

> *Others are writing protocol specifications — your agents are already getting work done.*<br/>
> *Others are deploying Agent Cards and webhook endpoints — your agents already finished the task.*<br/>
> *Others spent a week on interoperability — you spent 5 minutes editing `agents.json`.*

---

## 🔄 Why A2A SSH Skill?

A2A SSH Skill and Google A2A are **complementary, not competing**:

- **Google A2A** → *"How should agents discover each other across the internet?"*
- **A2A SSH Skill** → *"How do I make my machines work together as an AI team right now?"*

<table>
<tr>
  <th width="180"></th>
  <th width="300">🔀 A2A SSH Skill</th>
  <th width="300">🌐 Google A2A Protocol</th>
</tr>
<tr><td><b>What it is</b></td><td>Ready-to-use delegation tool</td><td>Interoperability protocol spec</td></tr>
<tr><td><b>Setup time</b></td><td>⚡ 5 minutes</td><td>Hours to days</td></tr>
<tr><td><b>Dependencies</b></td><td>Python stdlib + SSH</td><td>HTTP server + JSON-RPC + SDK</td></tr>
<tr><td><b>Infrastructure</b></td><td>Your existing SSH keys</td><td>Agent Cards + HTTP endpoints + webhooks</td></tr>
<tr><td><b>Transport</b></td><td>SSH (encrypted by default)</td><td>HTTP/HTTPS</td></tr>
<tr><td><b>Discovery</b></td><td><code>agents.json</code></td><td>Agent Card metadata</td></tr>
<tr><td><b>Cross-machine</b></td><td>✅ Native design goal</td><td>Possible, you build the infra</td></tr>
<tr><td><b>Task artifacts</b></td><td>✅ Built-in files</td><td>Not provided</td></tr>
<tr><td><b>Failure recovery</b></td><td>✅ Timeout, recursion guard, zombie cleanup</td><td>Up to implementer</td></tr>
<tr><td><b>Token efficiency</b></td><td>✅ Prompt-only, ~90% less</td><td>Depends on impl</td></tr>
<tr><td><b>Explainability</b></td><td>✅ Full <code>log.md</code> trace</td><td>Depends on impl</td></tr>
<tr><td><b>Best for</b></td><td><b>Getting work done today</b></td><td>Cross-vendor ecosystem interop</td></tr>
</table>

> **TL;DR** — Need your machines working as an AI team? **A2A SSH Skill, 5 minutes.** Need a public agent marketplace? Use Google A2A.

---

## 🎬 Demo

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  $ python agent.py send gpu-server \                          │
│      --cwd "/home/user/ml-project" \                          │
│      --text "Run the failing tests and fix them" \            │
│      --mode write --wait                                      │
│                                                               │
│  ── Behind the scenes ──────────────────────────────────────  │
│                                                               │
│  1. Creates job dir → prompt.md + meta.json + runner.py       │
│  2. Uploads to gpu-server via SCP                             │
│  3. Launches runner.py via SSH                                │
│  4. Remote AI reads code, runs tests, fixes bugs              │
│  5. Writes reply.md + log.md                                  │
│  6. Results fetched back                                      │
│                                                               │
│  ✅ [OK]                                                      │
│  Fixed 3 failing tests in src/utils.py:                       │
│  - test_parse_config: added missing default value             │
│  - test_validate_input: boundary check was off by one         │
│  - test_export_data: file path used wrong separator           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

**Prerequisites:** Python 3.10+ · SSH access · A CLI AI tool on remote machine

```bash
# 1. Clone (no pip install needed!)
git clone https://github.com/YonganZhang/a2a-ssh-skill && cd a2a-ssh-skill

# 2. Configure
cp agents.example.json agents.json    # Edit: SSH hosts, claude_path, python_path

# 3. Send your first task
python agent.py send my-server \
  --cwd "/home/user" \
  --text "Check Python version and disk usage" \
  --mode read --wait
```

**As a Claude Code Skill** — copy to `~/.claude/skills/` and Claude auto-discovers it:

```bash
cp -r a2a-ssh-skill ~/.claude/skills/agent-task-delegate
```

---

## 💡 Use Cases

| | Scenario | Example Prompt |
|---|---|---|
| 🧪 | **Remote testing** | *"Run the test suite on the server and fix any failures"* |
| 🔧 | **Remote debugging** | *"Check why the API returns 500 errors"* |
| 🤖 | **GPU offloading** | *"Train this model on the GPU server, report metrics"* |
| 📊 | **Cross-machine inspection** | *"Compare configs between staging and production"* |
| 🏗️ | **Multi-node deployment** | *"Update the service on server A, verify from server B"* |
| 🐛 | **Log analysis** | *"Search nginx logs for timeout errors"* |
| 📦 | **Build delegation** | *"Compile on the Linux box, it's faster there"* |
| 🔍 | **Security audit** | *"Check open ports and running services"* |

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🪶 | **Zero Dependencies** | Python stdlib only. No `pip install`. Just copy and run. |
| 🖥️ | **Cross-Platform** | Windows · Linux · WSL · macOS. One unified Python runner. |
| ⚡ | **Fast Path** | Read-only Linux tasks stream via SSH stdout — zero runner overhead. |
| 🛡️ | **Battle-Tested** | Recursion guard · timeout cap · process-group kill · atomic writes. |
| 📄 | **Observable** | `prompt.md` · `reply.md` · `log.md` — human-readable, grep-able, diff-able. |
| 🔀 | **Flexible Routing** | Direct SSH · relay (A→B→C) · shared filesystem. |
| 🤖 | **AI-Agnostic** | Claude Code, Codex, Aider — any CLI AI with `-p` flag. |
| 🔒 | **Anti-Loop** | `AGENT_DELEGATE_DEPTH` blocks infinite delegation loops. |
| 💰 | **Token Efficient** | Prompt-only transmission. No context, no history, no overhead. |

---

## 🏗️ Architecture

```
  ┌───────────────┐                         ┌───────────────┐
  │   Node A       │          SSH            │   Node B       │
  │   (Dispatcher) │                         │   (Executor)   │
  │                │  1. Upload job (SCP)     │                │
  │   agent.py     │ ─────────────────────►  │   runner.py    │
  │                │                         │                │
  │   Creates:     │  2. Launch runner (SSH)  │   Invokes:     │
  │   · prompt.md  │ ─────────────────────►  │   AI CLI tool  │
  │   · meta.json  │                         │   via stdin     │
  │   · runner.py  │  3. Fetch results (SCP) │                │
  │                │ ◄─────────────────────  │   Produces:    │
  │   Receives:    │                         │   · reply.md   │
  │   · reply.md   │                         │   · log.md     │
  │   · log.md     │                         │   · output/    │
  └───────────────┘                         └───────────────┘
```

### Execution Paths

| Target | Mode | Wait | Path | Speed |
|:-------|:-----|:-----|:-----|:------|
| Linux | read | yes | **Direct SSH stdout** | ⚡ Fastest |
| Linux | read | no | Python runner | Fast |
| Linux | write | * | Python runner | Fast |
| Windows | * | * | Python runner | Fast |

### Topology

A2A SSH Skill works with **any number of nodes** in any topology:

```
Two-Node            Three-Node (Relay)              Fan-Out
                                                     ┌─► 🖥️ Server A
💻 ── SSH ──► 🖥️    💻 ── SSH ──► 🖥️ ── WSL ──► 🐧    💻 ──┼─► 🖥️ Server B
                                                     └─► 🐧 GPU Box
```

Add nodes by editing `agents.json`. Each node auto-detects its identity. Any node can be sender, receiver, or both.

---

## ⚙️ How It Works

### Job Protocol

Every delegation creates a self-contained **job directory**:

```
jobs/<job-id>/
├── prompt.md      📝 Task instructions
├── meta.json      ⚙️ Metadata (target, mode, timeout)
├── runner.py      🏃 Bundled executor
├── reply.md       ✅ Result: [OK] or [FAILED]
├── log.md         📋 Execution trace
├── input/         📁 Input files (optional)
└── output/        📁 Generated artifacts (optional)
```

**Everything is plain text.** Debug with `cat`. Monitor with `watch`. Archive with `tar`. Search with `grep`.

### Flow

```
You type a command
  └─► agent.py detects your node, creates job dir
        └─► SCP uploads to remote machine
              └─► SSH launches runner.py
                    └─► runner.py pipes prompt to AI via stdin
                          └─► AI executes task, writes reply.md + log.md
                                └─► agent.py fetches results via SCP
                                      └─► You see the result
```

### Safety

| Mechanism | Prevents |
|:----------|:---------|
| `AGENT_DELEGATE_DEPTH` | Infinite A→B→A loops (token drain) |
| `MAX_TIMEOUT_SEC = 1800` | Runaway processes |
| `os.setsid` + `os.killpg` | Zombie processes on SSH disconnect |
| Atomic file writes | Reading half-written results |
| Preflight checks | Launching on bad remote state |
| D-state monitoring | Stalled WSL instances |

---

## 💰 Token Efficiency: ~90% Less

| Waste Source | Traditional | A2A SSH Skill |
|:-------------|:-----------|:--------------|
| Framework context injection | ~2000-5000 tokens/call | **0** (no framework) |
| MCP tool definitions | ~3000-8000 tokens | **0** (native tools on remote) |
| False retries | Re-sends entire context | Stderr-only matching |
| Delegation loops | Infinite token burn | Blocked at first recursion |
| Discovery handshakes | Agent Cards exchange | **0** (local `agents.json`) |

**Concrete example** — checking disk usage on a remote server:

| Approach | Tokens Used |
|:---------|:-----------|
| MCP tools (tool schemas + prompt) | ~5,500 |
| **A2A SSH Skill** (prompt only) | **~500** |
| **Savings** | **~90%** |

---

## 🧪 End-to-End Test Results

<table>
<tr><td>✅</td><td><b>Test 1: Linux Read + Wait</b></td><td>Direct SSH stdout path — the fastest, most common operation. Verifies response streams correctly without runner overhead.</td></tr>
<tr><td>✅</td><td><b>Test 2: Linux Write + Wait</b></td><td>Full runner pipeline — SCP upload, remote launch, Claude execution with write permissions, reply.md creation, result fetch.</td></tr>
<tr><td>✅</td><td><b>Test 3: Timeout Cap</b></td><td>Passes <code>--timeout-sec 99999</code>, verifies it's silently clamped to 1800s. Prevents runaway processes consuming tokens for hours.</td></tr>
<tr><td>✅</td><td><b>Test 4: Windows Read + Wait</b></td><td>Cross-platform — Python runner on Windows via stdin pipe. Proves the unified runner handles Windows process management correctly.</td></tr>
<tr><td>✅</td><td><b>Test 5: Recursion Blocked</b></td><td>Asks delegated agent to re-delegate. It refuses — preventing A→B→A infinite loops that would burn tokens endlessly.</td></tr>
<tr><td>✅</td><td><b>Test 6: No False Retry</b></td><td>Output containing "overloaded" doesn't trigger retry. Only stderr errors do. Prevents wasting tokens on spurious retries.</td></tr>
</table>

**Test environment:** Windows laptop ↔ Windows Server ↔ Ubuntu Linux — but A2A SSH Skill supports **any OS combination** over SSH.

```bash
# Run tests yourself
./tests/e2e-test.sh my-server
```

---

## 📝 Configuration

```json
{
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

<details>
<summary><b>📋 Full field reference</b></summary>
<br/>

| Field | Required | Description |
|:------|:---------|:-----------|
| `hostname_patterns` | Yes | Glob patterns for auto-detection (`socket.gethostname()`) |
| `platform` | Yes | `"windows"` or `"linux"` |
| `claude_path` | Yes | Path to AI CLI executable |
| `python_path` | Yes | Python interpreter for runner |
| `job_root` | Yes | Job directory location |
| `ssh_from` | Yes | `{source: ssh_alias}` map. `null` = same machine |
| `exchange_root` | No | Exchange filesystem root |
| `relay_via` | No | Fallback relay node |
| `wsl_distro` | No | WSL distribution name |
| `capabilities` | No | Node capability tags |

</details>

See [agents.example.json](agents.example.json) for a commented template · [examples/](examples/) for ready-to-use setups.

---

## 📌 Commands

```bash
# Delegate a task
python agent.py send <target> --cwd <path> --text "task" --mode read|write [--wait] [--timeout-sec N]

# Check status
python agent.py status <job-id> [--detail]

# Clean up old jobs
python agent.py cleanup [--days 7]
```

---

## 🗺️ Roadmap

| Status | Feature |
|:------:|:--------|
| 📦 | **Standalone CLI** — `pip install a2a-ssh-skill` |
| 🤖 | **More AI adapters** — Codex, Gemini CLI, Aider, Ollama |
| 📊 | **Web dashboard** — real-time job monitoring |
| 🌐 | **A2A bridge** — optional Google A2A compatibility |
| 🔄 | **Job chaining** — multi-step workflows (A→B→C) |
| 📱 | **Notifications** — Slack/Telegram on completion |

### Design Principles

| | Principle | How |
|---|---|---|
| 💰 | **Low token consumption** | Prompt-only transmission — no context, no history |
| 🎯 | **High accuracy** | File-based results (`reply.md`), not chat-style output |
| 🔍 | **Full explainability** | Complete `log.md` with timestamps and exit codes |
| 🪶 | **Zero bloat** | No dependencies today. No dependencies tomorrow. |

---

## ❓ FAQ

<details>
<summary><b>💡 How is this different from Google A2A?</b></summary>
<br/>
Google A2A is a <b>protocol spec</b> (like HTTP for agents). A2A SSH Skill is a <b>practical tool</b> that works over SSH right now. They're complementary — A2A for discovery, A2A SSH Skill for execution.
</details>

<details>
<summary><b>🤖 Does it only work with Claude?</b></summary>
<br/>
No. Any CLI AI with a <code>-p</code> flag works: Claude Code, Codex, Aider, etc. Set <code>claude_path</code> in config to your tool's binary.
</details>

<details>
<summary><b>☁️ Do I need cloud services?</b></summary>
<br/>
No. Everything runs over SSH between your own machines. Your prompts and results stay on your hardware.
</details>

<details>
<summary><b>🔄 How is this better than raw SSH?</b></summary>
<br/>
A2A SSH Skill adds: structured task delivery, result collection, execution logging, auto-routing, timeout protection, recursion guards, and cross-platform compatibility. Same transport, much better protocol.
</details>

<details>
<summary><b>➕ How many nodes can I have?</b></summary>
<br/>
No limit. Add entries to <code>agents.json</code>. Supports direct SSH, relay routing (A→B→C), shared filesystem, and any mix of Windows/Linux/macOS.
</details>

<details>
<summary><b>🔒 Is it secure?</b></summary>
<br/>
Yes — inherits SSH's encryption. No HTTP endpoints exposed, no extra ports opened. The <code>--dangerously-skip-permissions</code> flag enables non-interactive AI execution, which is architecturally required for headless operation.
</details>

---

## 🤝 Contributing

Contributions welcome! Bug reports, feature requests, docs, code — all appreciated.

1. Fork → 2. Branch → 3. Commit → 4. Push → 5. PR

---

## 📄 License

[MIT](LICENSE) — use it however you want.

---

<div align="center">
  <br/>
  <b>If your agent can SSH, your agent can scale. 🚀</b>
  <br/><br/>
  <sub>
    Not an official Google A2A implementation.<br/>
    Inspired by the <a href="https://github.com/a2aproject/A2A">Agent2Agent</a> vision, built for builders who need it working today.
  </sub>
  <br/><br/>
  <a href="https://github.com/YonganZhang/a2a-ssh-skill">⭐ Star this repo</a> if it saved you from deploying an HTTP server.
</div>
