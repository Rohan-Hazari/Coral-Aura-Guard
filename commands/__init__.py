"""
commands package — Aura Guard

This package previously contained a brittle subprocess.Popen CLI wrapper.
It has been completely purged in favor of Native MCP via Pydantic AI.
"""

from __future__ import annotations

# All legacy CLI logic has been removed.
# For data retrieval, use the Native MCP Agent in commands/agent.py.
