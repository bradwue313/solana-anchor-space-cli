import hashlib

def calculate_account_discriminator(account_name: str) -> bytes:
    """
    Computes the 8-byte Anchor account discriminator:
    sha256("account:<AccountName>")[0..8]
    """
    preimage = f"account:{account_name}".encode("utf-8")
    return hashlib.sha256(preimage).digest()[:8]

def calculate_instruction_discriminator(ix_name: str) -> bytes:
    """
    Computes the 8-byte Anchor instruction discriminator:
    sha256("global:<InstructionName>")[0..8]
    """
    preimage = f"global:{ix_name}".encode("utf-8")
    return hashlib.sha256(preimage).digest()[:8]

def format_discriminator_hex(disc: bytes) -> str:
    return "0x" + disc.hex()

def format_discriminator_rust(disc: bytes) -> str:
    return "[" + ", ".join(f"0x{b:02x}" for b in disc) + "]"
