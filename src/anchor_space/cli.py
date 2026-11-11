import argparse
import sys
import json
import os
from typing import List, Dict, Any

from anchor_space.calculator import analyze_fields, calculate_rent_exemption
from anchor_space.discriminator import (
    calculate_account_discriminator,
    format_discriminator_hex,
    format_discriminator_rust,
)
from anchor_space.parser import parse_idl_json, parse_rust_source
from anchor_space.rpc import inspect_onchain_account

BANNER = r"""
   ___             __                ___                           
  / _ | ___  ____ / /  ___  ____    / __| ___  ___ _  ____ ___    
 / __ |/ _ \/ __// _ \/ _ \/ __/    \__ \/ _ \/ _ `/ / __// -_)   
/_/ |_/_//_/\__//_//_/\___/_/       |___/ .__/\_,_/  \__/ \__/    
                                        /_/  Solana Account Sizer
"""

def render_table(headers: List[str], rows: List[List[str]]) -> str:
    """Helper to render clean ASCII table without external dependencies"""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(val)))

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    head_str = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    lines = [sep, head_str, sep]
    for row in rows:
        row_str = "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        lines.append(row_str)
    lines.append(sep)
    return "\n".join(lines)

def handle_inspect(args):
    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    accounts = []
    if file_path.endswith(".json"):
        accounts = parse_idl_json(content)
    elif file_path.endswith(".rs"):
        accounts = parse_rust_source(content)
    else:
        # Try JSON first, fallback to Rust
        try:
            accounts = parse_idl_json(content)
        except Exception:
            accounts = parse_rust_source(content)

    if not accounts:
        print("No Anchor account structs or IDL definitions detected in file.")
        return

    sol_price = args.sol_price
    all_results = []

    for acc in accounts:
        name = acc["name"]
        fields = acc["fields"]
        layout = analyze_fields(name, fields, sol_price)
        disc = calculate_account_discriminator(name)

        if args.json:
            all_results.append({
                "account": name,
                "discriminator_hex": format_discriminator_hex(disc),
                "total_space": layout.total_space_required,
                "rent_lamports": layout.rent_lamports,
                "rent_sol": layout.rent_sol,
                "rent_usd": layout.rent_usdc_estimate,
                "fields": [
                    {
                        "name": f.name,
                        "type": f.type_name,
                        "size": f.size,
                        "offset": f.offset,
                        "notes": f.notes
                    }
                    for f in layout.fields
                ]
            })
            continue

        print(f"\n=======================================================")
        print(f" Account: {name}")
        print(f" Discriminator: {format_discriminator_hex(disc)} {format_discriminator_rust(disc)}")
        print(f"=======================================================")

        headers = ["Offset", "Field", "Type", "Bytes", "Notes"]
        rows = [["0..7", "__discriminator", "u64", "8", "Anchor 8-byte discriminator"]]
        for f in layout.fields:
            offset_str = f"{f.offset}..{f.offset + f.size - 1}"
            rows.append([offset_str, f.name, f.type_name, str(f.size), f.notes])

        print(render_table(headers, rows))
        print(f"\nSummary:")
        print(f"  • Data Size:       {layout.total_data_bytes} bytes")
        print(f"  • Total Space:     {layout.total_space_required} bytes (8 disc + {layout.total_data_bytes} data)")
        print(f"  • Rent Exemption:  {layout.rent_lamports:,} lamports ({layout.rent_sol:.6f} SOL ~ ${layout.rent_usdc_estimate:.2f} USD)")
        print(f"\nRecommended Anchor Constraint:")
        print(f"  #[account(\n      init,\n      payer = authority,\n      space = 8 + {name}::INIT_SPACE\n  )]")
        print(f"  pub {name.lower()}: Account<'info, {name}>,")

    if args.json:
        print(json.dumps(all_results, indent=2))

def handle_calc(args):
    """Parses command-line format: name:type[:maxlen]"""
    field_specs = args.fields.split(",")
    parsed_fields = []
    for spec in field_specs:
        parts = spec.strip().split(":")
        fname = parts[0]
        ftype = parts[1] if len(parts) > 1 else "u8"
        maxlen = int(parts[2]) if len(parts) > 2 else 32
        parsed_fields.append({"name": fname, "type": ftype, "max_len": maxlen})

    layout = analyze_fields(args.name, parsed_fields, args.sol_price)
    disc = calculate_account_discriminator(args.name)

    if args.json:
        res = {
            "account": args.name,
            "discriminator": format_discriminator_hex(disc),
            "total_space": layout.total_space_required,
            "rent_lamports": layout.rent_lamports,
            "rent_sol": layout.rent_sol,
            "rent_usd": layout.rent_usdc_estimate,
        }
        print(json.dumps(res, indent=2))
        return

    print(f"\nAccount '{args.name}' Layout:")
    headers = ["Offset", "Field", "Type", "Bytes", "Notes"]
    rows = [["0..7", "__discriminator", "u64", "8", "Anchor 8-byte discriminator"]]
    for f in layout.fields:
        offset_str = f"{f.offset}..{f.offset + f.size - 1}"
        rows.append([offset_str, f.name, f.type_name, str(f.size), f.notes])
    print(render_table(headers, rows))
    print(f"\nTotal Space: {layout.total_space_required} bytes | Rent: {layout.rent_lamports:,} lamports ({layout.rent_sol:.6f} SOL ~ ${layout.rent_usdc_estimate:.2f})")

def handle_onchain(args):
    print(f"Querying Solana RPC for account '{args.pubkey}'...")
    res = inspect_onchain_account(args.pubkey, args.rpc)
    if "error" in res:
        print(f"RPC Error: {res['error']}")
        sys.exit(1)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    print("\nOn-Chain Account Status:")
    print(f"  • Address:            {res['pubkey']}")
    print(f"  • Owner Program:      {res['owner']}")
    print(f"  • Data Length:        {res['data_len']} bytes")
    print(f"  • Lamport Balance:    {res['lamports']:,} ({res['sol']:.6f} SOL)")
    print(f"  • Rent-Exempt:        {'✅ YES' if res['is_rent_exempt'] else '❌ NO'}")
    print(f"  • Required Exemption: {res['required_rent_lamports']:,} lamports ({res['required_rent_sol']:.6f} SOL)")
    if res['surplus_lamports'] > 0:
        print(f"  • Rent Surplus:       +{res['surplus_lamports']:,} lamports (+{res['surplus_sol']:.6f} SOL)")

def handle_disc(args):
    disc = calculate_account_discriminator(args.name)
    print(f"Account:        {args.name}")
    print(f"Hex:            {format_discriminator_hex(disc)}")
    print(f"Rust Array:     {format_discriminator_rust(disc)}")

def main():
    parser = argparse.ArgumentParser(
        prog="anchor-space",
        description="High-performance CLI & static analysis toolkit for Solana & Anchor account space & rent optimization."
    )
    parser.add_argument("--sol-price", type=float, default=180.0, help="SOL price in USD for cost estimation (default: 180.0)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect an Anchor IDL JSON or Rust source file")
    p_inspect.add_argument("file", help="Path to IDL .json or Rust .rs file")

    # calc
    p_calc = subparsers.add_parser("calc", help="Quick command-line calculation of fields")
    p_calc.add_argument("--name", default="MyAccount", help="Account struct name")
    p_calc.add_argument("--fields", required=True, help="Comma-separated field specs: 'name:type[:maxlen]' (e.g. 'owner:Pubkey,username:String:32,points:u64')")

    # onchain
    p_onchain = subparsers.add_parser("onchain", help="Inspect live account on Solana mainnet/devnet")
    p_onchain.add_argument("pubkey", help="Solana public key (base58)")
    p_onchain.add_argument("--rpc", default="https://api.mainnet-beta.solana.com", help="Solana RPC URL")

    # discriminator
    p_disc = subparsers.add_parser("disc", help="Calculate Anchor 8-byte discriminator for an account name")
    p_disc.add_argument("name", help="Account name (e.g. UserProfile)")

    args = parser.parse_args()

    if not args.json:
        print(BANNER)

    if args.command == "inspect":
        handle_inspect(args)
    elif args.command == "calc":
        handle_calc(args)
    elif args.command == "onchain":
        handle_onchain(args)
    elif args.command == "disc":
        handle_disc(args)

if __name__ == "__main__":
    main()
