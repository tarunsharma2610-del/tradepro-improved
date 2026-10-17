# Tradepro Improved

A separate improvement track for Tradepro. The original `tradepro` repository and its `main` branch remain untouched.

## Safety-first development plan

- Preserve existing functionality while fixing verified defects.
- Keep paper trading as the default mode.
- Keep live trading disabled until broker execution, order reconciliation, duplicate-order prevention, risk limits, and an emergency kill switch are tested.
- Never commit API tokens, OAuth secrets, passwords, or other credentials.
- Validate changes with automated tests and build checks before enabling any live execution.

## Current status

This repository is being prepared as the isolated improved version. The initial code import and validation are still pending.
