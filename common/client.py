"""Shared Anthropic client setup for task scripts."""

from anthropic import Anthropic
from dotenv import load_dotenv

from .bootstrap import find_repo_root

DEFAULT_MODEL = "claude-opus-4-8"


def get_client() -> Anthropic:
    """Load the repo-root .env and return an Anthropic client."""
    root = find_repo_root(__file__)
    load_dotenv(root / ".env")
    return Anthropic()
