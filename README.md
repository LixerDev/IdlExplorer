# 🔍 IdlExplorer

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e69467f5-dada-46dc-b922-0e25175761c1" />


**Built by LixerDev**
Follow me here on my personal Twitter (X): https://x.com/Lix_Devv

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Solana](https://img.shields.io/badge/network-Solana-9945FF)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## 🚀 Quick Start

```bash
git clone https://github.com/LixerDev/IdlExplorer.git
cd IdlExplorer
pip install -r requirements.txt
cp .env.example .env

# Generate everything from a local IDL file
python main.py generate ./my_program.json

# Generate from a deployed program address (fetches IDL from chain)
python main.py from-address TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA

# Inspect IDL structure in the terminal
python main.py inspect ./my_program.json

# Serve interactive docs in the browser (localhost:8080)
python main.py serve ./my_program.json

# Generate only specific outputs
python main.py generate ./idl.json --only ts
python main.py generate ./idl.json --only python
python main.py generate ./idl.json --only docs
```

---

## ✨ What Gets Generated

Given this IDL snippet:
```json
{
  "name": "my_staking",
  "instructions": [
    {
      "name": "stake",
      "accounts": [
        { "name": "pool", "isMut": true, "isSigner": false },
        { "name": "user", "isMut": true, "isSigner": true }
      ],
      "args": [
        { "name": "amount", "type": "u64" }
      ]
    }
  ]
}
```

### 1. TypeScript SDK (`sdk/index.ts`)
```typescript
import { MyStakingClient } from "./sdk";

const client = new MyStakingClient(provider, PROGRAM_ID);

// Fully typed method — accounts auto-derived where possible
const txSig = await client.stake({
  amount: new BN(1_000_000_000),
  accounts: {
    pool: poolPDA,
    user: provider.wallet.publicKey,
  },
});
```

### 2. Python Client (`client/client.py`)
```python
from client import MyStakingClient

client = MyStakingClient(provider, PROGRAM_ID)

# Async method with typed args
tx_sig = await client.stake(
    amount=1_000_000_000,
    accounts={
        "pool": pool_pda,
        "user": provider.wallet.public_key,
    }
)
```

### 3. Interactive HTML Docs
```
output/my_staking/docs/index.html
```
Opens in browser with:
- Full instruction reference with argument types
- Account table with mut/signer flags
- Error code reference
- Copy-paste code examples (TypeScript + Python)
- Account type definitions

---

## 📁 Output Structure

```
output/my-staking/
├── sdk/
│   ├── index.ts          ← Main SDK class with all instruction methods
│   ├── types.ts          ← TypeScript types for all accounts and custom types
│   ├── errors.ts         ← Typed error classes
│   └── package.json
├── client/
│   ├── client.py         ← Python async client class
│   ├── types.py          ← Python dataclasses for all account types
│   └── requirements.txt
└── docs/
    └── index.html        ← Interactive single-page documentation
```

---

## 🔗 Fetching IDL from Chain

Anchor programs store their IDL on-chain at a deterministic address. IdlExplorer fetches it automatically:

```bash
# Fetch IDL from any deployed Anchor program
python main.py from-address <PROGRAM_ID>

# Specify cluster
python main.py from-address <PROGRAM_ID> --cluster devnet
python main.py from-address <PROGRAM_ID> --cluster mainnet-beta

# Just fetch and save the IDL, don't generate
python main.py from-address <PROGRAM_ID> --save-only
```

---

## 🏗️ Architecture

```
main.py (CLI)
    ├── generate  → Parser → [TS Generator, Python Generator, Docs Generator]
    ├── inspect   → Parser → Terminal Renderer (Rich tables)
    ├── serve     → Docs Generator → HTTP server (localhost:8080)
    └── from-address → Fetcher → Parser → Generators

src/
    ├── models.py          IDL parser → AnchorIDL, Instruction, AccountType, etc.
    ├── fetcher.py         Fetch IDL from Solana RPC (any cluster)
    ├── renderer.py        Rich terminal display (tables, colors)
    └── generators/
        ├── typescript.py  TypeScript SDK generator
        ├── python_sdk.py  Python async client generator
        └── docs.py        Interactive HTML documentation generator
```

---

## 📊 Supported IDL Fields

| Field | Supported |
|---|---|
| Instructions (name, accounts, args, docs) | ✅ |
| Account types (struct fields) | ✅ |
| Custom types (enums, structs) | ✅ |
| Error codes | ✅ |
| Events | ✅ |
| Type aliases | ✅ |
| Generics (`Option<T>`, `Vec<T>`) | ✅ |
| Nested types | ✅ |
| Anchor v0.26–0.30 IDL format | ✅ |
| SPL token accounts | ✅ |

---

## 🎯 Supported Type Mappings

| IDL Type | TypeScript | Python |
|---|---|---|
| `publicKey` | `PublicKey` | `Pubkey` |
| `u8/u16/u32` | `number` | `int` |
| `u64/u128/i64` | `BN` | `int` |
| `bool` | `boolean` | `bool` |
| `string` | `string` | `str` |
| `bytes` | `Buffer` | `bytes` |
| `{ option: T }` | `T \| null` | `Optional[T]` |
| `{ vec: T }` | `T[]` | `List[T]` |
| `{ defined: T }` | `T` | `T` |
