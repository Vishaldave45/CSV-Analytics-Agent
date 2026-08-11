"""Prompt loader and composer service for CSV Analytics Agent.

Provides thread-safe loading and composition of repository root `prompts/*.md` templates.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# Version identifiers
ROUTER_PROMPT_VERSION = "v1"
PLANNER_PROMPT_VERSION = "v1"
PYTHON_PROMPT_VERSION = "v1"
RESPONSE_PROMPT_VERSION = "v1"


def get_prompts_dir() -> Path:
    """Return absolute Path to repository root `prompts/` directory."""
    # loader.py lives in src/csv_analytics_agent/prompts/loader.py -> 3 levels up to repo root
    repo_root = Path(__file__).resolve().parents[3]
    prompts_dir = repo_root / "prompts"
    if not prompts_dir.exists() or not prompts_dir.is_dir():
        # Fallback search if installed as package
        cwd_prompts = Path.cwd() / "prompts"
        if cwd_prompts.exists() and cwd_prompts.is_dir():
            return cwd_prompts
        raise FileNotFoundError(f"Prompts directory not found at expected path: '{prompts_dir}'")
    return prompts_dir


@lru_cache(maxsize=32)
def load_prompt(relative_path: str) -> str:
    """Load content of a static prompt markdown file.

    Args:
        relative_path: Path relative to repository `prompts/` dir (e.g. 'router/system.md').

    Returns:
        String content of the prompt file stripped of surrounding whitespace.

    Raises:
        FileNotFoundError: If prompt file does not exist.
    """
    prompts_dir = get_prompts_dir()
    file_path = (prompts_dir / relative_path).resolve()

    # Security check: ensure path stays within prompts_dir
    try:
        file_path.relative_to(prompts_dir)
    except ValueError as exc:
        raise FileNotFoundError(
            f"Access denied: Path '{relative_path}' escapes prompts directory."
        ) from exc

    if not file_path.is_file():
        raise FileNotFoundError(f"Prompt asset file not found: '{file_path}'")

    return file_path.read_text(encoding="utf-8").strip()


def compose_prompt(*relative_paths: str) -> str:
    """Compose multiple prompt markdown templates into a unified prompt string.

    Args:
        relative_paths: Positional path strings relative to `prompts/` directory.

    Returns:
        Joined prompt content string.
    """
    parts: list[str] = [load_prompt(rel_path) for rel_path in relative_paths]
    return "\n\n---\n\n".join(parts)


def get_router_prompt() -> str:
    """Return composed system prompt for the intent router layer."""
    return compose_prompt("shared/grounding.md", "router/system.md")


def get_planner_prompt() -> str:
    """Return composed system prompt for the analytical planner layer."""
    return compose_prompt(
        "shared/grounding.md",
        "shared/data_quality.md",
        "shared/security.md",
        "followup/system.md",
        "planner/system.md",
    )


def get_python_prompt() -> str:
    """Return composed system prompt for the Python code generator layer."""
    return compose_prompt(
        "shared/grounding.md",
        "shared/security.md",
        "shared/data_quality.md",
        "python/system.md",
        "python/security.md",
    )


def get_response_prompt() -> str:
    """Return composed system prompt for the response generator layer."""
    return compose_prompt(
        "shared/grounding.md",
        "response/evidence.md",
        "response/system.md",
    )


def clear_prompt_cache() -> None:
    """Clear lru_cache for load_prompt (useful during testing)."""
    load_prompt.cache_clear()


__all__ = [
    "PLANNER_PROMPT_VERSION",
    "PYTHON_PROMPT_VERSION",
    "RESPONSE_PROMPT_VERSION",
    "ROUTER_PROMPT_VERSION",
    "clear_prompt_cache",
    "compose_prompt",
    "get_planner_prompt",
    "get_prompts_dir",
    "get_python_prompt",
    "get_response_prompt",
    "get_router_prompt",
    "load_prompt",
]
