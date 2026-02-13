# Crypto ATM Money Transfer (Prototype)

This repository includes a lightweight Python prototype for a **crypto ATM transfer backend** where all transfers are processed as crypto transactions.

## What it does

- Creates user wallets (default currency: USDC).
- Funds wallets.
- Transfers value through the ATM backend:
  - Debits sender amount + network fee.
  - Credits receiver amount.
  - Records an on-chain-style transaction in a simulated blockchain ledger.
- Stores an audit log for transfer/funding events.

## Run demo

```bash
python3 crypto_atm.py
```

## Testing

### Standard test run

```bash
python3 -m unittest discover -s tests -v
```

### Advanced validation coverage included

The test suite now includes deeper checks beyond basic happy-path behavior:

- Duplicate wallet and cross-currency rejection behavior.
- Transaction lookup + audit-log consistency.
- Fee quantization/rounding validation to 8 decimal places.
- High-volume randomized transfer simulation with invariant checks:
  - every successful transfer is confirmed,
  - blockchain entries match audit transfer events,
  - total user balances decrease only by collected fees.

These tests are deterministic (`random.seed(7)`) to keep CI results stable.

## Notes

- This is a simulation/prototype, not production-grade custody infrastructure.
- No private keys, cryptographic signatures, AML/KYC checks, or real chain RPC integration are included.
