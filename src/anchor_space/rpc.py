import urllib.request
import json
from typing import Dict, Any, Optional

DEFAULT_RPC = "https://api.mainnet-beta.solana.com"

def inspect_onchain_account(pubkey: str, rpc_url: str = DEFAULT_RPC) -> Dict[str, Any]:
    """
    Fetches real account info from Solana RPC and evaluates its space and rent status.
    """
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            pubkey,
            {"encoding": "base64"}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "AnchorSpace/0.1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            val = data.get("result", {}).get("value")
            if not val:
                return {"error": "Account not found or uninitialized"}

            lamports = val.get("lamports", 0)
            data_arr = val.get("data", ["", "base64"])
            owner = val.get("owner", "")
            executable = val.get("executable", False)
            rent_epoch = val.get("rentEpoch", 0)

            # Estimate data size
            import base64
            try:
                raw_bytes = base64.b64decode(data_arr[0])
                data_len = len(raw_bytes)
            except Exception:
                data_len = 0

            # Calculate theoretical rent
            total_storage = data_len + 128
            req_lamports = total_storage * 3480 * 2
            is_exempt = lamports >= req_lamports
            surplus = lamports - req_lamports

            return {
                "pubkey": pubkey,
                "lamports": lamports,
                "sol": lamports / 1e9,
                "data_len": data_len,
                "owner": owner,
                "executable": executable,
                "rent_epoch": rent_epoch,
                "is_rent_exempt": is_exempt,
                "required_rent_lamports": req_lamports,
                "required_rent_sol": req_lamports / 1e9,
                "surplus_lamports": surplus,
                "surplus_sol": surplus / 1e9
            }
    except Exception as e:
        return {"error": str(e)}
