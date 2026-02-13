from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional
import hashlib
import uuid


DECIMAL_QUANT = Decimal("0.00000001")  # 8dp like BTC style assets


def q8(value: Decimal | str | float | int) -> Decimal:
    """Normalize a value to 8 decimal places."""
    return Decimal(str(value)).quantize(DECIMAL_QUANT, rounding=ROUND_DOWN)


@dataclass
class Wallet:
    owner_id: str
    currency: str = "USDC"
    balance: Decimal = field(default_factory=lambda: q8("0"))

    def credit(self, amount: Decimal) -> None:
        amount = q8(amount)
        if amount <= 0:
            raise ValueError("Credit amount must be positive.")
        self.balance = q8(self.balance + amount)

    def debit(self, amount: Decimal) -> None:
        amount = q8(amount)
        if amount <= 0:
            raise ValueError("Debit amount must be positive.")
        if self.balance < amount:
            raise ValueError("Insufficient wallet balance.")
        self.balance = q8(self.balance - amount)


@dataclass
class TransferTx:
    tx_id: str
    sender_wallet: str
    receiver_wallet: str
    amount: Decimal
    timestamp: datetime
    status: str
    network_fee: Decimal
    block_hash: str


class MockBlockchain:
    """A tiny in-memory blockchain ledger for demonstration/testing."""

    def __init__(self) -> None:
        self.chain: List[TransferTx] = []

    def submit_transfer(
        self,
        sender_wallet: str,
        receiver_wallet: str,
        amount: Decimal,
        network_fee: Decimal,
    ) -> TransferTx:
        amount = q8(amount)
        network_fee = q8(network_fee)
        now = datetime.now(timezone.utc)
        payload = f"{sender_wallet}|{receiver_wallet}|{amount}|{network_fee}|{now.isoformat()}|{uuid.uuid4()}"
        block_hash = hashlib.sha256(payload.encode()).hexdigest()
        tx = TransferTx(
            tx_id=str(uuid.uuid4()),
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=amount,
            timestamp=now,
            status="confirmed",
            network_fee=network_fee,
            block_hash=block_hash,
        )
        self.chain.append(tx)
        return tx

    def get_transaction(self, tx_id: str) -> Optional[TransferTx]:
        for tx in self.chain:
            if tx.tx_id == tx_id:
                return tx
        return None


class CryptoATMBackend:
    """
    Backend logic for a crypto-enabled ATM transfer service.

    - User balances are represented by wallets in crypto (default USDC).
    - Every transfer goes on-chain (simulated by MockBlockchain).
    - ATM records an internal audit log for compliance visibility.
    """

    def __init__(self, network_fee_rate: Decimal | str = Decimal("0.0025")) -> None:
        self.wallets: Dict[str, Wallet] = {}
        self.blockchain = MockBlockchain()
        self.network_fee_rate = q8(network_fee_rate)
        self.audit_log: List[dict] = []

    def create_wallet(self, owner_id: str, currency: str = "USDC") -> Wallet:
        if owner_id in self.wallets:
            raise ValueError(f"Wallet already exists for owner '{owner_id}'.")
        wallet = Wallet(owner_id=owner_id, currency=currency)
        self.wallets[owner_id] = wallet
        return wallet

    def fund_wallet(self, owner_id: str, amount: Decimal | str | float | int) -> Wallet:
        wallet = self._get_wallet(owner_id)
        wallet.credit(q8(amount))
        self.audit_log.append(
            {
                "event": "fund_wallet",
                "owner_id": owner_id,
                "amount": str(q8(amount)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return wallet

    def transfer_via_atm(
        self,
        sender_id: str,
        receiver_id: str,
        amount: Decimal | str | float | int,
    ) -> TransferTx:
        amount = q8(amount)
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        sender = self._get_wallet(sender_id)
        receiver = self._get_wallet(receiver_id)

        if sender.currency != receiver.currency:
            raise ValueError("Cross-currency transfers are not supported in this prototype.")

        network_fee = q8(amount * self.network_fee_rate)
        total_debit = q8(amount + network_fee)

        sender.debit(total_debit)
        receiver.credit(amount)

        tx = self.blockchain.submit_transfer(
            sender_wallet=sender.owner_id,
            receiver_wallet=receiver.owner_id,
            amount=amount,
            network_fee=network_fee,
        )

        self.audit_log.append(
            {
                "event": "atm_transfer",
                "tx_id": tx.tx_id,
                "sender": sender_id,
                "receiver": receiver_id,
                "amount": str(amount),
                "network_fee": str(network_fee),
                "total_debit": str(total_debit),
                "timestamp": tx.timestamp.isoformat(),
                "status": tx.status,
            }
        )

        return tx

    def wallet_balance(self, owner_id: str) -> Decimal:
        return self._get_wallet(owner_id).balance

    def _get_wallet(self, owner_id: str) -> Wallet:
        if owner_id not in self.wallets:
            raise ValueError(f"No wallet found for owner '{owner_id}'.")
        return self.wallets[owner_id]


def demo() -> None:
    atm = CryptoATMBackend(network_fee_rate="0.0010")  # 0.10%
    atm.create_wallet("alice")
    atm.create_wallet("bob")

    atm.fund_wallet("alice", "500")
    tx = atm.transfer_via_atm("alice", "bob", "125.55")

    print("Transfer complete")
    print(f"TX ID: {tx.tx_id}")
    print(f"Block Hash: {tx.block_hash}")
    print(f"Alice balance: {atm.wallet_balance('alice')} USDC")
    print(f"Bob balance: {atm.wallet_balance('bob')} USDC")


if __name__ == "__main__":
    demo()
