# 🪐 Solana Anchor Space CLI (`anchor-space`)

[![CI](https://github.com/bradwue313/solana-anchor-space-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/bradwue313/solana-anchor-space-cli/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-brightgreen.svg)](https://www.python.org/downloads/)
[![Solana](https://img.shields.io/badge/Solana-Web3-purple.svg)](https://solana.com)

High-performance CLI and static analysis toolkit for **Solana & Anchor** developers to calculate exact account byte layouts, discriminator offsets, and on-chain rent-exemption costs.

```
   ___             __                ___                           
  / _ | ___  ____ / /  ___  ____    / __| ___  ___ _  ____ ___    
 / __ |/ _ \/ __// _ \/ _ \/ __/    \__ \/ _ \/ _ `/ / __// -_)   
/_/ |_/_//_/\__//_//_/\___/_/       |___/ .__/\_,_/  \__/ \__/    
                                        /_/  Solana Account Sizer
```

---

## ⚡ The Problem

Every Solana program built with Anchor requires allocating account space during initialization:
```rust
#[account(
    init,
    payer = user,
    space = 8 + UserProfile::INIT_SPACE
)]
pub user_profile: Account<'info, UserProfile>,
```

* **Under-allocating** bytes causes on-chain transactions to panic immediately with `AccountDidNotDeserialize` or out-of-bounds memory errors.
* **Over-allocating** bytes permanently locks up user funds in unnecessary Solana rent-exemption fees (`~0.00089 SOL` per byte overhead).
* Manually tracking byte alignment for nested structs, `Pubkey` (32 bytes), dynamic Borsh strings (`4 + len`), vectors (`4 + n * size`), and option flags (`1 + size`) is tedious and error-prone.

**`anchor-space`** solves this in milliseconds.

---

## 🚀 Key Features

* 📐 **Zero-Config Account Sizer:** Parse raw field specs on the CLI, Anchor IDL JSON files, or native Rust `.rs` source files.
* 🛡️ **Anchor Discriminator Engine:** Computes the official 8-byte Anchor discriminator (`sha256("account:<Name>")[0..8]`) in hex and Rust byte-array format.
* 💰 **Solana Rent Calculator:** Computes exact lamport requirements, SOL cost, and USD value based on real-time Solana rent curves (`(128 + data_len) * 3480 * 2`).
* 🔍 **Live On-Chain Inspector:** Queries Solana mainnet/devnet RPC to inspect live accounts, compare data length vs. allocation, and identify surplus rent.
* 📋 **Clean ASCII Visualizer:** Generates formatted offset maps and instant copy-paste Anchor initialization code.

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/bradwue313/solana-anchor-space-cli.git
cd solana-anchor-space-cli

# Install locally
pip install .
```

Or install directly via git:
```bash
pip install git+https://github.com/bradwue313/solana-anchor-space-cli.git
```

---

## 💻 Usage & Examples

### 1. Quick Field Calculation
Calculate layout and rent for an account on the fly:
```bash
anchor-space calc --name UserProfile --fields "authority:Pubkey,username:String:24,score:u64,is_active:bool"
```

**Output:**
```
Account 'UserProfile' Layout:
+--------+-----------------+--------+-------+------------------------------+
| Offset | Field           | Type   | Bytes | Notes                        |
+--------+-----------------+--------+-------+------------------------------+
| 0..7   | __discriminator | u64    | 8     | Anchor 8-byte discriminator  |
| 8..39  | authority       | Pubkey | 32    |                              |
| 40..67 | username        | String | 28    | 4 byte prefix + max 24 chars |
| 68..75 | score           | u64    | 8     |                              |
| 76..76 | is_active       | bool   | 1     |                              |
+--------+-----------------+--------+-------+------------------------------+

Total Space: 77 bytes | Rent: 1,426,800 lamports (0.001427 SOL ~ $0.26)
```

---

### 2. Inspect Rust Source Code Directly
Scan any Anchor `.rs` file containing `#[account]` structs:
```bash
anchor-space inspect programs/my-program/src/state.rs
```

Generates the exact Anchor initialization constraints:
```rust
#[account(
    init,
    payer = authority,
    space = 8 + UserProfile::INIT_SPACE
)]
pub user_profile: Account<'info, UserProfile>,
```

---

### 3. Inspect Live On-Chain Accounts
Verify live rent-exemption and allocation status directly from the Solana cluster:
```bash
anchor-space onchain JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4
```

**Output:**
```
On-Chain Account Status:
  • Address:            JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4
  • Owner Program:      BPFLoaderUpgradeab1e11111111111111111111111
  • Data Length:        36 bytes
  • Lamport Balance:    1,141,440 (0.001141 SOL)
  • Rent-Exempt:        ✅ YES
  • Required Exemption: 1,141,440 lamports (0.001141 SOL)
```

---

### 4. Anchor Discriminator Generator
Compute the exact 8-byte discriminator for accounts or instructions:
```bash
anchor-space disc UserProfile
```
**Output:**
```
Account:        UserProfile
Hex:            0x208c909b910b89b8
Rust Array:     [0x20, 0x8c, 0x90, 0x9b, 0x91, 0x0b, 0x89, 0xb8]
```

---

## 🧪 Testing

Run the full unit test battery:
```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

---

## 📜 License

MIT License © 2026 Brad Wu ([@bradwue313](https://github.com/bradwue313)).
Contributions welcome!
