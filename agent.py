#!/usr/bin/env python3
"""Cross-node AI delegation CLI — supports bidirectional routing between any pair of nodes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import shlex
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("AGENT_RELAY_CONFIG", str(SCRIPT_DIR / "agents.json")))
POLL_INTERVAL_SECONDS = 15
WSL_DSTATE_THRESHOLD = 10
READ_RETRY_ATTEMPTS = 3


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "job"


def run(
    cmd: list[str],
    *,
    check: bool = True,
    capture: bool = True,
    input_text: str | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        input=input_text,
        timeout=timeout,
        errors="replace",
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def bash_quote(value: str) -> str:
    return shlex.quote(value)


def strip_terminal_noise(text: str) -> str:
    text = re.sub(r"\x1b\][^\x07]*\x07", "", text)
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = text.replace("\r", "")
    text = re.sub(r"^Connection to .+ closed\.\n?", "", text, flags=re.MULTILINE)
    return text.strip()


def is_retryable_claude_error(stderr: str) -> bool:
    err = stderr.lower()
    return "api error: 500" in err or '"type":"api_error"' in err or "overloaded" in err


def normalize_linux_cwd(cwd: str) -> str:
    normalized = cwd.strip().replace("\\", "/")
    git_prefix = re.match(r"^(?i:[a-z]:)/Program Files/Git(?P<rest>/.*)$", normalized)
    if git_prefix:
        normalized = git_prefix.group("rest")

    drive_path = re.match(r"^(?P<drive>[a-zA-Z]):/(?P<rest>.*)$", normalized)
    if drive_path:
        drive = drive_path.group("drive").lower()
        rest = drive_path.group("rest").strip("/")
        return f"/mnt/{drive}/{rest}" if rest else f"/mnt/{drive}"

    msys_drive = re.match(r"^/(?P<drive>[a-zA-Z])/(?P<rest>.*)$", normalized)
    if msys_drive:
        drive = msys_drive.group("drive").lower()
        rest = msys_drive.group("rest").strip("/")
        return f"/mnt/{drive}/{rest}" if rest else f"/mnt/{drive}"

    return normalized or cwd


def normalize_windows_cwd(cwd: str) -> str:
    normalized = cwd.strip().replace("\\", "/")
    drive_path = re.match(r"^/mnt/(?P<drive>[a-zA-Z])/(?P<rest>.*)$", normalized)
    if drive_path:
        drive = drive_path.group("drive").upper()
        rest = drive_path.group("rest").strip("/")
        return f"{drive}:/{rest}" if rest else f"{drive}:/"

    msys_drive = re.match(r"^/(?P<drive>[a-zA-Z])/(?P<rest>.*)$", normalized)
    if msys_drive:
        drive = msys_drive.group("drive").upper()
        rest = msys_drive.group("rest").strip("/")
        return f"{drive}:/{rest}" if rest else f"{drive}:/"

    return cwd


def detect_local_agent(agents: dict[str, Any]) -> str:
    """Determine which agent we are by hostname + platform, or env var override."""
    env_override = os.environ.get("AGENT_DELEGATE_LOCAL_AGENT")
    if env_override:
        if env_override in agents:
            return env_override
        raise SystemExit(f"AGENT_DELEGATE_LOCAL_AGENT={env_override} not found in config")

    hostname = socket.gethostname().split(".")[0].lower()
    current_platform = "linux" if sys.platform.startswith("linux") else "windows"

    for agent_name, cfg in agents.items():
        if cfg.get("platform") != current_platform:
            continue
        for pattern in cfg.get("hostname_patterns", []):
            if fnmatch.fnmatch(hostname, pattern.lower()):
                return agent_name

    raise SystemExit(
        f"Cannot determine local agent: hostname={hostname}, platform={current_platform} "
        "does not match any agent in config. Set AGENT_DELEGATE_LOCAL_AGENT env var."
    )


@dataclass
class RoutePlan:
    upload_host: str | None  # None = shared filesystem, no SCP needed
    upload_job_root: str
    upload_job_dir: str
    runner_host: str | None  # None = local execution (no SSH)
    runner_command_wait: str
    runner_command_background: str
    runner_job_dir: str
    artifact_host: str | None  # None = shared filesystem
    artifact_job_dir: str
    remote_platform: str = "linux"  # platform of the upload/artifact host


class AgentCli:
    def __init__(self, config: dict[str, Any], local_agent: str) -> None:
        self.config = config
        self.local_agent = local_agent
        self.agents = config["agents"]
        self.local_cfg = self.agents[self.local_agent]

    def local_job_root(self) -> Path:
        return Path(self.local_cfg["job_root"])

    def local_archive_root(self) -> Path:
        return Path(self.local_cfg["exchange_root"]) / "archive" / "agent-jobs"

    def agent_cfg(self, target: str) -> dict[str, Any]:
        try:
            return self.agents[target]
        except KeyError as exc:
            raise SystemExit(f"Unknown target: {target}") from exc

    def get_ssh_host(self, target: str) -> str | None:
        """Resolve the SSH host to reach *target* from this node.

        Returns None when target is on the same machine (e.g. local WSL).
        """
        target_cfg = self.agent_cfg(target)
        ssh_from = target_cfg.get("ssh_from", {})
        if self.local_agent in ssh_from:
            return ssh_from[self.local_agent]
        # Fallback to legacy 'host' field
        return target_cfg.get("host")

    def valid_targets(self) -> list[str]:
        return [name for name in self.agents if name != self.local_agent]

    def normalize_cwd(self, target: str, cwd: str) -> str:
        platform = self.agent_cfg(target)["platform"]
        if platform == "linux":
            return normalize_linux_cwd(cwd)
        if platform == "windows":
            return normalize_windows_cwd(cwd)
        return cwd

    def wsl_bash_command(self, target_cfg: dict[str, Any], bash_command: str) -> str:
        distro = target_cfg.get("wsl_distro")
        distro_part = f" -d {distro}" if distro else ""
        escaped = bash_command.replace('"', '\\"')
        return f'wsl{distro_part} -- bash -lc "{escaped}"'

    def append_dispatch_log(self, job_dir: Path, title: str, lines: list[str]) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block = [f"## {title}", f"- time: {timestamp}"]
        block.extend(f"- {line}" for line in lines)
        append_text(job_dir / "dispatch.log", "\n".join(block) + "\n\n")

    def build_read_stdout_prompt(self, *, task_text: str, cwd: str, timeout_sec: int) -> str:
        return (
            "# Task\n"
            f"{task_text.strip()}\n\n"
            "## Working Directory\n"
            f"{cwd}\n\n"
            "## Constraints\n"
            "- read-only task, do not modify any files\n"
            f"- timeout_sec: {timeout_sec}\n"
            "- respond in plain text only\n"
            "- do not mention reply.md, log.md, output/, or internal job protocol\n"
            "- do not use markdown code fences unless the task explicitly asks for them\n"
            "- IMPORTANT: do NOT delegate this task to other agents or call agent.py\n"
        )

    def can_connect(self, host: str) -> bool:
        try:
            result = run(["ssh", host, "echo ok"], check=False, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and "ok" in result.stdout

    def select_route(self, target: str, requested: str) -> str:
        if requested != "auto":
            return requested

        target_cfg = self.agent_cfg(target)
        ssh_host = self.get_ssh_host(target)
        relay = target_cfg.get("relay_via")

        # No SSH needed (local WSL or same-machine target) → always direct
        if ssh_host is None:
            return "direct"

        # No relay option → must go direct
        if relay is None:
            return "direct"

        # Has relay fallback → try direct first
        if self.can_connect(ssh_host):
            return "direct"

        return f"via-{relay}"

    def create_job_id(self, target: str, title: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{stamp}-{target}-{slugify(title)[:32]}-{uuid.uuid4().hex[:6]}"

    def build_prompt(
        self,
        *,
        task_text: str,
        cwd: str,
        mode: str,
        timeout_sec: int,
        inputs: list[Path],
    ) -> str:
        input_lines = "\n".join(f"- input/{path.name}" for path in inputs) or "- none"
        if mode == "read":
            mode_rule = "do not modify files"
        else:
            mode_rule = "only modify files under the working directory"
        return (
            "# Task\n"
            f"{task_text.strip()}\n\n"
            "## Context\n"
            f"This task was delegated from {self.local_agent}. Use the local environment on this node.\n\n"
            "## Working Directory\n"
            f"{cwd}\n\n"
            "## Constraints\n"
            f"- mode: {mode}\n"
            f"- timeout_sec: {timeout_sec}\n"
            f"- if mode={mode}, {mode_rule}\n"
            "- do not modify rules/skills/settings unless explicitly requested\n"
            "- IMPORTANT: do NOT delegate this task to other agents or call agent.py\n\n"
            "## Inputs\n"
            f"{input_lines}\n\n"
            "## Deliverables\n"
            "- write final result to reply.md\n"
            "- write execution notes to log.md\n"
            "- put generated files in output/\n\n"
            "## Failure Handling\n"
            "- if blocked, write [FAILED] in reply.md\n"
            "- explain the blocker and the recommended next step\n"
        )

    def create_local_job(
        self,
        *,
        target: str,
        route: str,
        title: str,
        mode: str,
        cwd: str,
        timeout_sec: int,
        task_text: str,
        inputs: list[Path],
    ) -> Path:
        job_id = self.create_job_id(target, title)
        job_dir = self.local_job_root() / job_id
        job_dir.mkdir(parents=True, exist_ok=False)
        (job_dir / "input").mkdir()
        (job_dir / "output").mkdir()

        target_cfg = self.agent_cfg(target)
        meta = {
            "protocol_version": self.config.get("protocol_version", 2),
            "id": job_id,
            "created_by": self.local_agent,
            "origin_agent": self.local_agent,
            "target": target,
            "route": route,
            "relay_via": None if route == "direct" else route.replace("via-", "", 1),
            "mode": mode,
            "cwd": cwd,
            "timeout_sec": timeout_sec,
            "title": title,
            "required_capabilities": target_cfg.get("capabilities", []),
            "parent_job": None,
            "created_at": now_iso(),
            "callback_host": self.local_cfg.get("pushback_host"),
            "callback_job_root": self.local_cfg.get("pushback_job_root"),
            "claude_path": target_cfg.get("claude_path", "claude"),
        }
        write_text(job_dir / "meta.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        write_text(
            job_dir / "prompt.md",
            self.build_prompt(task_text=task_text, cwd=cwd, mode=mode, timeout_sec=timeout_sec, inputs=inputs),
        )
        # Bundle unified Python runner into job directory
        shutil.copy2(SCRIPT_DIR / "agent-runner.py", job_dir / "runner.py")

        for source in inputs:
            destination = job_dir / "input" / source.name
            if source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(source, destination)

        return job_dir

    def _run_remote_check(self, target: str, route: str, bash_command: str, timeout: int = 20) -> subprocess.CompletedProcess[str]:
        """Run a bash command on a remote Linux target, handling direct/local-wsl/relay routing."""
        target_cfg = self.agent_cfg(target)
        if route == "direct":
            ssh_host = self.get_ssh_host(target)
            if ssh_host is None:
                # Local WSL
                wsl_cmd = self.wsl_bash_command(target_cfg, bash_command)
                return subprocess.run(wsl_cmd, shell=True, check=False, capture_output=True, text=True, timeout=timeout)
            command = f"bash -lc {bash_quote(bash_command)}"
            return run(["ssh", ssh_host, command], check=False, timeout=timeout)
        else:
            relay_name = route.replace("via-", "", 1)
            relay_ssh_host = self.get_ssh_host(relay_name)
            if relay_ssh_host is None:
                raise SystemExit(
                    f"Relay agent '{relay_name}' has no SSH host from '{self.local_agent}'; "
                    "a local agent cannot serve as a remote relay."
                )
            command = self.wsl_bash_command(target_cfg, bash_command)
            return run(["ssh", relay_ssh_host, command], check=False, timeout=timeout)

    def preflight_target(self, target: str, route: str, cwd: str) -> None:
        target_cfg = self.agent_cfg(target)
        if target_cfg["platform"] != "linux":
            return

        d_state_count = self.remote_d_state_count(target, route)
        if d_state_count >= WSL_DSTATE_THRESHOLD:
            raise SystemExit(
                f"Remote Linux node looks unhealthy: {d_state_count} D-state processes detected. "
                "Ask the host machine to run 'wsl --shutdown' before retrying."
            )

        bash_command = (
            f"test -d {bash_quote(cwd)} || exit 11; "
            "command -v claude >/dev/null || exit 12; "
            "timeout 10s claude --version >/dev/null 2>&1 || exit 13; "
            "printf PRECHECK_OK"
        )
        result = self._run_remote_check(target, route, bash_command, timeout=20)

        if result.returncode == 0 and "PRECHECK_OK" in result.stdout:
            return

        reason_map = {
            11: f"Remote cwd does not exist: {cwd}",
            12: "claude is not available on the remote Linux node",
            13: "claude is installed but did not respond to 'claude --version' within 10 seconds",
        }
        reason = reason_map.get(result.returncode, f"remote preflight failed with exit code {result.returncode}")
        details = result.stderr.strip() or result.stdout.strip()
        if details:
            reason = f"{reason}. details: {details}"
        raise SystemExit(reason)

    def remote_d_state_count(self, target: str, route: str) -> int:
        bash_command = "ps -eo stat= | grep -c '^D'"
        result = self._run_remote_check(target, route, bash_command, timeout=15)
        output = (result.stdout or "").strip()
        try:
            return int(output or "0")
        except ValueError:
            return 0

    def run_read_job(self, *, target: str, route: str, cwd: str, prompt_text: str, timeout_sec: int) -> subprocess.CompletedProcess[str]:
        target_cfg = self.agent_cfg(target)
        claude_bin = target_cfg.get("claude_path", "claude")
        bash_command = (
            f"cd {bash_quote(cwd)} && "
            "AGENT_DELEGATE_DEPTH=1 "
            "env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT "
            f'{bash_quote(claude_bin)} --dangerously-skip-permissions --tools "Read,Grep,Glob,Bash" -p {bash_quote(prompt_text)}'
        )

        if route == "direct":
            ssh_host = self.get_ssh_host(target)
            if ssh_host is None:
                # Local WSL
                wsl_cmd = self.wsl_bash_command(target_cfg, bash_command)
                return subprocess.run(wsl_cmd, shell=True, check=False, capture_output=True, text=True, timeout=timeout_sec + 30)
            ssh_cmd = ["ssh", "-tt", ssh_host, f"bash -lc {bash_quote(bash_command)}"]
        else:
            relay_name = route.replace("via-", "", 1)
            relay_ssh_host = self.get_ssh_host(relay_name)
            if relay_ssh_host is None:
                raise SystemExit(
                    f"Relay agent '{relay_name}' has no SSH host from '{self.local_agent}'; "
                    "a local agent cannot serve as a remote relay."
                )
            ssh_cmd = ["ssh", "-tt", relay_ssh_host, self.wsl_bash_command(target_cfg, bash_command)]

        return run(ssh_cmd, check=False, timeout=timeout_sec + 30)

    def _python_runner_commands(self, job_dir: str, target: str) -> tuple[str, str]:
        """Generate wait and background commands for the unified Python runner."""
        target_cfg = self.agent_cfg(target)
        python_bin = target_cfg.get("python_path", "python3")
        runner_path = f"{job_dir}/runner.py"
        if target_cfg["platform"] == "windows":
            wait_cmd = f'"{python_bin}" "{runner_path}" "{job_dir}"'
            background_cmd = f'cmd /c start "" /b "{python_bin}" "{runner_path}" "{job_dir}"'
        else:
            wait_cmd = f"'{python_bin}' '{runner_path}' '{job_dir}'"
            background_cmd = f"nohup '{python_bin}' '{runner_path}' '{job_dir}' >/dev/null 2>&1 &"
        return wait_cmd, background_cmd

    def build_route_plan(self, target: str, route: str, job_id: str) -> RoutePlan:
        target_cfg = self.agent_cfg(target)

        if route == "direct":
            ssh_host = self.get_ssh_host(target)
            remote_job_dir = f"{target_cfg['job_root'].rstrip('/')}/{job_id}"
            wait_cmd, bg_cmd = self._python_runner_commands(remote_job_dir, target)

            if target_cfg["platform"] == "windows":
                return RoutePlan(
                    upload_host=ssh_host,
                    upload_job_root=target_cfg["job_root"],
                    upload_job_dir=remote_job_dir,
                    runner_host=ssh_host,
                    runner_command_wait=wait_cmd,
                    runner_command_background=bg_cmd,
                    runner_job_dir=remote_job_dir,
                    artifact_host=ssh_host,
                    artifact_job_dir=remote_job_dir,
                    remote_platform="windows",
                )

            # Linux target
            if ssh_host is None:
                # Local WSL — shared filesystem, no SCP needed
                local_job_dir = f"{self.local_cfg['job_root'].rstrip('/')}/{job_id}"
                wsl_wait = self.wsl_bash_command(target_cfg, wait_cmd)
                wsl_bg = self.wsl_bash_command(target_cfg, bg_cmd)
                return RoutePlan(
                    upload_host=None,
                    upload_job_root=self.local_cfg["job_root"],
                    upload_job_dir=local_job_dir,
                    runner_host=None,
                    runner_command_wait=wsl_wait,
                    runner_command_background=wsl_bg,
                    runner_job_dir=remote_job_dir,
                    artifact_host=None,
                    artifact_job_dir=local_job_dir,
                    remote_platform="linux",
                )

            # Remote Linux via SSH
            return RoutePlan(
                upload_host=ssh_host,
                upload_job_root=target_cfg["job_root"],
                upload_job_dir=remote_job_dir,
                runner_host=ssh_host,
                runner_command_wait=wait_cmd,
                runner_command_background=bg_cmd,
                runner_job_dir=remote_job_dir,
                artifact_host=ssh_host,
                artifact_job_dir=remote_job_dir,
                remote_platform="linux",
            )

        # Relay route
        relay_name = route.replace("via-", "", 1)
        relay_cfg = self.agent_cfg(relay_name)
        relay_ssh_host = self.get_ssh_host(relay_name)
        if relay_ssh_host is None:
            raise SystemExit(
                f"Relay agent '{relay_name}' has no SSH host from '{self.local_agent}'; "
                "a local agent cannot serve as a remote relay."
            )
        upload_job_dir = f"{relay_cfg['job_root'].rstrip('/')}/{job_id}"
        runner_job_dir = f"{target_cfg['job_root'].rstrip('/')}/{job_id}"
        wait_cmd, bg_cmd = self._python_runner_commands(runner_job_dir, target)
        wait_cmd = self.wsl_bash_command(target_cfg, wait_cmd)
        bg_cmd = self.wsl_bash_command(target_cfg, bg_cmd)
        return RoutePlan(
            upload_host=relay_ssh_host,
            upload_job_root=relay_cfg["job_root"],
            upload_job_dir=upload_job_dir,
            runner_host=relay_ssh_host,
            runner_command_wait=wait_cmd,
            runner_command_background=bg_cmd,
            runner_job_dir=runner_job_dir,
            artifact_host=relay_ssh_host,
            artifact_job_dir=upload_job_dir,
            remote_platform=relay_cfg["platform"],
        )

    def remote_job_exists(self, target: str, route: str, job_id: str) -> bool:
        plan = self.build_route_plan(target, route, job_id)
        if plan.upload_host is None:
            return Path(plan.upload_job_dir).exists()
        if plan.remote_platform == "windows":
            command = (
                "powershell -NoProfile -Command "
                f"\"if (Test-Path '{plan.upload_job_dir}') {{ exit 0 }} else {{ exit 1 }}\""
            )
        else:
            command = f"test -d '{plan.upload_job_dir}'"
        result = run(["ssh", plan.upload_host, command], check=False, timeout=10)
        return result.returncode == 0

    def upload_job(self, job_dir: Path, plan: RoutePlan) -> None:
        if plan.upload_host is None:
            return  # Shared filesystem, no copy needed
        destination = f"{plan.upload_host}:{plan.upload_job_root.rstrip('/\\\\')}/"
        run(["scp", "-r", str(job_dir), destination], timeout=120)

    def invoke_runner(self, plan: RoutePlan, *, wait: bool, timeout_sec: int) -> None:
        command = plan.runner_command_wait if wait else plan.runner_command_background
        timeout = timeout_sec + 60 if wait else 30
        if plan.runner_host is None:
            # Local execution (wsl command or powershell command)
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
            return
        # Don't use -tt for runner invocations — tty causes SIGHUP on SSH disconnect
        # which puts Claude's Node.js into T (stopped) state, unkillable by timeout.
        # Runner uses setsid internally so tty is not needed.
        ssh_cmd = ["ssh", plan.runner_host, command]
        run(ssh_cmd, timeout=timeout)

    def reply_exists_remote(self, plan: RoutePlan) -> bool:
        if plan.artifact_host is None:
            return (Path(plan.artifact_job_dir) / "reply.md").exists()
        if plan.remote_platform == "windows":
            command = (
                "powershell -NoProfile -Command "
                f"\"if (Test-Path '{plan.artifact_job_dir}/reply.md') {{ exit 0 }} else {{ exit 1 }}\""
            )
        else:
            command = f"test -f '{plan.artifact_job_dir}/reply.md'"
        result = run(["ssh", plan.artifact_host, command], check=False, timeout=10)
        return result.returncode == 0

    def remote_path_exists(self, plan: RoutePlan, child: str) -> bool:
        if plan.artifact_host is None:
            return (Path(plan.artifact_job_dir) / child).exists()
        if plan.remote_platform == "windows":
            command = (
                "powershell -NoProfile -Command "
                f"\"if (Test-Path '{plan.artifact_job_dir}/{child}') {{ exit 0 }} else {{ exit 1 }}\""
            )
        else:
            command = f"test -e '{plan.artifact_job_dir}/{child}'"
        result = run(["ssh", plan.artifact_host, command], check=False, timeout=10)
        return result.returncode == 0

    def fetch_job_artifacts(self, plan: RoutePlan, job_dir: Path) -> None:
        if plan.artifact_host is None:
            # Shared filesystem — files are already at job_dir
            return
        for filename in ("meta.json", "reply.md", "log.md"):
            result = run(
                ["scp", f"{plan.artifact_host}:{plan.artifact_job_dir}/{filename}", str(job_dir / filename)],
                check=False,
                timeout=30,
            )
            if result.returncode != 0:
                print(f"Warning: failed to fetch {filename} from {plan.artifact_host}", file=sys.stderr)
        if self.remote_path_exists(plan, "output"):
            result = run(
                ["scp", "-r", f"{plan.artifact_host}:{plan.artifact_job_dir}/output", str(job_dir)],
                check=False,
                timeout=60,
            )
            if result.returncode != 0:
                print(f"Warning: failed to fetch output/ from {plan.artifact_host}", file=sys.stderr)

    def wait_for_completion(self, plan: RoutePlan, job_dir: Path, timeout_sec: int) -> int:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if (job_dir / "reply.md").exists():
                return reply_exit_code(job_dir / "reply.md")
            if self.reply_exists_remote(plan):
                self.fetch_job_artifacts(plan, job_dir)
                return reply_exit_code(job_dir / "reply.md")
            time.sleep(POLL_INTERVAL_SECONDS)
        return 124


def _clean_first_line(reply_path: Path) -> str:
    """Read first line, strip BOM and whitespace."""
    raw = read_text(reply_path)
    first_line = raw.lstrip("\ufeff").splitlines()[0].strip()
    return first_line


def reply_exit_code(reply_path: Path) -> int:
    if not reply_path.exists():
        return 124
    first_line = _clean_first_line(reply_path)
    return 1 if first_line == "[FAILED]" else 0


def reply_state(reply_path: Path) -> str:
    if not reply_path.exists():
        return "RUNNING"
    first_line = _clean_first_line(reply_path)
    if first_line == "[OK]":
        return "DONE"
    if first_line == "[FAILED]":
        return "FAILED"
    return "DONE_NO_SENTINEL"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_inputs(values: list[str] | None) -> list[Path]:
    inputs: list[Path] = []
    for value in values or []:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Input path not found: {path}")
        inputs.append(path)
    return inputs


def read_prompt_source(text: str | None, prompt_file: str | None) -> str:
    if text and not prompt_file:
        return text
    if prompt_file and not text:
        return Path(prompt_file).expanduser().read_text(encoding="utf-8")
    raise SystemExit("Provide exactly one of --text or --prompt-file")


MAX_TIMEOUT_SEC = 1800


def resolve_timeout(mode: str, override: int | None) -> int:
    if override is not None:
        return min(override, MAX_TIMEOUT_SEC)
    return 180 if mode == "read" else 300


def format_status(job_dir: Path, detail: bool) -> str:
    meta = json.loads(read_text(job_dir / "meta.json"))
    reply_path = job_dir / "reply.md"
    state = reply_state(reply_path)
    lines = [
        f"id: {meta['id']}",
        f"target: {meta['target']}",
        f"route: {meta['route']}",
        f"mode: {meta['mode']}",
        f"state: {state}",
        f"cwd: {meta['cwd']}",
    ]
    if detail:
        for filename in ("dispatch.log", "reply.md", "log.md"):
            path = job_dir / filename
            if path.exists():
                lines.append(f"\n## {filename}")
                lines.append(read_text(path).strip())
    return "\n".join(lines)


def cmd_send(cli: AgentCli, args: argparse.Namespace) -> int:
    depth = int(os.environ.get("AGENT_DELEGATE_DEPTH", "0"))
    if depth >= 1:
        raise SystemExit("Recursive delegation blocked: AGENT_DELEGATE_DEPTH >= 1. Execute the task directly.")

    route = cli.select_route(args.target, args.route)
    timeout_sec = resolve_timeout(args.mode, args.timeout_sec)
    task_text = read_prompt_source(args.text, args.prompt_file)
    inputs = collect_inputs(args.input)
    title = args.title or task_text.splitlines()[0][:60]
    normalized_cwd = cli.normalize_cwd(args.target, args.cwd)
    target_cfg = cli.agent_cfg(args.target)

    job_dir = cli.create_local_job(
        target=args.target,
        route=route,
        title=title,
        mode=args.mode,
        cwd=normalized_cwd,
        timeout_sec=timeout_sec,
        task_text=task_text,
        inputs=inputs,
    )
    cli.append_dispatch_log(
        job_dir,
        "Dispatch",
        [
            f"origin: {cli.local_agent}",
            f"target: {args.target}",
            f"route: {route}",
            f"requested_cwd: {args.cwd}",
            f"resolved_cwd: {normalized_cwd}",
        ],
    )
    plan = cli.build_route_plan(args.target, route, job_dir.name)
    # Skip remote_job_exists for shared-filesystem (local WSL) — the local job dir IS the remote dir
    if plan.upload_host is not None and cli.remote_job_exists(args.target, route, job_dir.name):
        raise SystemExit(f"Remote job already exists: {job_dir.name}")
    try:
        cli.preflight_target(args.target, route, normalized_cwd)
        if target_cfg["platform"] == "linux":
            cli.append_dispatch_log(job_dir, "Preflight", ["remote Linux checks passed"])
    except SystemExit as exc:
        cli.append_dispatch_log(job_dir, "Preflight", [f"failed: {exc}"])
        raise

    if target_cfg["platform"] == "linux" and args.mode == "read" and args.wait:
        cli.append_dispatch_log(job_dir, "Execution", ["mode: direct-read-stdout"])
        prompt_text = cli.build_read_stdout_prompt(task_text=task_text, cwd=normalized_cwd, timeout_sec=timeout_sec)
        attempts: list[tuple[subprocess.CompletedProcess[str], str, str]] = []
        result: subprocess.CompletedProcess[str] | None = None
        cleaned_stdout = ""
        cleaned_stderr = ""
        for attempt in range(1, READ_RETRY_ATTEMPTS + 1):
            result = cli.run_read_job(
                target=args.target,
                route=route,
                cwd=normalized_cwd,
                prompt_text=prompt_text,
                timeout_sec=timeout_sec,
            )
            cleaned_stdout = strip_terminal_noise(result.stdout)
            cleaned_stderr = strip_terminal_noise(result.stderr)
            attempts.append((result, cleaned_stdout, cleaned_stderr))
            if result.returncode == 0 and cleaned_stdout:
                break
            if attempt == READ_RETRY_ATTEMPTS or not is_retryable_claude_error(cleaned_stderr):
                break
            cli.append_dispatch_log(
                job_dir,
                "Execution",
                [f"retrying_after_attempt: {attempt}", "reason: transient Claude API error"],
            )
            time.sleep(attempt * 2)
        if result is None:
            raise RuntimeError("No read attempt was made; READ_RETRY_ATTEMPTS must be >= 1")
        log_lines = [
            "# Execution Log",
            "",
            "## Route",
            route,
            "",
            "## Exit Code",
            str(result.returncode),
        ]
        log_lines.extend(["", "## Attempts", str(len(attempts))])
        if cleaned_stderr:
            log_lines.extend(["", "## Stderr", cleaned_stderr])
        write_text(job_dir / "log.md", "\n".join(log_lines) + "\n")
        if result.returncode == 0 and cleaned_stdout:
            write_text(job_dir / "reply.md", f"[OK]\n\n{cleaned_stdout}\n")
            print(job_dir.name)
            print(read_text(job_dir / "reply.md"))
            return 0

        failure_lines = [
            "[FAILED]",
            "",
            "# Summary",
            "Remote read task did not return a usable stdout response.",
            "",
            "## Findings or Actions",
        ]
        if cleaned_stdout:
            failure_lines.append(f"- partial stdout: {cleaned_stdout[:400]}")
        else:
            failure_lines.append("- stdout was empty")
        if cleaned_stderr:
            failure_lines.append(f"- stderr: {cleaned_stderr[:400]}")
        failure_lines.extend(
            [
                "",
                "## Next Step",
                "Retry after checking the remote Claude CLI environment.",
                "",
            ]
        )
        write_text(job_dir / "reply.md", "\n".join(failure_lines))
        print(job_dir.name)
        print(read_text(job_dir / "reply.md"))
        return 1

    cli.upload_job(job_dir, plan)
    cli.append_dispatch_log(job_dir, "Upload", [f"uploaded_to: {plan.upload_host or 'local'}:{plan.upload_job_dir}"])
    print(job_dir.name)
    try:
        cli.invoke_runner(plan, wait=args.wait, timeout_sec=timeout_sec)
        cli.append_dispatch_log(
            job_dir,
            "Runner",
            [f"started_on: {plan.runner_host or 'local'}", f"mode: {'wait' if args.wait else 'background'}"],
        )
        if not args.wait:
            return 0

        cli.fetch_job_artifacts(plan, job_dir)
        code = reply_exit_code(job_dir / "reply.md")
        if code == 124:
            cli.append_dispatch_log(
                job_dir,
                "Wait",
                [f"timed_out_after: {timeout_sec + 60}s", "reply.md was not observed locally or remotely"],
            )
            print(f"Timed out waiting for reply.md. job_id={job_dir.name}", file=sys.stderr)
            return 124

        if (job_dir / "reply.md").exists():
            print(read_text(job_dir / "reply.md"))
        return code
    except subprocess.TimeoutExpired as exc:
        d_state_count = 0
        if target_cfg["platform"] == "linux":
            try:
                d_state_count = cli.remote_d_state_count(args.target, route)
            except (OSError, subprocess.TimeoutExpired):
                d_state_count = 0
        cli.append_dispatch_log(
            job_dir,
            "Runner",
            [
                f"ssh_timeout_sec: {exc.timeout}",
                f"host: {plan.runner_host or 'local'}",
                f"command: {plan.runner_command_wait if args.wait else plan.runner_command_background}",
                f"d_state_count: {d_state_count}",
            ],
        )
        if target_cfg["platform"] == "linux" and d_state_count >= WSL_DSTATE_THRESHOLD:
            raise SystemExit(
                f"Runner launch timed out for job {job_dir.name}. "
                f"Detected {d_state_count} D-state processes on WSL; ask the host machine to run 'wsl --shutdown'."
            ) from exc
        raise SystemExit(f"Runner launch timed out for job {job_dir.name}") from exc


def cmd_status(cli: AgentCli, args: argparse.Namespace) -> int:
    job_dir = cli.local_job_root() / args.job_id
    if not job_dir.exists():
        raise SystemExit(f"Local job not found: {job_dir}")
    meta = json.loads(read_text(job_dir / "meta.json"))
    if not (job_dir / "reply.md").exists():
        plan = cli.build_route_plan(meta["target"], meta["route"], meta["id"])
        if cli.reply_exists_remote(plan):
            cli.fetch_job_artifacts(plan, job_dir)
    print(format_status(job_dir, args.detail))
    return 0


def cmd_cleanup(cli: AgentCli, args: argparse.Namespace) -> int:
    archive_root = cli.local_archive_root()
    archive_root.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now() - timedelta(days=args.days)
    moved = 0
    for job_dir in cli.local_job_root().iterdir():
        if not job_dir.is_dir():
            continue
        reply_path = job_dir / "reply.md"
        if not reply_path.exists():
            continue
        if datetime.fromtimestamp(reply_path.stat().st_mtime) >= cutoff:
            continue
        shutil.move(str(job_dir), str(archive_root / job_dir.name))
        moved += 1
    print(f"Archived {moved} job(s) to {archive_root}")
    return 0


def build_parser(valid_targets: list[str], valid_relays: list[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-node AI delegation CLI (bidirectional)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send = subparsers.add_parser("send", help="Create and send a job")
    send.add_argument("target", choices=valid_targets)
    send.add_argument("--cwd", required=True)
    prompt_group = send.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--text")
    prompt_group.add_argument("--prompt-file")
    send.add_argument("--mode", choices=["read", "write"], default="read")
    send.add_argument("--title")
    send.add_argument("--input", action="append")
    route_choices = ["auto", "direct"] + [f"via-{r}" for r in valid_relays]
    send.add_argument("--route", choices=route_choices, default="auto")
    send.add_argument("--timeout-sec", type=int)
    send.add_argument("--wait", action="store_true")

    status = subparsers.add_parser("status", help="Show local job status")
    status.add_argument("job_id")
    status.add_argument("--detail", action="store_true")

    cleanup = subparsers.add_parser("cleanup", help="Archive old completed jobs")
    cleanup.add_argument("--days", type=int, default=7)

    return parser


def main() -> int:
    config = load_config()
    local_agent = detect_local_agent(config["agents"])
    cli = AgentCli(config, local_agent)
    valid_targets = cli.valid_targets()
    # Directly reachable agents (no relay_via) can be used as relay hops for --route via-X
    reachable_agents = [name for name in valid_targets if cli.agent_cfg(name).get("relay_via") is None]
    args = build_parser(valid_targets, reachable_agents).parse_args()
    if args.command == "send":
        return cmd_send(cli, args)
    if args.command == "status":
        return cmd_status(cli, args)
    if args.command == "cleanup":
        return cmd_cleanup(cli, args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
