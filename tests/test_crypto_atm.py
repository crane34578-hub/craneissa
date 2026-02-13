from decimal import Decimal
import random
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

        for amount in (Decimal("0"), Decimal("-0.1")):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    atm.transfer_via_atm("sender", "receiver", amount)

    def test_duplicate_wallet_rejected(self) -> None:
        atm = CryptoATMBackend()
        atm.create_wallet("sender")

        with self.assertRaises(ValueError):
            atm.create_wallet("sender")

    def test_currency_mismatch_rejected(self) -> None:
        atm = CryptoATMBackend()
        atm.create_wallet("sender", currency="USDC")
        atm.create_wallet("receiver", currency="BTC")
        atm.fund_wallet("sender", "100")

        with self.assertRaises(ValueError):
            atm.transfer_via_atm("sender", "receiver", "5")

    def test_tx_lookup_and_audit_log(self) -> None:
        atm = CryptoATMBackend(network_fee_rate="0.015")
        atm.create_wallet("alice")
        atm.create_wallet("bob")
        atm.fund_wallet("alice", "100")

        tx = atm.transfer_via_atm("alice", "bob", "25")
        found = atm.blockchain.get_transaction(tx.tx_id)

        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.block_hash, tx.block_hash)
        self.assertEqual(atm.audit_log[-1]["event"], "atm_transfer")
        self.assertEqual(atm.audit_log[-1]["tx_id"], tx.tx_id)

    def test_fee_rounding_quantized_to_8_decimals(self) -> None:
        atm = CryptoATMBackend(network_fee_rate="0.00333333")
        atm.create_wallet("alice")
        atm.create_wallet("bob")
        atm.fund_wallet("alice", "1")

        tx = atm.transfer_via_atm("alice", "bob", "0.12345678")

        self.assertEqual(tx.network_fee.as_tuple().exponent, -8)
        expected_fee = q8(Decimal("0.12345678") * Decimal("0.00333333"))
        self.assertEqual(tx.network_fee, expected_fee)

    def test_high_volume_randomized_transfers_preserve_invariants(self) -> None:
        random.seed(7)
        atm = CryptoATMBackend(network_fee_rate="0.0025")
        users = [f"u{i}" for i in range(8)]
        for user in users:
            atm.create_wallet(user)
            atm.fund_wallet(user, "100")

        initial_total = sum(atm.wallet_balance(u) for u in users)
        total_fees = Decimal("0")

        for _ in range(250):
            sender, receiver = random.sample(users, 2)
            sender_balance = atm.wallet_balance(sender)

            # Keep random amounts safely under sender's current ability to pay.
            if sender_balance <= Decimal("0.05000000"):
                continue

            amount = q8(Decimal(str(random.uniform(0.01, 5))))
            projected_fee = q8(amount * atm.network_fee_rate)
            total_debit = q8(amount + projected_fee)

            if total_debit > sender_balance:
                continue

            tx = atm.transfer_via_atm(sender, receiver, amount)
            self.assertEqual(tx.status, "confirmed")
            total_fees = q8(total_fees + tx.network_fee)

        final_total = sum(atm.wallet_balance(u) for u in users)

        # Fees are removed from circulating balances in this prototype.
        self.assertEqual(final_total, q8(initial_total - total_fees))
        self.assertEqual(len(atm.blockchain.chain), len([e for e in atm.audit_log if e["event"] == "atm_transfer"]))


if __name__ == "__main__":
    unittest.main()
