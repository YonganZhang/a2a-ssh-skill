#!/usr/bin/env python3
"""Unified cross-platform runner for delegated AI jobs.

Replaces agent-runner-win.ps1 and agent-runner-wsl.sh.
Uses subprocess.Popen + stdin pipe — consistent behavior on Windows and Linux.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

MAX_TIMEOUT_SEC = 1800


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def atomic_write(path: Path, content: str) -> None:
    """Write via temp file + rename to avoid reading half-written files."""
    tmp = path.with_suffix(".tmp")
    write_text(tmp, content)
    shutil.move(str(tmp), str(path))


def append_text(path: Path, content: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(content)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %z").strip()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: agent-runner.py <job_dir>", file=sys.stderr)
        return 1

    job_dir = Path(sys.argv[1]).resolve()
    meta_path = job_dir / "meta.json"
    prompt_path = job_dir / "prompt.md"
    reply_path = job_dir / "reply.md"
    log_path = job_dir / "log.md"
    output_dir = job_dir / "output"

    # --- Validate ---
    if not meta_path.exists():
        print(f"Missing meta.json: {meta_path}", file=sys.stderr)
        return 1
    if not prompt_path.exists():
        print(f"Missing prompt.md: {prompt_path}", file=sys.stderr)
        return 1

    meta = json.loads(read_text(meta_path))
    prompt_text = read_text(prompt_path)

    cwd = meta.get("cwd", ".")
    mode = meta.get("mode", "read")
    job_id = meta.get("id", job_dir.name)
    timeout_sec = min(int(meta.get("timeout_sec", 300)), MAX_TIMEOUT_SEC)
    claude_path = meta.get("claude_path", "claude")
    callback_host = meta.get("callback_host")
    callback_job_root = meta.get("callback_job_root")

    # --- Write initial log ---
    write_text(log_path, (
        "# Execution Log\n\n"
        f"## Started\n{now_str()}\n\n"
        f"## Node\n{socket.gethostname()}\n\n"
        f"## Working Directory\n{cwd}\n\n"
        f"## Mode\n{mode}\n"
    ))

    # --- Build delegated prompt ---
    delegated_prompt = (
        "You are running inside a delegated job.\n"
        "You must NOT delegate this task further. Execute everything directly on this node.\n"
        "\n"
        f"Job directory: {job_dir}\n"
        f"Reply file: {reply_path}\n"
        f"Log file: {log_path}\n"
        f"Output directory: {output_dir}\n"
        f"Working directory: {cwd}\n"
        "\n"
        "MANDATORY: You must write the final result to the exact reply file path above.\n"
        "MANDATORY: You must write execution notes to the exact log file path above.\n"
        "You must put generated files inside the exact output directory above.\n"
        "Do not write these deliverables anywhere else.\n"
        "Writing reply.md and log.md is REQUIRED regardless of any 'do not modify files' "
        "constraint in the task below. That constraint only applies to files in the working directory.\n"
        "\n"
        "The original task instructions follow.\n"
        "\n"
        "----- prompt.md -----\n"
        f"{prompt_text}"
    )

    # --- Run Claude ---
    env = os.environ.copy()
    env["AGENT_DELEGATE_DEPTH"] = "1"
    # Remove vars that confuse nested Claude instances
    for key in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"):
        env.pop(key, None)

    cmd = [claude_path, "--dangerously-skip-permissions", "-p", "-"]

    # On Linux, use setsid to detach from controlling tty (prevents SIGHUP zombies)
    preexec = os.setsid if hasattr(os, "setsid") else None

    timed_out = False
    exit_code = -1

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            preexec_fn=preexec,
            text=True,
        )

        # Timeout watchdog — kills process group on Linux, process on Windows
        def kill_on_timeout():
            nonlocal timed_out
            timed_out = True
            try:
                if hasattr(os, "killpg"):
                    os.killpg(proc.pid, 9)
                else:
                    proc.kill()
            except OSError:
                pass

        timer = threading.Timer(timeout_sec, kill_on_timeout)
        timer.start()

        try:
            _, stderr_output = proc.communicate(input=delegated_prompt)
            exit_code = proc.returncode
        finally:
            timer.cancel()

        # Log errors
        if timed_out:
            append_text(log_path, f"\n## Error\nclaude timed out after {timeout_sec}s\n")
        elif exit_code != 0:
            error_detail = (stderr_output or "").strip()[:500]
            append_text(log_path, f"\n## Error\nclaude exited with code {exit_code}\n")
            if error_detail:
                append_text(log_path, f"stderr: {error_detail}\n")

    except FileNotFoundError:
        append_text(log_path, f"\n## Error\nclaude not found at: {claude_path}\n")
    except Exception as exc:
        append_text(log_path, f"\n## Error\n{type(exc).__name__}: {exc}\n")

    # --- Ensure reply.md exists ---
    if not reply_path.exists():
        atomic_write(reply_path, (
            "[FAILED]\n\n"
            "# Summary\n"
            "Remote runner finished without producing reply.md.\n\n"
            "## Findings or Actions\n"
            "- The delegated AI did not write reply.md.\n\n"
            "## Changed Files\n- unknown\n\n"
            "## Outputs\n- none\n\n"
            "## Next Step\n"
            "Check log.md and rerun with a narrower prompt.\n"
        ))
    else:
        # Prepend [OK] if no sentinel
        content = read_text(reply_path)
        first_line = content.lstrip("\ufeff").split("\n", 1)[0].strip()
        if first_line not in ("[OK]", "[FAILED]"):
            atomic_write(reply_path, f"[OK]\n\n{content}")

    # --- Finished timestamp ---
    append_text(log_path, f"\n## Finished\n{now_str()}\n")

    # --- Callback pushback ---
    if callback_host and callback_job_root:
        remote_dir = f"{callback_host}:{callback_job_root}/{job_id}"
        for filename in ("reply.md", "log.md"):
            local = job_dir / filename
            if local.exists():
                result = subprocess.run(
                    ["scp", str(local), f"{remote_dir}/{filename}"],
                    check=False, capture_output=True, timeout=30,
                )
                if result.returncode != 0:
                    append_text(log_path, f"\n## Pushback\nCallback copy failed for {filename}\n")

    return 0 if not timed_out and exit_code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
