# Lendora AI - Ethereum Smart Contracts

## Overview

This directory contains the Ethereum-native smart contracts for Lendora AI, migrated from the Cardano Aiken contracts.

## Contract Structure

```
contracts/
├── core/
│   ├── interfaces/
│   │   ├── IERC20.sol              # ERC20 token interface
│   │   └── IChainlinkOracle.sol    # Chainlink price feed interface
│   ├── LoanManager.sol             # Main loan orchestration (replaces Aiken validator)
│   ├── CollateralVault.sol         # Collateral management
│   ├── InterestRateModel.sol       # Dynamic interest rate calculations
│   ├── LiquidationEngine.sol       # Automated liquidation system
│   └── zk/
│       ├── CreditScoreVerifier.sol # ZK proof verifier (placeholder)
│       └── circuits/
│           └── credit_score.circom # ZK circuit definition
├── scripts/
│   └── deploy.js                   # Deployment script
├── test/
│   └── LoanManager.test.js         # Contract tests
├── hardhat.config.js               # Hardhat configuration
└── package.json                    # Dependencies
```

## Key Contracts

### LoanManager.sol
Main loan orchestration contract, equivalent to the Aiken settlement validator. Handles:
- Loan creation (with ZK proof verification)
- Loan repayment
- Integration with CollateralVault and LiquidationEngine

### CollateralVault.sol
Manages collateral deposits and withdrawals:
- Supports ETH and ERC20 tokens as collateral
- Integrates with Chainlink oracles for price feeds
- Calculates collateral ratios

### InterestRateModel.sol
Dynamic interest rate calculation based on:
- Collateral ratio
- Credit eligibility (from ZK proof)
- Base rate and risk premiums

### LiquidationEngine.sol
Automated liquidation system:
- Monitors collateral ratios
- Liquidates undercollateralized loans
- Provides liquidation bonus to liquidators

### CreditScoreVerifier.sol
ZK proof verifier for credit scores:
- Placeholder implementation (to be replaced with Circom-generated verifier)
- Prevents proof replay attacks
- Verifies credit eligibility without revealing score

## Setup

### Install Dependencies

```bash
cd contracts
npm install
```

### Compile Contracts

```bash
npm run compile
```

### Run Tests

```bash
npm run test
```

## Deployment

### Prerequisites

1. Set environment variables:
```bash
export PRIVATE_KEY=your_private_key
export ARBITRUM_RPC_URL=https://goerli-rollup.arbitrum.io/rpc
```

2. Fund your deployment account with ETH on Arbitrum testnet

### Deploy to Testnet

```bash
npm run deploy:testnet
```

### Deploy to Mainnet

```bash
npm run deploy:mainnet
```

## ZK Circuit Compilation

### Generate Verifier Contract

1. Compile Circom circuit:
```bash
cd core/zk/circuits
circom credit_score.circom --r1cs --wasm --sym
```

2. Generate trusted setup:
```bash
snarkjs powersoftau new bn128 14 pot14_0000.ptau -v
snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau --name="First contribution" -v
snarkjs powersoftau prepare phase2 pot14_0001.ptau pot14_final.ptau -v
```

3. Generate proving key:
```bash
snarkjs groth16 setup credit_score.r1cs pot14_final.ptau credit_score_0000.zkey
snarkjs zkey contribute credit_score_0000.zkey credit_score_0001.zkey --name="1st Contributor" -v
snarkjs zkey export verificationkey credit_score_0001.zkey verification_key.json
```

4. Generate Solidity verifier:
```bash
snarkjs zkey export solidityverifier credit_score_0001.zkey CreditScoreVerifier.sol
```

5. Replace the placeholder `CreditScoreVerifier.sol` with the generated file

## Security Considerations

- All contracts use OpenZeppelin's security patterns (ReentrancyGuard, Ownable)
- Access control via modifiers and role-based permissions
- ZK proof verification prevents replay attacks
- Oracle price freshness checks (1 hour staleness limit)
- Gas optimizations: packed structs, event-based logging

## Gas Optimization

- Struct packing for efficient storage
- Events for historical data (instead of storage)
- Batch operations where possible
- L2-specific optimizations (Arbitrum/Optimism)

## Testing

Run unit tests:
```bash
npx hardhat test
```

Run with coverage:
```bash
npx hardhat coverage
```

## Migration from Cardano

Key differences:
- **eUTxO → Account-based**: State stored in contract storage vs UTxOs
- **Datum/Redeemer → Function parameters**: Settlement logic in function calls
- **Dual signatures → Single transaction**: Both parties sign same transaction
- **Hydra → L2**: Off-chain negotiation, on-chain settlement on L2

## References

- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Hardhat Documentation](https://hardhat.org/docs)
- [Circom Documentation](https://docs.circom.io/)
- [Arbitrum Documentation](https://docs.arbitrum.io/)

