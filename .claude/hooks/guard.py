#!/usr/bin/env python3
"""PreToolUse guard for Claude Code.

Keeps every tool call inside the project directory, protects secrets and the read-only
reference folder, and blocks destructive commands. Exit code 2 blocks the call and shows
the message to Claude.
"""
import json
import os
import re
import sys
from pathlib import Path

PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]).resolve()
# Claude Code's own working areas for this project (temp files and saved notes). Nothing else outside is allowed.
ALLOWED_OUTSIDE = (
    Path("/tmp/claude-1000") / "-home-nash-hackaton-minilik",
    Path.home() / ".claude/projects/-home-nash-hackaton-minilik",
    Path("/dev"),
)
SECRET_SUFFIXES = (".key", ".pem", ".p12", ".jks")
PATH_TOKEN = re.compile(r"""(?<![\w.\-])(?:~|\$HOME|\$\{HOME\}|/|\.\.?/)[^\s'"`;|&()<>,]*""")

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
inp = data.get("tool_input", {}) or {}
cwd = Path(data.get("cwd") or PROJECT)


def block(msg: str) -> None:
    print(f"BLOCKED by guard.py: {msg}", file=sys.stderr)
    sys.exit(2)


def resolve(raw: str) -> Path:
    raw = re.sub(r"^(\$HOME|\$\{HOME\})", str(Path.home()), raw)
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else cwd / path).resolve()


def inside_project(path: Path) -> bool:
    return any(path == base or base in path.parents for base in (PROJECT, *ALLOWED_OUTSIDE))


def is_secret(path: Path) -> bool:
    name = path.name
    if name == ".env.example":
        return False
    return name == ".env" or name.startswith(".env.") or name.endswith(SECRET_SUFFIXES)


def check_file_tool() -> None:
    raw = inp.get("file_path") or inp.get("notebook_path") or inp.get("path")
    if not raw:
        return
    path = resolve(raw)
    if not inside_project(path):
        block(f"{path} is outside the project. Work only inside {PROJECT}.")
    if is_secret(path):
        block("secret files (.env, keys) are off limits. Code loads them with python-dotenv.")
    top_level = path.relative_to(PROJECT).parts[:1] if PROJECT in path.parents else ()
    if tool in ("Edit", "Write", "NotebookEdit") and top_level and top_level[0].strip() == "prev_projects":
        block("prev_projects is read-only reference. Write new code in back-end/ or front-end/.")


def _path_candidates(cmd: str) -> str:
    """The command with URLs removed and quoted text kept only when the whole quote is a path."""

    def keep_if_path(match: re.Match) -> str:
        text = match.group(1) or match.group(2) or ""
        return f" {text} " if text.startswith(("/", "~", "./", "../", "$HOME", "${HOME}")) else " "

    return re.sub(r"'([^']*)'|\"([^\"]*)\"", keep_if_path, re.sub(r"\b\w+://\S+", " ", cmd))


def check_bash() -> None:
    cmd = inp.get("command", "")
    if not inside_project(cwd.resolve()):
        block(f"the shell is outside the project. Run `cd {PROJECT}` first.")
    if re.search(r"(^|[;&|]\s*)cd\s*($|[;&|]|-\s*($|[;&|]))", cmd):
        block("bare `cd` or `cd -` leaves the project.")
    for match in PATH_TOKEN.finditer(_path_candidates(cmd)):
        target = resolve(match.group(0))
        if not inside_project(target):
            block(f"{match.group(0)} points outside the project. Work only inside {PROJECT}.")
    if re.search(r"\b(sudo|su)\b", cmd):
        block("no privileged commands.")
    if re.search(r"\brm\s+-\w*(r\w*f|f\w*r)", cmd):
        block("rm -rf is not allowed. Remove specific files, or ask the user.")
    if re.search(r"git\s+push\b.*(--force|\s-f\b)", cmd):
        block("force push is not allowed.")
    if re.search(r"(^|[\s/'\"=<(])\.env(\.save)?($|[\s'\";|&)])", cmd):
        block("do not read or print .env in the shell. Scripts load it with python-dotenv.")
    if re.search(r"\.(key|pem)\b", cmd) and re.search(r"\b(cat|less|head|tail|cp|base64|xxd)\b", cmd):
        block("private key files are off limits.")
    if "prev_projects" in cmd and re.search(r"\b(rm|mv|tee|touch|chmod)\b|sed\s+-i|>", cmd):
        block("prev_projects is read-only reference.")


if tool == "Bash":
    check_bash()
elif tool in ("Read", "Edit", "Write", "NotebookEdit", "Glob", "Grep"):
    check_file_tool()
sys.exit(0)
