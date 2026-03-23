"""
Renderer — displays IDL structure in the terminal using Rich tables.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from src.models import AnchorIDL

console = Console()


def render_idl_overview(idl: AnchorIDL):
    """Print a complete IDL overview to the terminal."""
    console.print()
    console.rule(f"[bold]🔍 IDL Explorer — [cyan]{idl.display_name}[/cyan][/bold]")

    # Header info
    info = (
        f"[bold]Program:[/bold] {idl.name}  |  "
        f"[bold]Version:[/bold] {idl.version}  |  "
        f"[bold]Address:[/bold] [dim]{idl.address or 'N/A'}[/dim]"
    )
    console.print(f"\n  {info}\n")

    # Stats
    stats_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    stats_table.add_row("[bold]Instructions[/bold]", f"[cyan]{len(idl.instructions)}[/cyan]")
    stats_table.add_row("[bold]Account Types[/bold]", f"[green]{len(idl.accounts)}[/green]")
    stats_table.add_row("[bold]Events[/bold]", f"[yellow]{len(idl.events)}[/yellow]")
    stats_table.add_row("[bold]Errors[/bold]", f"[red]{len(idl.errors)}[/red]")
    stats_table.add_row("[bold]Custom Types[/bold]", f"[dim]{len(idl.types)}[/dim]")
    console.print(stats_table)

    # Instructions
    if idl.instructions:
        _render_instructions(idl)

    # Account types
    if idl.accounts:
        _render_account_types(idl)

    # Events
    if idl.events:
        _render_events(idl)

    # Errors
    if idl.errors:
        _render_errors(idl)

    console.print()


def _render_instructions(idl: AnchorIDL):
    console.print(f"\n[bold]📋 Instructions ({len(idl.instructions)})[/bold]\n")

    for ix in idl.instructions:
        # Instruction header
        doc = " — " + ix.docs[0] if ix.docs else ""
        console.print(f"  [bold cyan]{ix.camel_name}[/bold cyan][dim]{doc}[/dim]")

        # Args
        if ix.args:
            args_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
            args_table.add_column("Arg", style="bold", width=24)
            args_table.add_column("Type", width=28)
            args_table.add_column("TS Type", width=24)
            for arg in ix.args:
                args_table.add_row(arg.name, f"[dim]{arg.type_str}[/dim]", f"[cyan]{arg.ts_type}[/cyan]")
            console.print("  [dim]Arguments:[/dim]")
            console.print(args_table)

        # Accounts
        if ix.accounts:
            acc_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
            acc_table.add_column("Account", style="bold", width=24)
            acc_table.add_column("Mut", width=5, justify="center")
            acc_table.add_column("Signer", width=7, justify="center")
            acc_table.add_column("Optional", width=9, justify="center")
            for acc in ix.accounts:
                acc_table.add_row(
                    acc.name,
                    "[green]✓[/green]" if acc.is_mut else "[dim]·[/dim]",
                    "[yellow]✓[/yellow]" if acc.is_signer else "[dim]·[/dim]",
                    "[blue]?[/blue]" if acc.is_optional else "[dim]·[/dim]",
                )
            console.print("  [dim]Accounts:[/dim]")
            console.print(acc_table)

        if ix.returns:
            console.print(f"  [dim]Returns:[/dim] [cyan]{ix.returns}[/cyan]")

        console.print()


def _render_account_types(idl: AnchorIDL):
    console.print(f"\n[bold]🗂️  Account Types ({len(idl.accounts)})[/bold]\n")

    for acc_type in idl.accounts:
        console.print(f"  [bold green]{acc_type.pascal_name}[/bold green]")
        if acc_type.fields:
            t = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
            t.add_column("Field", style="bold", width=28)
            t.add_column("IDL Type", width=24)
            t.add_column("TypeScript", width=20)
            t.add_column("Python", width=20)
            for f in acc_type.fields:
                t.add_row(f.name, f"[dim]{f.type_str}[/dim]", f"[cyan]{f.ts_type}[/cyan]", f"[yellow]{f.py_type}[/yellow]")
            console.print(t)
        console.print()


def _render_events(idl: AnchorIDL):
    console.print(f"\n[bold]⚡ Events ({len(idl.events)})[/bold]\n")

    for ev in idl.events:
        console.print(f"  [bold yellow]{ev.name}[/bold yellow]")
        if ev.fields:
            t = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
            t.add_column("Field", style="bold", width=28)
            t.add_column("IDL Type", width=24)
            for f in ev.fields:
                t.add_row(f.name, f"[dim]{f.type_str}[/dim]")
            console.print(t)
        console.print()


def _render_errors(idl: AnchorIDL):
    console.print(f"\n[bold]❌ Error Codes ({len(idl.errors)})[/bold]\n")

    t = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    t.add_column("Code", style="bold", width=8)
    t.add_column("Hex", width=8)
    t.add_column("Name", width=32)
    t.add_column("Message", width=48)

    for err in idl.errors:
        t.add_row(
            str(err.code),
            f"0x{err.code:04x}",
            f"[red]{err.name}[/red]",
            f"[dim]{err.msg}[/dim]",
        )
    console.print(t)
