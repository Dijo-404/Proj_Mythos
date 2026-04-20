"""
Lendora AI - ZK Proof Generator (Circom/SnarkJS)
Replaces Midnight Network ZK proof generation
"""

import os
import json
import subprocess
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import snarkjs
    SNARKJS_AVAILABLE = True
except ImportError:
    SNARKJS_AVAILABLE = False
    print("[ZK] Warning: snarkjs not available. Install: npm install -g snarkjs")


@dataclass
class ZKProof:
    """ZK proof structure."""
    proof: List[int]  # 8 uint256 values: [a0, a1, b00, b01, b10, b11, c0, c1]
    publicSignals: List[int]  # 1 uint256 value: [isEligible]


@dataclass
class CreditCheckResult:
    """Result of credit check with ZK proof."""
    is_eligible: bool
    proof_hash: str
    proof: Optional[ZKProof] = None
    timestamp: Optional[str] = None


class ZKProofGenerator:
    """Generate ZK proofs for credit score verification."""
    
    def __init__(
        self,
        circuit_path: Optional[str] = None,
        proving_key_path: Optional[str] = None,
        wasm_path: Optional[str] = None
    ):
        """
        Initialize ZK proof generator.
        
        Args:
            circuit_path: Path to Circom circuit file
            proving_key_path: Path to proving key (.zkey file)
            wasm_path: Path to WASM file (generated from circuit)
        """
        # Default paths
        base_path = Path(__file__).parent.parent.parent / "contracts" / "core" / "zk" / "circuits"
        
        self.circuit_path = circuit_path or str(base_path / "credit_score.circom")
        self.proving_key_path = proving_key_path or os.getenv("ZK_PROVING_KEY_PATH")
        self.wasm_path = wasm_path or os.getenv("ZK_WASM_PATH")
        
        self._available = (
            SNARKJS_AVAILABLE and
            self.proving_key_path and
            Path(self.proving_key_path).exists() and
            self.wasm_path and
            Path(self.wasm_path).exists()
        )
        
        if not self._available:
            print("[ZK] Warning: ZK proof generation not fully configured")
            print("[ZK] Set ZK_PROVING_KEY_PATH and ZK_WASM_PATH environment variables")
    
    @property
    def available(self) -> bool:
        """Check if proof generator is available."""
        return self._available
    
    def generate_proof(
        self,
        credit_score: int,
        min_threshold: int = 700
    ) -> Optional[ZKProof]:
        """
        Generate ZK proof for credit score.
        
        Args:
            credit_score: Borrower's credit score (private)
            min_threshold: Minimum credit score threshold (default 700)
        
        Returns:
            ZK proof or None if generation fails
        """
        if not self.available:
            # Fallback: return mock proof
            return self._mock_proof(credit_score >= min_threshold)
        
        try:
            # Calculate isEligible
            is_eligible = 1 if credit_score > min_threshold else 0
            
            # Create input JSON for SnarkJS
            input_data = {
                "creditScore": credit_score,
                "isEligible": is_eligible
            }
            
            input_file = Path("/tmp/zk_input.json")
            input_file.write_text(json.dumps(input_data))
            
            # Generate witness
            witness_file = Path("/tmp/witness.wtns")
            witness_cmd = [
                "snarkjs", "wtns", "calculate",
                self.wasm_path,
                str(input_file),
                str(witness_file)
            ]
            
            result = subprocess.run(witness_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ZK] Error generating witness: {result.stderr}")
                return self._mock_proof(credit_score >= min_threshold)
            
            # Generate proof
            proof_file = Path("/tmp/proof.json")
            public_file = Path("/tmp/public.json")
            
            prove_cmd = [
                "snarkjs", "groth16", "prove",
                self.proving_key_path,
                str(witness_file),
                str(proof_file),
                str(public_file)
            ]
            
            result = subprocess.run(prove_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ZK] Error generating proof: {result.stderr}")
                return self._mock_proof(credit_score >= min_threshold)
            
            # Parse proof JSON
            proof_data = json.loads(proof_file.read_text())
            public_data = json.loads(public_file.read_text())
            
            # Convert proof to uint256 array format
            proof = self._format_proof(proof_data)
            public_signals = [int(public_data[0])]
            
            return ZKProof(proof=proof, publicSignals=public_signals)
            
        except Exception as e:
            print(f"[ZK] Error in proof generation: {e}")
            return self._mock_proof(credit_score >= min_threshold)
    
    def _format_proof(self, proof_data: Dict) -> List[int]:
        """
        Format SnarkJS proof to contract format.
        
        Args:
            proof_data: Proof data from SnarkJS
        
        Returns:
            Formatted proof as list of 8 uint256 values
        """
        # SnarkJS format: { pi_a: [a0, a1], pi_b: [[b00, b01], [b10, b11]], pi_c: [c0, c1] }
        # Contract format: [a0, a1, b00, b01, b10, b11, c0, c1]
        
        pi_a = proof_data["pi_a"][:2]
        pi_b = proof_data["pi_b"][0] + proof_data["pi_b"][1]
        pi_c = proof_data["pi_c"][:2]
        
        # Convert from string to int (handle big numbers)
        def to_int(val):
            if isinstance(val, str):
                # Remove leading "0x" if present
                val = val.replace("0x", "")
                return int(val, 16) if val.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f")) else int(val)
            return int(val)
        
        return [
            to_int(pi_a[0]),
            to_int(pi_a[1]),
            to_int(pi_b[0]),
            to_int(pi_b[1]),
            to_int(pi_b[2]),
            to_int(pi_b[3]),
            to_int(pi_c[0]),
            to_int(pi_c[1])
        ]
    
    def _mock_proof(self, is_eligible: bool) -> ZKProof:
        """
        Generate mock proof for testing.
        
        Args:
            is_eligible: Eligibility boolean
        
        Returns:
            Mock ZK proof
        """
        # Mock proof values (not cryptographically valid)
        proof = [0] * 8
        public_signals = [1 if is_eligible else 0]
        
        return ZKProof(proof=proof, publicSignals=public_signals)
    
    def verify_credit_score(
        self,
        borrower_address: str,
        credit_score: int,
        min_threshold: int = 700
    ) -> CreditCheckResult:
        """
        Generate ZK proof and return credit check result.
        
        Args:
            borrower_address: Borrower's Ethereum address
            credit_score: Credit score (private, never revealed)
            min_threshold: Minimum threshold (default 700)
        
        Returns:
            Credit check result with proof
        """
        from datetime import datetime
        import hashlib
        
        # Generate proof
        proof = self.generate_proof(credit_score, min_threshold)
        
        # Calculate eligibility
        is_eligible = credit_score >= min_threshold
        
        # Generate proof hash
        if proof:
            proof_data = json.dumps({
                "proof": proof.proof,
                "publicSignals": proof.publicSignals
            }, sort_keys=True)
            proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()
        else:
            proof_hash = f"zk_proof_{borrower_address[:10]}_{int(datetime.now().timestamp())}"
        
        return CreditCheckResult(
            is_eligible=is_eligible,
            proof_hash=proof_hash,
            proof=proof,
            timestamp=datetime.now().isoformat()
        )


# Global instance
_proof_generator: Optional[ZKProofGenerator] = None


def get_proof_generator() -> ZKProofGenerator:
    """Get or create global proof generator instance."""
    global _proof_generator
    if _proof_generator is None:
        _proof_generator = ZKProofGenerator()
    return _proof_generator

