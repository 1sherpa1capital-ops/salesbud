"""
Minimalist logger for SalesBud CLI.
Clean, simple output with minimal visual noise.
"""

from typing import Any, Optional
from rich.console import Console

console = Console()

# Global quiet mode
_QUIET_MODE = False


def set_quiet_mode(quiet: bool):
    """Enable or disable quiet mode."""
    global _QUIET_MODE
    _QUIET_MODE = quiet


def is_quiet() -> bool:
    return _QUIET_MODE


def print_text(text: Any = "", *args, **kwargs):
    """Print text (suppressed in quiet mode)."""
    if not _QUIET_MODE:
        console.print(text, *args, **kwargs)


def info(text: str):
    """Info message."""
    if not _QUIET_MODE:
        console.print(f"[dim]› {text}[/dim]")


def success(text: str):
    """Success message."""
    if not _QUIET_MODE:
        console.print(f"[green]✓ {text}[/green]")


def warning(text: str):
    """Warning message."""
    if not _QUIET_MODE:
        console.print(f"[yellow]! {text}[/yellow]")


def error(text: str):
    """Error message."""
    if not _QUIET_MODE:
        console.print(f"[red]✗ {text}[/red]")


def step(text: str):
    """Workflow step."""
    if not _QUIET_MODE:
        console.print(f"\n[bold]{text}[/bold]")


def header(text: str):
    """Section header."""
    if not _QUIET_MODE:
        console.print(f"\n[bold]{text}[/bold]\n")
