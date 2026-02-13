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

## Run tests

```bash
python3 -m unittest discover -s tests -v
```

## Notes

- This is a simulation/prototype, not production-grade custody infrastructure.
- No private keys, cryptographic signatures, AML/KYC checks, or real chain RPC integration are included.
