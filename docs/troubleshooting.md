# Troubleshooting

## Common Issues

### "Cannot determine local agent"

**Cause**: Your machine's hostname doesn't match any `hostname_patterns` in agents.json.

**Fix**:
```bash
# Check your hostname
hostname
# Add it to agents.json, or set the env var:
export AGENT_RELAY_LOCAL_AGENT=my-laptop
```

### Runner produces no reply.md

**Symptoms**: log.md exists with "Started" but no "Error" or "Finished" section.

**Diagnosis**:
1. Check for zombie Claude processes on the remote machine:
   ```bash
   ssh my-server "ps aux | grep claude | grep -v grep"
   ```
2. Kill any zombies:
   ```bash
   ssh my-server "pkill -9 -f claude"
   ```
3. Verify Claude CLI works on the remote machine:
   ```bash
   ssh my-server "claude --version"
   ```

### SSH timeout

**Symptoms**: "Runner launch timed out" error.

**Possible causes**:
- Remote machine is slow or overloaded
- SSH connection is unreliable
- Claude CLI is taking too long

**Fix**: Increase timeout:
```bash
python agent.py send my-server --timeout-sec 600 ...
```

### "python" not found on remote

**Symptoms**: Runner fails immediately, no log.md created.

**Fix**: Set the correct Python path in agents.json:
```json
"python_path": "/usr/bin/python3"
```

### Windows: Claude doesn't write reply.md

**Historical note**: This was caused by PowerShell's `| Out-Null` making Claude think it was in a pipe. The unified Python runner eliminated this issue entirely by using `subprocess.Popen` with stdin pipe.

### Linux: Zombie Claude processes

**Historical note**: SSH's `-tt` flag created pseudo-TTYs. When SSH disconnected, SIGHUP put Claude's Node.js into "stopped" state, unkillable by timeout. Fixed with `os.setsid` in the Python runner — Claude runs in its own process group, detached from the TTY.

## Debug Checklist

1. **Check log.md** — The Error section captures exit codes and stderr
2. **Check dispatch.log** — Shows routing decisions and preflight results
3. **Verify SSH** — `ssh <host> "echo ok"`
4. **Verify Claude** — `ssh <host> "claude --version"`
5. **Verify Python** — `ssh <host> "python3 --version"`
6. **Check for zombies** — `ssh <host> "ps aux | grep claude"`
