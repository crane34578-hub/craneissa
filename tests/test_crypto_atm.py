from decimal import Decimal
import unittest

from crypto_atm import CryptoATMBackend, q8


class CryptoATMTests(unittest.TestCase):
    def test_successful_transfer_records_chain_tx(self) -> None:
        atm = CryptoATMBackend(network_fee_rate="0.01")
        atm.create_wallet("sender")
        atm.create_wallet("receiver")

        atm.fund_wallet("sender", "100")
        tx = atm.transfer_via_atm("sender", "receiver", "20")

        self.assertEqual(tx.status, "confirmed")
        self.assertEqual(len(atm.blockchain.chain), 1)
        self.assertEqual(atm.wallet_balance("receiver"), q8("20"))
        self.assertEqual(atm.wallet_balance("sender"), q8("79.8"))

    def test_insufficient_balance_raises(self) -> None:
        atm = CryptoATMBackend(network_fee_rate="0.005")
        atm.create_wallet("sender")
        atm.create_wallet("receiver")
        atm.fund_wallet("sender", "5")

        with self.assertRaises(ValueError):
            atm.transfer_via_atm("sender", "receiver", "10")

    def test_rejects_non_positive_amount(self) -> None:
        atm = CryptoATMBackend()
        atm.create_wallet("sender")
        atm.create_wallet("receiver")
        atm.fund_wallet("sender", "50")

        with self.assertRaises(ValueError):
            atm.transfer_via_atm("sender", "receiver", Decimal("0"))


if __name__ == "__main__":
    unittest.main()
