# Quick Start: Ethereum Migration

## Overview

This guide helps you quickly understand and use the Ethereum-native Lendora AI system.

## Prerequisites

1. **Node.js 18+** and **npm**
2. **Python 3.10+**
3. **MetaMask** browser extension
4. **Arbitrum Testnet** configured in MetaMask

## Setup

### 1. Install Contract Dependencies

```bash
cd contracts
npm install
```

### 2. Compile Contracts

```bash
npm run compile
```

### 3. Deploy to Arbitrum Testnet

```bash
# Set environment variables
export PRIVATE_KEY=your_private_key
export ETH_RPC_URL=https://goerli-rollup.arbitrum.io/rpc

# Deploy
npm run deploy:testnet
```

This will deploy all contracts in the correct order:
1. InterestRateModel
2. CollateralVault
3. LiquidationEngine
4. CreditScoreVerifier
5. LoanManager

Save the deployed contract addresses from the output.

### 4. Setup Backend

```bash
# Install Python dependencies
pip install web3 eth-account

# Set environment variables
export ETH_RPC_URL=https://goerli-rollup.arbitrum.io/rpc
export ETH_CHAIN_ID=421613
export LOAN_MANAGER_ADDRESS=<from deployment>
export COLLATERAL_VAULT_ADDRESS=<from deployment>
```

### 5. Setup ZK Proof Generation (Optional)

```bash
# Install SnarkJS globally
npm install -g snarkjs

# Compile Circom circuit
cd contracts/core/zk/circuits
circom credit_score.circom --r1cs --wasm --sym

# Generate trusted setup (development only)
snarkjs powersoftau new bn128 14 pot14_0000.ptau -v
# ... follow SnarkJS setup guide

# Generate proving key
snarkjs groth16 setup credit_score.r1cs pot14_final.ptau credit_score_0000.zkey

# Export verifier
snarkjs zkey export solidityverifier credit_score_0000.zkey CreditScoreVerifier.sol

# Set environment variables
export ZK_PROVING_KEY_PATH=./credit_score_0000.zkey
export ZK_WASM_PATH=./credit_score.wasm
```

## Usage

### Creating a Loan

```python
from backend.ethereum.tx_builder import EthereumTxBuilder, LoanSettlementParams
from backend.zk.proof_generator import get_proof_generator

# 1. Generate ZK proof for credit score
zk_client = get_proof_generator()
credit_result = zk_client.verify_credit_score(
    borrower_address="0x...",
    credit_score=750  # Private - never revealed!
)

# 2. Build transaction
tx_builder = EthereumTxBuilder()
params = LoanSettlementParams(
    borrower_address="0x...",
    lender_address="0x...",
    principal=1000 * 10**6,  # 1000 USDC (6 decimals)
    interest_amount=50 * 10**6,
    loan_token="0x...",  # USDC address
    collateral_token="0x0",  # ETH
    collateral_amount=1.5 * 10**18,  # 1.5 ETH
    interest_rate=500,  # 5% (basis points)
    term_months=12,
    zk_proof=credit_result.proof.proof,
    public_signals=credit_result.proof.publicSignals
)

tx_data = tx_builder.build_create_loan_tx(
    loan_manager_address="0x...",
    params=params
)

# 3. Sign and send (frontend does this via MetaMask)
```

### Checking Loan Status

```python
from backend.ethereum.contract_client import get_contract_client
import json

client = get_contract_client()

# Load contract ABI
with open("contracts/artifacts/LoanManager.sol/LoanManager.json") as f:
    abi = json.load(f)["abi"]

loan = client.get_loan(
    loan_manager_address="0x...",
    loan_id=0,
    abi=abi
)

print(f"Borrower: {loan['borrower']}")
print(f"Principal: {loan['principal']}")
print(f"Status: {loan['status']}")
```

### Repaying a Loan

```python
# Build repayment transaction
tx_data = tx_builder.build_repay_loan_tx(
    loan_manager_address="0x...",
    loan_id=0,
    loan_token="0x...",  # USDC
    total_repayment=1050 * 10**6  # Principal + interest
)

# Frontend signs and sends via MetaMask
```

## Frontend Integration

### Connect MetaMask

```typescript
// Check if MetaMask is installed
if (typeof window.ethereum !== 'undefined') {
  // Request account access
  const accounts = await window.ethereum.request({
    method: 'eth_requestAccounts'
  });
  
  const address = accounts[0];
  console.log('Connected:', address);
}
```

### Sign Transaction

```typescript
import { ethers } from 'ethers';

const provider = new ethers.BrowserProvider(window.ethereum);
const signer = await provider.getSigner();

const loanManager = new ethers.Contract(
  LOAN_MANAGER_ADDRESS,
  LOAN_MANAGER_ABI,
  signer
);

// Create loan
const tx = await loanManager.createLoan(
  lenderAddress,
  principal,
  interestRate,
  termMonths,
  collateralToken,
  collateralAmount,
  loanToken,
  zkProof,
  publicSignals,
  { value: collateralAmount } // If ETH collateral
);

await tx.wait();
```

## Contract Addresses (Testnet)

After deployment, you'll receive addresses like:

```
InterestRateModel:  0x1234...
CollateralVault:    0x5678...
LiquidationEngine:  0x9abc...
CreditScoreVerifier: 0xdef0...
LoanManager:        0x2468...
```

Save these in your environment variables and frontend configuration.

## Testing

### Unit Tests

```bash
cd contracts
npx hardhat test
```

### Integration Test

```python
# Test complete workflow
python test_integration_ethereum.py
```

## Troubleshooting

### "Web3 not available"
- Install: `pip install web3 eth-account`
- Check RPC URL is accessible

### "ZK proof generation failed"
- Ensure SnarkJS is installed: `npm install -g snarkjs`
- Check proving key and WASM paths are correct
- For development, mock proofs will be used

### "Transaction failed"
- Check you have enough ETH for gas
- Verify contract addresses are correct
- Check token approvals (for ERC20)

### "Price feed not available"
- Set Chainlink price feed address in CollateralVault
- For testnet, use testnet feeds
- For mainnet, use mainnet feeds

## Next Steps

1. **Read Full Migration Guide**: [ETHEREUM_MIGRATION.md](./ETHEREUM_MIGRATION.md)
2. **Understand Architecture**: [ARCHITECTURE_COMPARISON.md](./ARCHITECTURE_COMPARISON.md)
3. **Review Contracts**: [contracts/README.md](../contracts/README.md)
4. **Check Migration Status**: [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md)

## Support

- **Contract Issues**: Check Hardhat docs and OpenZeppelin contracts
- **ZK Circuit Issues**: See Circom documentation
- **Oracle Issues**: Review Chainlink documentation
- **Frontend Issues**: See ethers.js or web3.js docs

