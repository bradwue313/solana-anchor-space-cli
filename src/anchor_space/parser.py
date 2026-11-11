import json
import re
from typing import List, Dict, Any, Optional

def parse_idl_json(content: str) -> List[Dict[str, Any]]:
    """
    Parses Anchor IDL JSON and extracts account definitions and field schemas.
    """
    data = json.loads(content)
    results = []

    # Check for Anchor 0.30+ style or legacy IDL style
    accounts = data.get("accounts", [])
    types = data.get("types", [])

    # Map custom types if defined
    type_lookup = {}
    for t in types:
        t_name = t.get("name")
        type_lookup[t_name] = t.get("type", {})

    for acc in accounts:
        acc_name = acc.get("name")
        fields = []

        # Some IDLs store fields directly or in types
        type_def = acc.get("type", {})
        raw_fields = type_def.get("fields", [])
        if not raw_fields and acc_name in type_lookup:
            raw_fields = type_lookup[acc_name].get("fields", [])

        for f in raw_fields:
            fname = f.get("name")
            ftype = f.get("type")
            # Flatten type if it's a dict (e.g. {"defined": "MyCustomType"})
            if isinstance(ftype, dict):
                if "defined" in ftype:
                    ftype = ftype["defined"]
                elif "vec" in ftype:
                    inner = ftype["vec"]
                    ftype = f"Vec<{inner}>"
                elif "option" in ftype:
                    inner = ftype["option"]
                    ftype = f"Option<{inner}>"
                elif "array" in ftype:
                    inner = ftype["array"][0]
                    size = ftype["array"][1]
                    ftype = f"[{inner}; {size}]"
                else:
                    ftype = str(ftype)

            fields.append({
                "name": fname,
                "type": str(ftype),
                "max_len": 64  # default assumption for dynamic types if unspecified
            })

        results.append({
            "name": acc_name,
            "fields": fields
        })

    return results

def parse_rust_source(source_text: str) -> List[Dict[str, Any]]:
    """
    Scans Rust source code for Anchor `#[account]` structs and extracts fields.
    """
    results = []

    # Regex to find #[account] followed by pub struct <Name> { ... }
    struct_pattern = re.compile(
        r'#\[account[^\]]*\]\s*(?:pub\s+)?struct\s+([A-Za-z0-9_]+)\s*\{([^}]+)\}',
        re.MULTILINE
    )

    matches = struct_pattern.findall(source_text)
    for struct_name, struct_body in matches:
        fields = []
        for line in struct_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            # Look for: pub <name>: <type>,
            field_match = re.search(r'(?:pub\s+)?([A-Za-z0-9_]+)\s*:\s*([^,;]+)', line)
            if field_match:
                fname = field_match.group(1).strip()
                ftype = field_match.group(2).strip()
                fields.append({
                    "name": fname,
                    "type": ftype,
                    "max_len": 64
                })

        results.append({
            "name": struct_name,
            "fields": fields
        })

    return results
