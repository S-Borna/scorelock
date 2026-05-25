"""ScoreLock LLM-motor via Claude Code CLI (`claude -p`) mot Max-subben.

Platt kostnad istället för metered Anthropic-API — driver all ScoreLock-AI
(analys, content, sentiment) utan per-token-kostnad som skenar vid skala.

VIKTIGT: körs DÄR claude-auth (Max-sub) finns — host / dedikerad worker-box —
inte i Docker-backend (där finns varken `claude` eller auth).

Verifierat invokerings-recept (2026-05-25): miljö UTAN ANTHROPIC_API_KEY (annars
kan en ogiltig nyckel överrida Max-OAuth → 401) + prompt via STDIN (inte ett
gigantiskt positional-arg som shell kan mangla) + --model + --system-prompt.
"""
from __future__ import annotations

import json
import os
import subprocess


class ClaudeCLIError(Exception):
    """claude -p misslyckades (auth, timeout, exit, tom output)."""


def generate(
    system_prompt: str,
    user_prompt: str,
    model: str = "sonnet",
    timeout: int = 120,
) -> str:
    """Kör claude -p mot Max-subben och returnera råtexten."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        proc = subprocess.run(
            ["claude", "-p", "--model", model, "--system-prompt", system_prompt],
            input=user_prompt,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCLIError(f"claude -p timeout efter {timeout}s") from exc
    except FileNotFoundError as exc:
        # claude-binären finns inte (Docker/prod) — signalera så orkestratorn
        # kan falla tillbaka på Anthropic-API i stället för att krascha.
        raise ClaudeCLIError("claude-binär saknas (ej host/box-miljö)") from exc
    if proc.returncode != 0:
        raise ClaudeCLIError(
            f"claude -p exit {proc.returncode}: {proc.stderr.strip()[:200]}"
        )
    out = (proc.stdout or "").strip()
    if not out or "Failed to authenticate" in out:
        raise ClaudeCLIError(f"claude -p auth/tom output: {out[:200]}")
    return out


def generate_json(
    system_prompt: str,
    user_prompt: str,
    model: str = "sonnet",
    timeout: int = 120,
) -> dict:
    """Som generate(), men parsar ut {summary, body}-JSON (strippar fence)."""
    raw = generate(system_prompt, user_prompt, model, timeout)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
        if cleaned[:4].lower() == "json":
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    return json.loads(cleaned)
