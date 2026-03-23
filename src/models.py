"""
IDL Models — Parses Anchor IDL JSON into structured Python objects.

Supports Anchor IDL format v0.26 through v0.30+.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ─── IDL Type System ─────────────────────────────────────────────────────────

def parse_idl_type(raw: Any) -> str:
    """
    Recursively parse an IDL type descriptor into a human-readable string.

    Examples:
      "u64"                    → "u64"
      {"option": "publicKey"}  → "Option<publicKey>"
      {"vec": "u8"}            → "Vec<u8>"
      {"defined": "MyStruct"}  → "MyStruct"
      {"array": ["u8", 32]}    → "[u8; 32]"
    """
    if isinstance(raw, str):
        return raw

    if isinstance(raw, dict):
        if "option" in raw:
            return f"Option<{parse_idl_type(raw['option'])}>"
        if "vec" in raw:
            return f"Vec<{parse_idl_type(raw['vec'])}>"
        if "defined" in raw:
            defined = raw["defined"]
            if isinstance(defined, dict):
                return defined.get("name", str(defined))
            return str(defined)
        if "array" in raw:
            elem, size = raw["array"]
            return f"[{parse_idl_type(elem)}; {size}]"
        if "coption" in raw:
            return f"COption<{parse_idl_type(raw['coption'])}>"

    return str(raw)


def ts_type(idl_type: str) -> str:
    """Map IDL type string to TypeScript type."""
    mapping = {
        "publicKey": "PublicKey",
        "u8": "number",
        "u16": "number",
        "u32": "number",
        "i8": "number",
        "i16": "number",
        "i32": "number",
        "u64": "BN",
        "u128": "BN",
        "i64": "BN",
        "i128": "BN",
        "f32": "number",
        "f64": "number",
        "bool": "boolean",
        "string": "string",
        "bytes": "Buffer",
    }
    if idl_type.startswith("Option<"):
        inner = idl_type[7:-1]
        return f"{ts_type(inner)} | null"
    if idl_type.startswith("Vec<"):
        inner = idl_type[4:-1]
        return f"{ts_type(inner)}[]"
    if idl_type.startswith("[") and ";" in idl_type:
        inner = idl_type[1:idl_type.index(";")].strip()
        return f"{ts_type(inner)}[]"
    return mapping.get(idl_type, idl_type)


def py_type(idl_type: str) -> str:
    """Map IDL type string to Python type hint."""
    mapping = {
        "publicKey": "Pubkey",
        "u8": "int",
        "u16": "int",
        "u32": "int",
        "i8": "int",
        "i16": "int",
        "i32": "int",
        "u64": "int",
        "u128": "int",
        "i64": "int",
        "i128": "int",
        "f32": "float",
        "f64": "float",
        "bool": "bool",
        "string": "str",
        "bytes": "bytes",
    }
    if idl_type.startswith("Option<"):
        inner = idl_type[7:-1]
        return f"Optional[{py_type(inner)}]"
    if idl_type.startswith("Vec<"):
        inner = idl_type[4:-1]
        return f"List[{py_type(inner)}]"
    if idl_type.startswith("[") and ";" in idl_type:
        inner = idl_type[1:idl_type.index(";")].strip()
        return f"List[{py_type(inner)}]"
    return mapping.get(idl_type, idl_type)


# ─── IDL Data Models ─────────────────────────────────────────────────────────

@dataclass
class IdlField:
    name: str
    type_str: str          # e.g. "u64", "Option<publicKey>", "Vec<u8>"
    docs: list[str] = field(default_factory=list)

    @property
    def ts_type(self) -> str:
        return ts_type(self.type_str)

    @property
    def py_type(self) -> str:
        return py_type(self.type_str)


@dataclass
class IdlAccount:
    name: str
    is_mut: bool
    is_signer: bool
    is_optional: bool = False
    docs: list[str] = field(default_factory=list)

    @property
    def flags(self) -> str:
        parts = []
        if self.is_mut:
            parts.append("mut")
        if self.is_signer:
            parts.append("signer")
        if self.is_optional:
            parts.append("optional")
        return ", ".join(parts) if parts else "—"


@dataclass
class IdlInstruction:
    name: str
    accounts: list[IdlAccount]
    args: list[IdlField]
    docs: list[str] = field(default_factory=list)
    returns: Optional[str] = None

    @property
    def camel_name(self) -> str:
        parts = self.name.split("_")
        return parts[0] + "".join(p.title() for p in parts[1:])

    @property
    def pascal_name(self) -> str:
        return "".join(p.title() for p in self.name.split("_"))


@dataclass
class IdlStructField:
    name: str
    type_str: str

    @property
    def ts_type(self) -> str:
        return ts_type(self.type_str)

    @property
    def py_type(self) -> str:
        return py_type(self.type_str)


@dataclass
class IdlAccountType:
    name: str
    fields: list[IdlStructField]

    @property
    def pascal_name(self) -> str:
        return self.name[0].upper() + self.name[1:]


@dataclass
class IdlEnumVariant:
    name: str
    fields: list[IdlStructField] = field(default_factory=list)


@dataclass
class IdlCustomType:
    name: str
    kind: str                    # "struct" or "enum"
    fields: list[IdlStructField] = field(default_factory=list)
    variants: list[IdlEnumVariant] = field(default_factory=list)


@dataclass
class IdlError:
    code: int
    name: str
    msg: str

    @property
    def class_name(self) -> str:
        return f"{self.name}Error"


@dataclass
class IdlEvent:
    name: str
    fields: list[IdlStructField]


@dataclass
class AnchorIDL:
    """Parsed representation of a full Anchor IDL JSON."""
    name: str
    version: str
    instructions: list[IdlInstruction]
    accounts: list[IdlAccountType]
    events: list[IdlEvent]
    errors: list[IdlError]
    types: list[IdlCustomType]
    metadata: dict = field(default_factory=dict)
    address: str = ""

    @property
    def program_name(self) -> str:
        return self.name

    @property
    def class_name(self) -> str:
        parts = self.name.replace("-", "_").split("_")
        return "".join(p.title() for p in parts) + "Client"

    @property
    def display_name(self) -> str:
        return self.name.replace("_", " ").replace("-", " ").title()


# ─── IDL Parser ──────────────────────────────────────────────────────────────

class IdlParser:
    """Parses raw Anchor IDL JSON into structured AnchorIDL objects."""

    def parse_file(self, path: str) -> AnchorIDL:
        with open(path, "r") as f:
            raw = json.load(f)
        return self.parse(raw)

    def parse(self, raw: dict) -> AnchorIDL:
        """Parse a raw IDL dict (from JSON) into an AnchorIDL."""
        name = raw.get("name", "unknown_program")
        version = raw.get("version", "0.0.0")
        metadata = raw.get("metadata", {})

        # Support both Anchor v0.26 (metadata.address) and v0.30 (address field)
        address = (
            raw.get("address") or
            metadata.get("address") or
            ""
        )

        instructions = [self._parse_instruction(ix) for ix in raw.get("instructions", [])]
        accounts     = [self._parse_account_type(acc) for acc in raw.get("accounts", [])]
        events       = [self._parse_event(ev) for ev in raw.get("events", [])]
        errors       = [self._parse_error(err) for err in raw.get("errors", [])]
        types        = [self._parse_custom_type(t) for t in raw.get("types", [])]

        return AnchorIDL(
            name=name,
            version=version,
            instructions=instructions,
            accounts=accounts,
            events=events,
            errors=errors,
            types=types,
            metadata=metadata,
            address=address,
        )

    def _parse_instruction(self, raw: dict) -> IdlInstruction:
        accounts = [self._parse_ix_account(acc) for acc in raw.get("accounts", [])]
        args = [
            IdlField(
                name=f.get("name", "arg"),
                type_str=parse_idl_type(f.get("type", "bytes")),
                docs=f.get("docs", []),
            )
            for f in raw.get("args", [])
        ]
        returns = parse_idl_type(raw["returns"]) if "returns" in raw and raw["returns"] else None
        return IdlInstruction(
            name=raw.get("name", "unknown"),
            accounts=accounts,
            args=args,
            docs=raw.get("docs", []),
            returns=returns,
        )

    def _parse_ix_account(self, raw: dict) -> IdlAccount:
        return IdlAccount(
            name=raw.get("name", "account"),
            is_mut=raw.get("isMut", raw.get("writable", False)),
            is_signer=raw.get("isSigner", raw.get("signer", False)),
            is_optional=raw.get("isOptional", raw.get("optional", False)),
            docs=raw.get("docs", []),
        )

    def _parse_account_type(self, raw: dict) -> IdlAccountType:
        type_def = raw.get("type", {})
        fields = [
            IdlStructField(
                name=f.get("name", "field"),
                type_str=parse_idl_type(f.get("type", "bytes")),
            )
            for f in type_def.get("fields", [])
        ]
        return IdlAccountType(name=raw.get("name", "Account"), fields=fields)

    def _parse_event(self, raw: dict) -> IdlEvent:
        fields = [
            IdlStructField(
                name=f.get("name", "field"),
                type_str=parse_idl_type(f.get("type", "bytes")),
            )
            for f in raw.get("fields", [])
        ]
        return IdlEvent(name=raw.get("name", "Event"), fields=fields)

    def _parse_error(self, raw: dict) -> IdlError:
        return IdlError(
            code=int(raw.get("code", 6000)),
            name=raw.get("name", "UnknownError"),
            msg=raw.get("msg", ""),
        )

    def _parse_custom_type(self, raw: dict) -> IdlCustomType:
        type_def = raw.get("type", {})
        kind = type_def.get("kind", "struct")

        fields = []
        variants = []

        if kind == "struct":
            fields = [
                IdlStructField(
                    name=f.get("name", "field"),
                    type_str=parse_idl_type(f.get("type", "bytes")),
                )
                for f in type_def.get("fields", [])
            ]
        elif kind == "enum":
            for v in type_def.get("variants", []):
                variant_fields = [
                    IdlStructField(
                        name=vf.get("name", "field"),
                        type_str=parse_idl_type(vf.get("type", "bytes")),
                    )
                    for vf in (v.get("fields") or [])
                ]
                variants.append(IdlEnumVariant(name=v.get("name", "Variant"), fields=variant_fields))

        return IdlCustomType(
            name=raw.get("name", "Type"),
            kind=kind,
            fields=fields,
            variants=variants,
        )
