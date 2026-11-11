import unittest
from anchor_space.calculator import (
    calculate_rent_exemption,
    analyze_fields,
    ACCOUNT_METADATA_OVERHEAD,
    LAMPORTS_PER_BYTE_YEAR,
    EXEMPTION_YEARS
)

class TestCalculator(unittest.TestCase):
    def test_rent_exemption_zero(self):
        res = calculate_rent_exemption(0)
        expected_lamports = ACCOUNT_METADATA_OVERHEAD * LAMPORTS_PER_BYTE_YEAR * EXEMPTION_YEARS
        self.assertEqual(res["lamports"], expected_lamports)
        self.assertAlmostEqual(res["sol"], expected_lamports / 1e9)

    def test_analyze_fields_layout(self):
        fields = [
            {"name": "authority", "type": "Pubkey"},
            {"name": "counter", "type": "u64"},
            {"name": "is_active", "type": "bool"},
            {"name": "username", "type": "String", "max_len": 20}
        ]
        layout = analyze_fields("TestAccount", fields)

        # 8 (disc) + 32 (pubkey) + 8 (u64) + 1 (bool) + 4+20 (string) = 73 bytes
        self.assertEqual(layout.discriminator_size, 8)
        self.assertEqual(layout.total_space_required, 73)
        self.assertEqual(len(layout.fields), 4)

        # Verify field offsets
        self.assertEqual(layout.fields[0].offset, 8)
        self.assertEqual(layout.fields[0].size, 32)
        self.assertEqual(layout.fields[1].offset, 40)
        self.assertEqual(layout.fields[1].size, 8)
        self.assertEqual(layout.fields[2].offset, 48)
        self.assertEqual(layout.fields[2].size, 1)
        self.assertEqual(layout.fields[3].offset, 49)
        self.assertEqual(layout.fields[3].size, 24)

if __name__ == "__main__":
    unittest.main()
