"""
Centralized logger for SalesBud CLI.
Uses `rich` for TUI rendering, but strictly enforces JSON-safe output
by routing all prints/logs to /dev/null when QUIET_MODE is enabled.
"""
from typing import Any, Optional
from rich.console import Console

# Use a standard console for human output
console = Console()

# We control this globally from main.py via set_quiet_mode
_QUIET_MODE = False

def set_quiet_mode(quiet: bool):
    """Enable or disable quiet mode (suppresses all output except explicit JSON)."""
    global _QUIET_MODE
    _QUIET_MODE = quiet

def is_quiet() -> bool:
    return _QUIET_MODE

def print_text(text: Any, *args, **kwargs):
    """Print standard text via rich console. Suppressed in quiet mode."""
    if not _QUIET_MODE:
        console.print(text, *args, **kwargs)

def info(text: str):
    """Print an informational message."""
    if not _QUIET_MODE:
        console.print(f"[cyan]ℹ {text}[/cyan]")

def success(text: str):
    """Print a success message."""
    if not _QUIET_MODE:
        console.print(f"[green]✓ {text}[/green]")

def warning(text: str):
    """Print a warning message."""
    if not _QUIET_MODE:
        console.print(f"[yellow]⚠ {text}[/yellow]")

def error(text: str):
    """Print an error message."""
    if not _QUIET_MODE:
        console.print(f"[red]✗ {text}[/red]")

def step(text: str):
    """Print a bold workflow step header."""
    if not _QUIET_MODE:
        console.print(f"\n[bold blue]--- {text} ---[/bold blue]")

def rule(title: Optional[str] = None):
    """Print a horizontal rule."""
    if not _QUIET_MODE:
        if title:
            console.rule(f"[bold]{title}[/bold]")
        else:
            console.rule()

def header(text: str):
    """Print a large header."""
    if not _QUIET_MODE:
        console.print(f"\n[bold magenta]=== {text} ===[/bold magenta]\n")
