"""
HTML Docs Generator — generates a complete interactive documentation page from an IDL.

Output:
  docs/index.html — Single-page HTML with all instructions, types, errors, events.
                    No external dependencies — uses only CDN resources.
"""

from pathlib import Path
from src.models import AnchorIDL
from src.logger import get_logger

logger = get_logger(__name__)


class DocsGenerator:
    def generate(self, idl: AnchorIDL, output_dir: str) -> dict[str, str]:
        docs_dir = Path(output_dir) / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        html = self._generate_html(idl)
        files = {"docs/index.html": html}

        for rel_path, content in files.items():
            full_path = Path(output_dir) / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

        logger.info(f"HTML docs → {docs_dir / 'index.html'}")
        return files

    def _generate_html(self, idl: AnchorIDL) -> str:
        instructions_html = self._render_instructions_section(idl)
        accounts_html = self._render_accounts_section(idl)
        events_html = self._render_events_section(idl)
        errors_html = self._render_errors_section(idl)
        types_html = self._render_types_section(idl)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{idl.display_name} — IDL Reference</title>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #1a1d2e;
      --surface2: #232640;
      --border: #2a2f4a;
      --text: #e2e8f0;
      --dim: #8892a4;
      --accent: #9945FF;
      --accent2: #14F195;
      --cyan: #00d4ff;
      --yellow: #f6d860;
      --red: #ff5555;
      --green: #50fa7b;
      --orange: #ffb86c;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
    .sidebar {{ position: fixed; left: 0; top: 0; width: 260px; height: 100vh; background: var(--surface); border-right: 1px solid var(--border); overflow-y: auto; padding: 20px 0; z-index: 100; }}
    .sidebar-logo {{ padding: 12px 20px 20px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }}
    .sidebar-logo h2 {{ font-size: 1.1rem; color: var(--accent); }}
    .sidebar-logo span {{ font-size: 0.75rem; color: var(--dim); }}
    .sidebar-section {{ padding: 4px 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--dim); margin-top: 16px; }}
    .sidebar a {{ display: block; padding: 6px 20px 6px 28px; font-size: 0.85rem; color: var(--dim); text-decoration: none; border-left: 2px solid transparent; transition: all 0.15s; }}
    .sidebar a:hover {{ color: var(--text); border-left-color: var(--accent); background: rgba(153,69,255,0.08); }}
    .main {{ margin-left: 260px; padding: 40px 48px; max-width: 1200px; }}
    .page-header {{ margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
    .page-header h1 {{ font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .meta-chips {{ display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }}
    .chip {{ padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 500; border: 1px solid var(--border); background: var(--surface); color: var(--dim); }}
    .chip.accent {{ border-color: var(--accent); color: var(--accent); }}
    .stat-bar {{ display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }}
    .stat {{ text-align: center; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 24px; }}
    .stat-num {{ font-size: 1.8rem; font-weight: 700; color: var(--accent2); }}
    .stat-label {{ font-size: 0.75rem; color: var(--dim); text-transform: uppercase; }}
    section {{ margin-bottom: 56px; }}
    section h2 {{ font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }}
    .ix-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 16px; overflow: hidden; }}
    .ix-header {{ padding: 16px 20px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; user-select: none; transition: background 0.15s; }}
    .ix-header:hover {{ background: var(--surface2); }}
    .ix-name {{ font-family: 'Courier New', monospace; font-size: 1rem; font-weight: 700; color: var(--cyan); }}
    .ix-doc {{ font-size: 0.83rem; color: var(--dim); margin-left: 12px; }}
    .ix-body {{ padding: 0 20px 20px; border-top: 1px solid var(--border); display: none; }}
    .ix-body.open {{ display: block; }}
    .sub-section-title {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--dim); margin: 16px 0 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    th {{ text-align: left; padding: 8px 12px; background: var(--surface2); color: var(--dim); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    tr:last-child td {{ border-bottom: none; }}
    .type-badge {{ font-family: 'Courier New', monospace; font-size: 0.78rem; background: rgba(0, 212, 255, 0.1); color: var(--cyan); padding: 2px 8px; border-radius: 4px; }}
    .ts-type {{ font-family: 'Courier New', monospace; font-size: 0.78rem; color: var(--yellow); }}
    .py-type {{ font-family: 'Courier New', monospace; font-size: 0.78rem; color: var(--green); }}
    .flag-mut {{ color: var(--orange); font-size: 0.72rem; font-weight: 600; }}
    .flag-signer {{ color: var(--yellow); font-size: 0.72rem; font-weight: 600; }}
    .flag-opt {{ color: var(--cyan); font-size: 0.72rem; font-weight: 600; }}
    .code-block {{ background: #0d1117; border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-top: 12px; overflow-x: auto; }}
    .code-block pre {{ font-family: 'Courier New', monospace; font-size: 0.82rem; color: #c9d1d9; white-space: pre; }}
    .code-tabs {{ display: flex; gap: 2px; margin-top: 12px; }}
    .tab {{ padding: 6px 14px; font-size: 0.78rem; border-radius: 6px 6px 0 0; cursor: pointer; background: var(--surface2); color: var(--dim); border: 1px solid var(--border); border-bottom: none; }}
    .tab.active {{ background: #0d1117; color: var(--text); }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .error-code {{ font-family: 'Courier New', monospace; color: var(--red); font-weight: 600; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; }}
    .badge-green {{ background: rgba(80,250,123,0.15); color: var(--green); }}
    .badge-red {{ background: rgba(255,85,85,0.15); color: var(--red); }}
    .chevron {{ transition: transform 0.2s; color: var(--dim); }}
    .open .chevron {{ transform: rotate(90deg); }}
    footer {{ margin-top: 60px; padding: 20px 0; border-top: 1px solid var(--border); font-size: 0.78rem; color: var(--dim); }}
    @media (max-width: 768px) {{ .sidebar {{ display: none; }} .main {{ margin-left: 0; padding: 20px; }} }}
  </style>
</head>
<body>

<nav class="sidebar">
  <div class="sidebar-logo">
    <h2>🔍 IdlExplorer</h2>
    <span>by LixerDev</span>
  </div>
  <div class="sidebar-section">Program</div>
  <a href="#overview">Overview</a>
  <a href="#instructions">Instructions</a>
  <a href="#accounts">Account Types</a>
  {('<a href="#events">Events</a>' if idl.events else "")}
  <a href="#errors">Error Codes</a>
  {('<a href="#types">Custom Types</a>' if idl.types else "")}
  <div class="sidebar-section">Instructions</div>
  {"".join(f'<a href="#ix-{ix.name}">{ix.camel_name}</a>' for ix in idl.instructions)}
</nav>

<main class="main">
  <div id="overview" class="page-header">
    <h1>{idl.display_name}</h1>
    <div class="meta-chips">
      <span class="chip accent">v{idl.version}</span>
      <span class="chip">{idl.name}</span>
      {f'<span class="chip" style="font-family:monospace;font-size:0.72rem">{idl.address}</span>' if idl.address else ""}
    </div>
    <div class="stat-bar">
      <div class="stat"><div class="stat-num">{len(idl.instructions)}</div><div class="stat-label">Instructions</div></div>
      <div class="stat"><div class="stat-num">{len(idl.accounts)}</div><div class="stat-label">Accounts</div></div>
      <div class="stat"><div class="stat-num">{len(idl.events)}</div><div class="stat-label">Events</div></div>
      <div class="stat"><div class="stat-num">{len(idl.errors)}</div><div class="stat-label">Errors</div></div>
    </div>
  </div>

  {instructions_html}
  {accounts_html}
  {events_html}
  {errors_html}
  {types_html}

  <footer>
    Generated by <strong>IdlExplorer</strong> — Built by LixerDev &nbsp;•&nbsp;
    <a href="https://github.com/LixerDev/IdlExplorer" style="color:var(--accent)">GitHub</a>
  </footer>
</main>

<script>
  document.querySelectorAll('.ix-header').forEach(h => {{
    h.addEventListener('click', () => {{
      const body = h.nextElementSibling;
      body.classList.toggle('open');
      h.classList.toggle('open');
    }});
  }});
  document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
      const group = tab.closest('.tab-group');
      group.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      group.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      const target = group.querySelector('#' + tab.dataset.target);
      if (target) target.classList.add('active');
    }});
  }});
</script>
</body>
</html>'''

    def _render_instructions_section(self, idl: AnchorIDL) -> str:
        cards = ""
        for ix in idl.instructions:
            doc = ix.docs[0] if ix.docs else ""

            # Args table
            args_html = ""
            if ix.args:
                rows = "".join(
                    f"<tr><td><strong>{a.name}</strong></td><td><span class='type-badge'>{a.type_str}</span></td><td class='ts-type'>{a.ts_type}</td><td class='py-type'>{a.py_type}</td></tr>"
                    for a in ix.args
                )
                args_html = f"<div class='sub-section-title'>Arguments</div><table><tr><th>Name</th><th>IDL Type</th><th>TypeScript</th><th>Python</th></tr>{rows}</table>"

            # Accounts table
            accs_html = ""
            if ix.accounts:
                rows = "".join(
                    f"<tr><td><strong>{acc.name}</strong></td><td>{'<span class=\"flag-mut\">MUT</span>' if acc.is_mut else '—'}</td><td>{'<span class=\"flag-signer\">SIGNER</span>' if acc.is_signer else '—'}</td><td>{'<span class=\"flag-opt\">OPT</span>' if acc.is_optional else '—'}</td></tr>"
                    for acc in ix.accounts
                )
                accs_html = f"<div class='sub-section-title'>Accounts</div><table><tr><th>Account</th><th>Mut</th><th>Signer</th><th>Optional</th></tr>{rows}</table>"

            # Code examples
            ts_args = ", ".join(f"args.{a.name}" for a in ix.args)
            ts_accounts = "".join(f"\n        {acc.name}: PublicKey," for acc in ix.accounts)
            ts_example = f"""const txSig = await client.{ix.camel_name}(
  {{{", ".join(f"{a.name}: {self._ts_example_val(a.ts_type)}" for a in ix.args)}}},
  {{{ts_accounts}
  }}
);"""

            py_args = "".join(f"\n        {a.name}={self._py_example_val(a.py_type)}," for a in ix.args)
            py_accounts = "".join(f'\n        "{acc.name}": PublicKey,' for acc in ix.accounts)
            py_example = f"""tx_sig = await client.{ix.name}({py_args}
    accounts={{{py_accounts}
    }}
)"""

            code_html = f"""<div class='tab-group' style='margin-top:16px'>
  <div class='code-tabs'>
    <div class='tab active' data-target='ts-{ix.name}'>TypeScript</div>
    <div class='tab' data-target='py-{ix.name}'>Python</div>
  </div>
  <div class='code-block'>
    <div class='tab-content active' id='ts-{ix.name}'><pre>{ts_example}</pre></div>
    <div class='tab-content' id='py-{ix.name}'><pre>{py_example}</pre></div>
  </div>
</div>"""

            cards += f"""<div class='ix-card' id='ix-{ix.name}'>
  <div class='ix-header'>
    <div><span class='ix-name'>{ix.camel_name}</span><span class='ix-doc'>{doc}</span></div>
    <span class='chevron'>›</span>
  </div>
  <div class='ix-body'>
    {args_html}
    {accs_html}
    {code_html}
  </div>
</div>"""

        return f"<section id='instructions'><h2>📋 Instructions</h2>{cards}</section>"

    def _render_accounts_section(self, idl: AnchorIDL) -> str:
        if not idl.accounts:
            return ""
        cards = ""
        for acc in idl.accounts:
            rows = "".join(
                f"<tr><td><strong>{f.name}</strong></td><td><span class='type-badge'>{f.type_str}</span></td><td class='ts-type'>{f.ts_type}</td><td class='py-type'>{f.py_type}</td></tr>"
                for f in acc.fields
            )
            cards += f"""<div class='ix-card' id='acc-{acc.name}'>
  <div class='ix-header'><span class='ix-name' style='color:var(--green)'>{acc.pascal_name}</span><span class='chevron'>›</span></div>
  <div class='ix-body'><table><tr><th>Field</th><th>IDL Type</th><th>TypeScript</th><th>Python</th></tr>{rows}</table></div>
</div>"""
        return f"<section id='accounts'><h2>🗂️ Account Types</h2>{cards}</section>"

    def _render_events_section(self, idl: AnchorIDL) -> str:
        if not idl.events:
            return ""
        rows = "".join(
            f"<tr><td style='color:var(--yellow)'><strong>{ev.name}</strong></td><td>{', '.join(f.name for f in ev.fields)}</td><td>{', '.join(f.type_str for f in ev.fields)}</td></tr>"
            for ev in idl.events
        )
        return f"<section id='events'><h2>⚡ Events</h2><table><tr><th>Event</th><th>Fields</th><th>Types</th></tr>{rows}</table></section>"

    def _render_errors_section(self, idl: AnchorIDL) -> str:
        if not idl.errors:
            return ""
        rows = "".join(
            f"<tr><td class='error-code'>{err.code}</td><td style='font-family:monospace;color:#888'>0x{err.code:04x}</td><td style='color:var(--red)'>{err.name}</td><td style='color:var(--dim)'>{err.msg}</td></tr>"
            for err in idl.errors
        )
        return f"<section id='errors'><h2>❌ Error Codes</h2><table><tr><th>Code</th><th>Hex</th><th>Name</th><th>Message</th></tr>{rows}</table></section>"

    def _render_types_section(self, idl: AnchorIDL) -> str:
        if not idl.types:
            return ""
        cards = ""
        for t in idl.types:
            if t.kind == "struct":
                rows = "".join(f"<tr><td><strong>{f.name}</strong></td><td><span class='type-badge'>{f.type_str}</span></td></tr>" for f in t.fields)
                cards += f"<div class='ix-card'><div class='ix-header'><span class='ix-name' style='color:var(--orange)'>{t.name}</span> <small style='color:var(--dim)'>struct</small><span class='chevron'>›</span></div><div class='ix-body'><table><tr><th>Field</th><th>Type</th></tr>{rows}</table></div></div>"
            elif t.kind == "enum":
                variants = ", ".join(f"<code>{v.name}</code>" for v in t.variants)
                cards += f"<div class='ix-card'><div class='ix-header'><span class='ix-name' style='color:var(--orange)'>{t.name}</span> <small style='color:var(--dim)'>enum</small><span class='chevron'>›</span></div><div class='ix-body'><p style='color:var(--dim);font-size:0.85rem'>Variants: {variants}</p></div></div>"
        return f"<section id='types'><h2>🧩 Custom Types</h2>{cards}</section>"

    def _ts_example_val(self, ts_type: str) -> str:
        examples = {
            "PublicKey": "new PublicKey('...')",
            "BN": "new BN(1000)",
            "number": "1",
            "boolean": "true",
            "string": '"..."',
            "Buffer": "Buffer.from([])",
        }
        return examples.get(ts_type, "/* ... */")

    def _py_example_val(self, py_type: str) -> str:
        examples = {
            "Pubkey": "Pubkey.from_string('...')",
            "int": "1000",
            "bool": "True",
            "str": '"..."',
            "bytes": "b''",
            "float": "1.0",
        }
        return examples.get(py_type, "...")
