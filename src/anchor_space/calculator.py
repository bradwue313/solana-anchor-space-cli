from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

ACCOUNT_METADATA_OVERHEAD = 128  # bytes
LAMPORTS_PER_BYTE_YEAR = 3480
EXEMPTION_YEARS = 2
LAMPORTS_PER_SOL = 1_000_000_000

PRIMITIVE_SIZES: Dict[str, int] = {
    "bool": 1,
    "u8": 1,
    "i8": 1,
    "u16": 2,
    "i16": 2,
    "u32": 4,
    "i32": 4,
    "f32": 4,
    "u64": 8,
    "i64": 8,
    "f64": 8,
    "u128": 16,
    "i128": 16,
    "Pubkey": 32,
    "pubkey": 32,
    "publicKey": 32,
}

@dataclass
class FieldLayout:
    name: str
    type_name: str
    size: int
    offset: int
    is_dynamic: bool = False
    notes: str = ""

@dataclass
class AccountLayout:
    name: str
    discriminator_size: int = 8
    fields: List[FieldLayout] = field(default_factory=list)
    total_data_bytes: int = 0
    total_space_required: int = 0
    rent_lamports: int = 0
    rent_sol: float = 0.0
    rent_usdc_estimate: float = 0.0

def calculate_rent_exemption(data_len: int, sol_price_usd: float = 180.0) -> Dict[str, Any]:
    """
    Computes Solana rent exemption in lamports, SOL, and estimated USD.
    Formula: (data_len + 128) * 3480 * 2
    """
    total_storage = data_len + ACCOUNT_METADATA_OVERHEAD
    lamports = total_storage * LAMPORTS_PER_BYTE_YEAR * EXEMPTION_YEARS
    sol = lamports / LAMPORTS_PER_SOL
    usd = sol * sol_price_usd
    return {
        "lamports": lamports,
        "sol": sol,
        "usd": usd,
        "data_len": data_len,
        "total_storage_bytes": total_storage
    }

def analyze_fields(account_name: str, raw_fields: List[Dict[str, Any]], sol_price_usd: float = 180.0) -> AccountLayout:
    """
    Given a list of fields [{name: str, type: str, max_len?: int}],
    calculates byte offsets, total space, and rent exemption.
    """
    offset = 8  # Start after 8-byte Anchor discriminator
    fields_layout: List[FieldLayout] = []

    for f in raw_fields:
        f_name = f.get("name", "unnamed")
        f_type = f.get("type", "u8")
        max_len = f.get("max_len", 32)

        size = 0
        is_dynamic = False
        notes = ""

        if f_type in PRIMITIVE_SIZES:
            size = PRIMITIVE_SIZES[f_type]
        elif f_type == "String" or f_type == "string":
            # 4 bytes for length prefix + max characters
            size = 4 + max_len
            is_dynamic = True
            notes = f"4 byte prefix + max {max_len} chars"
        elif f_type.startswith("Vec<") or f_type.startswith("vec<"):
            inner = f_type[4:-1].strip()
            inner_size = PRIMITIVE_SIZES.get(inner, 1)
            size = 4 + (max_len * inner_size)
            is_dynamic = True
            notes = f"4 byte prefix + {max_len} items of {inner} ({inner_size}B)"
        elif f_type.startswith("[u8;") or f_type.startswith("[u8;"):
            # Fixed byte array e.g. [u8; 32]
            try:
                length = int(f_type.split(";")[1].replace("]", "").strip())
                size = length
            except Exception:
                size = 32
        elif f_type.startswith("Option<"):
            inner = f_type[7:-1].strip()
            inner_size = PRIMITIVE_SIZES.get(inner, 1)
            size = 1 + inner_size
            notes = f"1 byte flag + {inner} ({inner_size}B)"
        else:
            # Fallback custom struct/enum default estimate
            size = 32
            notes = "estimated custom type"

        layout = FieldLayout(
            name=f_name,
            type_name=f_type,
            size=size,
            offset=offset,
            is_dynamic=is_dynamic,
            notes=notes
        )
        fields_layout.append(layout)
        offset += size

    total_space = offset
    total_data_bytes = offset - 8
    rent_info = calculate_rent_exemption(total_space, sol_price_usd)

    return AccountLayout(
        name=account_name,
        discriminator_size=8,
        fields=fields_layout,
        total_data_bytes=total_data_bytes,
        total_space_required=total_space,
        rent_lamports=rent_info["lamports"],
        rent_sol=rent_info["sol"],
        rent_usdc_estimate=rent_info["usd"]
    )
