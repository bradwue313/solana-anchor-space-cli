import unittest
import json
from anchor_space.parser import parse_idl_json, parse_rust_source

class TestParser(unittest.TestCase):
    def test_parse_rust_struct(self):
        rust_src = """
        use anchor_lang::prelude::*;

        #[account]
        pub struct EscrowState {
            pub maker: Pubkey,
            pub mint_a: Pubkey,
            pub mint_b: Pubkey,
            pub amount: u64,
            pub bump: u8,
        }
        """
        accounts = parse_rust_source(rust_src)
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]["name"], "EscrowState")
        fields = accounts[0]["fields"]
        self.assertEqual(len(fields), 5)
        self.assertEqual(fields[0]["name"], "maker")
        self.assertEqual(fields[0]["type"], "Pubkey")
        self.assertEqual(fields[4]["name"], "bump")
        self.assertEqual(fields[4]["type"], "u8")

    def test_parse_idl_json(self):
        idl_src = json.dumps({
            "version": "0.1.0",
            "name": "my_program",
            "accounts": [
                {
                    "name": "Vault",
                    "type": {
                        "kind": "struct",
                        "fields": [
                            {"name": "owner", "type": "publicKey"},
                            {"name": "balance", "type": "u64"}
                        ]
                    }
                }
            ]
        })
        accounts = parse_idl_json(idl_src)
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]["name"], "Vault")
        self.assertEqual(len(accounts[0]["fields"]), 2)

if __name__ == "__main__":
    unittest.main()
