from __future__ import annotations

from rich.console import Console


console = Console()


def info(msg: str) -> None:
    console.print(f"[bold cyan]info[/bold cyan] {msg}")


def warn(msg: str) -> None:
    console.print(f"[bold yellow]warn[/bold yellow] {msg}")


def error(msg: str) -> None:
    console.print(f"[bold red]error[/bold red] {msg}")
