// ============================================================================
// Lendora AI - Credit Score ZK Circuit (Circom)
// ============================================================================
// Privacy-preserving credit score verification circuit
// Equivalent to Midnight Network's credit_score.compact
//
// Circuit Logic:
//   - Private input: credit_score (uint)
//   - Public output: is_eligible (boolean)
//   - Constraint: is_eligible = (credit_score > MIN_CREDIT_SCORE)
//
// This circuit proves that a borrower's credit score exceeds a threshold
// without revealing the actual score value.
// ============================================================================

pragma circom 2.0.0;

// Include Circom standard templates
include "../node_modules/circomlib/circuits/comparators.circom";

// ============================================================================
// Circuit Template
// ============================================================================

template CreditScoreCheck() {
    // Private input: borrower's credit score (not revealed)
    signal private input creditScore;
    
    // Public output: eligibility boolean (revealed)
    signal output isEligible;
    
    // Minimum credit score threshold (hardcoded in circuit)
    component gt = GreaterThan(32); // 32-bit comparison (scores 0-850 fit in 10 bits)
    
    // Constraint: creditScore > 700
    // We need to compare: creditScore > 700
    // GreaterThan template expects: in[0] > in[1]
    gt.in[0] <== creditScore;
    gt.in[1] <== 700; // MIN_CREDIT_SCORE
    
    // Output: is eligible if credit score exceeds threshold
    isEligible <== gt.out;
}

// ============================================================================
// Main Component
// ============================================================================

component main = CreditScoreCheck();

// ============================================================================
// Compilation Instructions
// ============================================================================
//
// 1. Install dependencies:
//    npm install circom circomlib snarkjs
//
// 2. Compile circuit:
//    circom credit_score.circom --r1cs --wasm --sym
//
// 3. Generate trusted setup (powers of tau):
//    snarkjs powersoftau new bn128 14 pot14_0000.ptau -v
//    snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau --name="First contribution" -v
//    snarkjs powersoftau prepare phase2 pot14_0001.ptau pot14_final.ptau -v
//
// 4. Generate proving key:
//    snarkjs groth16 setup credit_score.r1cs pot14_final.ptau credit_score_0000.zkey
//    snarkjs zkey contribute credit_score_0000.zkey credit_score_0001.zkey --name="1st Contributor" -v
//    snarkjs zkey export verificationkey credit_score_0001.zkey verification_key.json
//
// 5. Generate proof (off-chain, e.g., in Node.js):
//    snarkjs groth16 prove credit_score_0001.zkey witness.wtns proof.json public.json
//
// 6. Generate Solidity verifier:
//    snarkjs zkey export solidityverifier credit_score_0001.zkey verifier.sol
//
// 7. Deploy verifier.sol to Ethereum L2
//
// ============================================================================

