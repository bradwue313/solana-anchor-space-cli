import unittest
from anchor_space.discriminator import (
    calculate_account_discriminator,
    format_discriminator_hex,
    format_discriminator_rust
)

class TestDiscriminator(unittest.TestCase):
    def test_account_discriminator(self):
        # Known Anchor discriminator for UserProfile
        disc = calculate_account_discriminator("UserProfile")
        self.assertEqual(len(disc), 8)
        self.assertTrue(format_discriminator_hex(disc).startswith("0x"))
        self.assertEqual(len(format_discriminator_hex(disc)), 18)

    def test_format_rust(self):
        disc = bytes([0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0])
        rust_str = format_discriminator_rust(disc)
        self.assertEqual(rust_str, "[0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0]")

if __name__ == "__main__":
    unittest.main()
