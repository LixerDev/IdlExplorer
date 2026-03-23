#!/usr/bin/env python3
"""
IdlExplorer — Solana IDL → SDK + Docs Generator
Built by LixerDev
"""

import asyncio
import json
import http.server
import os
import threading
import webbrowser
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from config import config
from src.logger import get_logger, print_banner
from src.models import IdlParser, AnchorIDL
from src.fetcher import IdlFetcher
from src.renderer import render_idl_overview
from src.generators.typescript import TypeScriptGenerator
from src.generators.python_sdk import PythonGenerator
from src.generators.docs import DocsGenerator

app = typer.Typer(
    help="IdlExplorer — Generate TypeScript SDK, Python client, and HTML docs from any Anchor IDL",
    no_args_is_help=True
)
console = Console()
logger = get_logger(__name__)

OUTPUTS = ["ts", "python", "docs", "all"]


@app.command()
def generate(
    idl_path: str = typer.Argument(..., help="Path to IDL JSON file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
    only: str = typer.Option("all", "--only", help="What to generate: ts, python, docs, all"),
    open_docs: bool = typer.Option(False, "--open", help="Open docs in browser after generating"),
):
    """
    Generate TypeScript SDK, Python client, and HTML docs from a local IDL file.

    Example:
      idl-explorer generate ./target/idl/my_program.json
      idl-explorer generate ./idl.json --only ts --output ./sdk
    """
    print_banner()

    if not Path(idl_path).exists():
        console.print(f"[red]File not found: {idl_path}[/red]")
        raise typer.Exit(1)

    parser = IdlParser()
    idl = parser.parse_file(idl_path)

    console.print(f"\n[bold]📄 IDL loaded: [cyan]{idl.display_name}[/cyan] v{idl.version}[/bold]")
    console.print(f"  {len(idl.instructions)} instructions  |  {len(idl.accounts)} account types  |  {len(idl.errors)} errors\n")

    out_dir = output or str(Path(config.OUTPUT_DIR) / idl.name)
    _run_generators(idl, out_dir, only)

    if open_docs or only in ("docs", "all"):
        docs_path = Path(out_dir) / "docs" / "index.html"
        if docs_path.exists():
            console.print(f"\n[dim]Docs: file://{docs_path.resolve()}[/dim]")
            if open_docs:
                webbrowser.open(f"file://{docs_path.resolve()}")


@app.command("from-address")
def from_address(
    program_id: str = typer.Argument(..., help="Deployed Anchor program public key"),
    cluster: str = typer.Option("mainnet-beta", "--cluster", "-c", help="Cluster: mainnet-beta, devnet, testnet, localnet"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
    only: str = typer.Option("all", "--only", help="What to generate: ts, python, docs, all"),
    save_only: bool = typer.Option(False, "--save-only", help="Just save the IDL JSON, don't generate SDK"),
    open_docs: bool = typer.Option(False, "--open", help="Open docs in browser after generating"),
):
    """
    Fetch an IDL from a deployed Anchor program and generate the SDK.

    Example:
      idl-explorer from-address TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
      idl-explorer from-address <PROGRAM_ID> --cluster devnet
    """
    print_banner()

    async def _run():
        fetcher = IdlFetcher(cluster)
        console.print(f"\n[dim]Fetching IDL from {cluster} for {program_id[:12]}...[/dim]")
        try:
            idl_json = await fetcher.fetch_idl(program_id)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

        parser = IdlParser()
        idl = parser.parse(idl_json)
        console.print(f"[green]✅ IDL fetched:[/green] {idl.display_name} v{idl.version}")

        out_dir = output or str(Path(config.OUTPUT_DIR) / idl.name)

        if save_only:
            idl_path = Path(out_dir) / f"{idl.name}.json"
            idl_path.parent.mkdir(parents=True, exist_ok=True)
            with open(idl_path, "w") as f:
                json.dump(idl_json, f, indent=2)
            console.print(f"[dim]IDL saved to: {idl_path}[/dim]")
            return

        _run_generators(idl, out_dir, only)

        if open_docs:
            docs_path = Path(out_dir) / "docs" / "index.html"
            if docs_path.exists():
                webbrowser.open(f"file://{docs_path.resolve()}")

    asyncio.run(_run())


@app.command()
def inspect(
    idl_path: str = typer.Argument(..., help="Path to IDL JSON file"),
    section: Optional[str] = typer.Option(None, "--section", "-s", help="Show only: instructions, accounts, events, errors, types"),
):
    """
    Display IDL structure in the terminal — instructions, accounts, events, errors.

    Example:
      idl-explorer inspect ./idl.json
      idl-explorer inspect ./idl.json --section instructions
    """
    print_banner()

    if not Path(idl_path).exists():
        console.print(f"[red]File not found: {idl_path}[/red]")
        raise typer.Exit(1)

    parser = IdlParser()
    idl = parser.parse_file(idl_path)
    render_idl_overview(idl)


@app.command()
def serve(
    idl_path: str = typer.Argument(..., help="Path to IDL JSON file"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to serve on (default: 8080)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """
    Generate HTML docs and serve them on localhost. Opens automatically in browser.

    Example:
      idl-explorer serve ./idl.json
      idl-explorer serve ./idl.json --port 3000
    """
    print_banner()

    if not Path(idl_path).exists():
        console.print(f"[red]File not found: {idl_path}[/red]")
        raise typer.Exit(1)

    parser = IdlParser()
    idl = parser.parse_file(idl_path)

    out_dir = output or str(Path(config.OUTPUT_DIR) / idl.name)
    docs_gen = DocsGenerator()
    docs_gen.generate(idl, out_dir)

    docs_dir = Path(out_dir) / "docs"
    port_num = port or config.DOCS_PORT

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(docs_dir), **kwargs)
        def log_message(self, format, *args):
            pass  # suppress logs

    server = http.server.HTTPServer(("0.0.0.0", port_num), Handler)
    url = f"http://localhost:{port_num}"

    console.print(f"\n[bold green]✅ Serving docs at {url}[/bold green]")
    console.print(f"[dim]Program: {idl.display_name} v{idl.version}[/dim]")
    console.print(f"[dim]Docs dir: {docs_dir}[/dim]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[dim]Server stopped.[/dim]")


@app.command()
def validate(
    idl_path: str = typer.Argument(..., help="Path to IDL JSON file"),
):
    """Validate an IDL file and report any parsing issues."""
    print_banner()

    if not Path(idl_path).exists():
        console.print(f"[red]File not found: {idl_path}[/red]")
        raise typer.Exit(1)

    try:
        parser = IdlParser()
        idl = parser.parse_file(idl_path)
        console.print(f"\n[bold green]✅ IDL is valid![/bold green]")
        console.print(f"  Program:      {idl.name}")
        console.print(f"  Version:      {idl.version}")
        console.print(f"  Instructions: {len(idl.instructions)}")
        console.print(f"  Accounts:     {len(idl.accounts)}")
        console.print(f"  Events:       {len(idl.events)}")
        console.print(f"  Errors:       {len(idl.errors)}")
        console.print(f"  Custom Types: {len(idl.types)}\n")
    except Exception as e:
        console.print(f"[red]❌ IDL validation failed: {e}[/red]")
        raise typer.Exit(1)


def _run_generators(idl: AnchorIDL, out_dir: str, only: str):
    """Run the requested generators."""
    generated = []

    if only in ("ts", "all"):
        ts_gen = TypeScriptGenerator()
        ts_gen.generate(idl, out_dir)
        generated.append(("TypeScript SDK", f"{out_dir}/sdk/index.ts"))

    if only in ("python", "all"):
        py_gen = PythonGenerator()
        py_gen.generate(idl, out_dir)
        generated.append(("Python Client", f"{out_dir}/client/client.py"))

    if only in ("docs", "all"):
        docs_gen = DocsGenerator()
        docs_gen.generate(idl, out_dir)
        generated.append(("HTML Docs", f"{out_dir}/docs/index.html"))

    console.print(f"\n[bold green]✅ Generation complete![/bold green]\n")
    for name, path in generated:
        console.print(f"  [bold]{name}:[/bold] {path}")
    console.print(f"\n  [dim]Output directory: {out_dir}[/dim]\n")


if __name__ == "__main__":
    app()
