# Quick Start Guide

## Prerequisites

- **Python 3.10+** on all machines (no pip packages needed)
- **SSH access** between machines (key-based auth recommended)
- **An AI CLI tool** on remote machines (e.g., [Claude Code](https://claude.ai/claude-code), [Codex](https://openai.com/codex))

## Step 1: Clone

```bash
git clone https://github.com/YonganZhang/agent-relay
cd agent-relay
```

## Step 2: Configure Nodes

```bash
cp agents.example.json agents.json
```

Edit `agents.json` to match your setup. Here's a minimal two-node example:

```json
{
  "protocol_version": 2,
  "agents": {
    "my-laptop": {
      "hostname_patterns": ["my-hostname"],
      "platform": "windows",
      "claude_path": "claude",
      "python_path": "python",
      "exchange_root": "C:/Users/me/exchange",
      "job_root": "C:/Users/me/exchange/jobs",
      "ssh_from": {
        "my-server": "my-laptop-ssh"
      }
    },
    "my-server": {
      "hostname_patterns": ["server-*"],
      "platform": "linux",
      "claude_path": "/usr/local/bin/claude",
      "python_path": "python3",
      "exchange_root": "/home/user/exchange",
      "job_root": "/home/user/exchange/jobs",
      "ssh_from": {
        "my-laptop": "my-server-ssh"
      }
    }
  }
}
```

Key fields:
- `hostname_patterns`: How the script auto-detects which node it's running on
- `ssh_from`: Maps `{origin_agent: ssh_host_alias}` — what SSH alias to use from each source
- `claude_path`: Full path to your AI CLI executable
- `python_path`: Full path to Python (needed for running the job runner)

## Step 3: Verify SSH

Make sure you can SSH from your laptop to your server:

```bash
ssh my-server-ssh "echo ok"
```

## Step 4: Send Your First Task

```bash
# Read-only task (fastest — uses direct SSH stdout)
python agent.py send my-server --cwd "/home/user" \
    --text "What Python version is installed?" --mode read --wait

# Write task (uses Python runner on remote)
python agent.py send my-server --cwd "/home/user/project" \
    --text "Fix the failing tests in test_utils.py" --mode write --wait
```

## Step 5: Check Job Status

```bash
# List recent jobs
ls -lt ~/exchange/jobs/ | head -5

# Check a specific job
python agent.py status <job-id> --detail
```

## Step 6: Clean Up Old Jobs

```bash
python agent.py cleanup --days 7
```

## Using as a Claude Code Skill

AgentRelay can also be installed as a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code):

```bash
# Copy to your Claude Code skills directory
cp -r agent-relay ~/.claude/skills/agent-task-delegate
```

Then Claude Code will automatically use it when you ask it to delegate tasks to remote machines.

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues and solutions.
