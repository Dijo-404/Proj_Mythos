"""
Mythos â€” Solana Attestation Service (SAS) Client
=================================================
Issues and verifies on-chain credit score attestations using the
Solana Attestation Service (SAS). Replaces ZK proofs with native
Solana attestations â€” lightweight, composable, and hackathon-highlighted.

SAS Attestation Schema:
  - Schema: "mythos-credit-v1"
  - Fields: credit_tier, income_verified, max_loan_usdc, timestamp
  - Subject: borrower's Solana public key
  - Expires: 30 days after issuance

Attestation Tiers:
  AAA: score 800+  â†’ 7% APR, 150% LTV
  AA:  score 750+  â†’ 8% APR, 140% LTV
  A:   score 700+  â†’ 9.5% APR, 130% LTV
  B:   score 650+  â†’ 11% APR, 120% LTV
  C:   score 600+  â†’ 13% APR, 110% LTV
"""

import os
import json
import hashlib
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CreditAttestation:
    """On-chain credit attestation record."""
    subject_pubkey: str          # Borrower's Solana public key
    attestation_id: str          # Unique attestation identifier (PDA seed)
    credit_tier: str             # AAA, AA, A, B, C
    credit_score: int            # 300-850 range
    income_verified: bool        # Income verification status
    max_loan_usdc: int           # Maximum loan amount in USDC cents
    interest_rate_bps: int       # Base interest rate in basis points
    ltv_bps: int                 # Loan-to-value in basis points
    schema: str = "mythos-credit-v1"
    issued_at: str = ""
    expires_at: str = ""
    tx_signature: Optional[str] = None   # Solana tx that created this attestation
    on_chain: bool = False

    def __post_init__(self):
        if not self.issued_at:
            self.issued_at = datetime.utcnow().isoformat()
        if not self.expires_at:
            expires = datetime.utcnow() + timedelta(days=30)
            self.expires_at = expires.isoformat()
        if not self.attestation_id:
            # Derive PDA-like ID from subject + schema + issuer
            seed = f"{self.subject_pubkey}:{self.schema}:{self.issued_at}"
            self.attestation_id = f"att_{hashlib.sha256(seed.encode()).hexdigest()[:16]}"

    @property
    def is_expired(self) -> bool:
        return datetime.fromisoformat(self.expires_at) < datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Credit tier configuration
CREDIT_TIERS = {
    "AAA": {"min_score": 800, "rate_bps": 700,  "ltv_bps": 15000, "max_usdc": 100000_00},
    "AA":  {"min_score": 750, "rate_bps": 800,  "ltv_bps": 14000, "max_usdc": 75000_00},
    "A":   {"min_score": 700, "rate_bps": 950,  "ltv_bps": 13000, "max_usdc": 50000_00},
    "B":   {"min_score": 650, "rate_bps": 1100, "ltv_bps": 12000, "max_usdc": 25000_00},
    "C":   {"min_score": 600, "rate_bps": 1300, "ltv_bps": 11000, "max_usdc": 10000_00},
}

# In-memory attestation store (simulates on-chain PDAs)
_attestations: Dict[str, CreditAttestation] = {}


# ============================================================================
# SAS Client
# ============================================================================

class SASClient:
    """
    Client for the Solana Attestation Service.
    
    In demo mode: creates attestations locally and stores them in memory.
    In production: submits anchor instructions to the SAS program on Solana.
    """

    def __init__(self):
        self.network = os.getenv("SOLANA_NETWORK", "devnet")
        self.helius_url = (
            f"https://{self.network}.helius-rpc.com/?api-key="
            f"{os.getenv('HELIUS_API_KEY', 'demo')}"
        )
        self.demo_mode = os.getenv("SAS_DEMO_MODE", "true").lower() == "true"
        self.schema_id = "mythos-credit-v1"
        
        print(f"[SAS] Client initialized (demo={self.demo_mode}, network={self.network})")

    def _score_to_tier(self, score: int) -> str:
        """Convert credit score to tier label."""
        for tier, config in CREDIT_TIERS.items():
            if score >= config["min_score"]:
                return tier
        return "INELIGIBLE"

    def _compute_interest_rate(self, score: int, term_months: int) -> float:
        """
        Compute personalized interest rate from credit score.
        Better score + shorter term = lower rate.
        """
        tier = self._score_to_tier(score)
        if tier == "INELIGIBLE":
            return 15.0

        base_bps = CREDIT_TIERS[tier]["rate_bps"]
        
        # Term adjustment: shorter term gets 0.25% discount per 6 months under 24
        term_adj = max(0, (24 - term_months) // 6) * 25  # 25 bps per bracket
        
        final_bps = max(base_bps - term_adj, 500)  # Floor at 5%
        return final_bps / 100.0

    async def issue_attestation(
        self,
        subject_pubkey: str,
        credit_score: int,
        income_verified: bool = True
    ) -> CreditAttestation:
        """
        Issue a credit attestation for a borrower.
        
        Args:
            subject_pubkey: Borrower's Solana public key
            credit_score: Credit score (300-850)
            income_verified: Whether off-chain income has been verified
            
        Returns: CreditAttestation with on-chain signature (demo or real)
        """
        print(f"\n[SAS] ðŸ“‹ Issuing credit attestation...")
        print(f"[SAS]    Borrower: {subject_pubkey[:20]}...")
        print(f"[SAS]    Score: {credit_score} (private, not stored on-chain)")

        tier = self._score_to_tier(credit_score)
        
        if tier == "INELIGIBLE":
            print(f"[SAS] âŒ Score too low ({credit_score} < 600). No attestation issued.")
            raise ValueError(f"Credit score {credit_score} does not qualify for any tier (minimum 600)")

        tier_config = CREDIT_TIERS[tier]

        attestation = CreditAttestation(
            subject_pubkey=subject_pubkey,
            attestation_id="",  # Generated in __post_init__
            credit_tier=tier,
            credit_score=credit_score,  # Note: in real SAS this stays private
            income_verified=income_verified,
            max_loan_usdc=tier_config["max_usdc"],
            interest_rate_bps=tier_config["rate_bps"],
            ltv_bps=tier_config["ltv_bps"],
        )

        if self.demo_mode:
            # Simulate the on-chain SAS instruction
            await asyncio.sleep(0.5)  # Simulate network latency
            attestation.tx_signature = f"SAS_TX_{attestation.attestation_id[:20]}"
            attestation.on_chain = True

            _attestations[subject_pubkey] = attestation

            print(f"[SAS] âœ… Attestation issued!")
            print(f"[SAS]    Tier: {tier} | Rate: {tier_config['rate_bps']/100}% APR | LTV: {tier_config['ltv_bps']/100}%")
            print(f"[SAS]    Attestation ID: {attestation.attestation_id}")
            print(f"[SAS]    Expires: {attestation.expires_at[:10]}")
            return attestation
        else:
            # Real SAS instruction (anchor call)
            return await self._submit_sas_instruction(attestation)

    async def verify_attestation(
        self,
        subject_pubkey: str
    ) -> Optional[CreditAttestation]:
        """
        Verify an existing credit attestation for a borrower.
        
        Args:
            subject_pubkey: Borrower's Solana public key
            
        Returns: CreditAttestation if valid, None if missing/expired
        """
        print(f"\n[SAS] ðŸ” Verifying attestation for {subject_pubkey[:20]}...")

        attestation = _attestations.get(subject_pubkey)

        if not attestation:
            print(f"[SAS] âš ï¸  No attestation found for this wallet")
            return None

        if attestation.is_expired:
            print(f"[SAS] âš ï¸  Attestation expired on {attestation.expires_at[:10]}")
            del _attestations[subject_pubkey]
            return None

        print(f"[SAS] âœ… Valid attestation found: Tier {attestation.credit_tier}")
        return attestation

    async def get_loan_terms(
        self,
        subject_pubkey: str,
        requested_amount_usdc: float,
        term_months: int
    ) -> Dict[str, Any]:
        """
        Get loan terms based on attestation.
        Used by Luna (lender agent) to price the loan offer.
        
        Returns: dict with rate, max_amount, ltv, tier
        """
        attestation = await self.verify_attestation(subject_pubkey)

        if not attestation:
            return {
                "eligible": False,
                "reason": "No valid credit attestation. Please complete credit verification first.",
            }

        max_loan = attestation.max_loan_usdc / 100  # Convert cents to USDC
        
        if requested_amount_usdc > max_loan:
            return {
                "eligible": False,
                "reason": f"Requested amount ${requested_amount_usdc:,.2f} exceeds maximum ${max_loan:,.2f} for tier {attestation.credit_tier}",
                "suggestion": f"Apply for up to ${max_loan:,.2f} USDC",
            }

        # Compute personalized rate
        rate = self._compute_interest_rate(attestation.credit_score, term_months)

        return {
            "eligible": True,
            "tier": attestation.credit_tier,
            "interest_rate": rate,
            "interest_rate_bps": attestation.interest_rate_bps,
            "ltv_percent": attestation.ltv_bps / 100,
            "max_loan_usdc": max_loan,
            "requested_amount_usdc": requested_amount_usdc,
            "monthly_payment": self._compute_monthly_payment(requested_amount_usdc, rate, term_months),
            "attestation_id": attestation.attestation_id,
            "attestation_expires": attestation.expires_at[:10],
        }

    def _compute_monthly_payment(self, principal: float, annual_rate: float, months: int) -> float:
        """Compute monthly payment using standard amortization formula."""
        if annual_rate == 0:
            return principal / months
        monthly_rate = (annual_rate / 100) / 12
        payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        return round(payment, 2)

    async def _submit_sas_instruction(self, attestation: CreditAttestation) -> CreditAttestation:
        """
        Submit real SAS attestation instruction to Solana.
        This calls the actual SAS program to create an on-chain attestation PDA.
        """
        # In a real implementation, this would:
        # 1. Derive the attestation PDA: [b"attestation", schema_id, subject_pubkey]
        # 2. Build an anchor instruction to the SAS program
        # 3. Sign with the issuer keypair
        # 4. Submit to Solana
        
        # For now, mark as pending and return
        attestation.tx_signature = "SAS_TX_PENDING_ANCHOR_INTEGRATION"
        attestation.on_chain = False
        _attestations[attestation.subject_pubkey] = attestation
        
        print("[SAS] â„¹ï¸  Real SAS instruction submission not yet implemented")
        print("[SAS]     Attestation stored locally as fallback")
        return attestation

    def list_all_attestations(self) -> list:
        """List all active attestations (for dashboard display)."""
        return [
            {
                "subject": att.subject_pubkey[:8] + "..." + att.subject_pubkey[-4:],
                "tier": att.credit_tier,
                "rate": att.interest_rate_bps / 100,
                "expires": att.expires_at[:10],
                "on_chain": att.on_chain
            }
            for att in _attestations.values()
            if not att.is_expired
        ]


# Global SAS client instance
sas_client = SASClient()


# ============================================================================
# Helper Functions
# ============================================================================

async def get_or_create_attestation(
    pubkey: str,
    credit_score: int = 720,
    income_verified: bool = True
) -> CreditAttestation:
    """
    Get existing attestation or create new one.
    Convenience function for the demo flow.
    """
    existing = await sas_client.verify_attestation(pubkey)
    if existing:
        return existing
    return await sas_client.issue_attestation(pubkey, credit_score, income_verified)


def mock_credit_score_from_history(wallet_address: str) -> int:
    """
    Deterministic mock credit score based on wallet address.
    For demo purposes â€” maps wallet to a repeatable credit score.
    """
    score_seed = int(hashlib.sha256(wallet_address.encode()).hexdigest()[:4], 16)
    # Map to 600-820 range
    return 600 + (score_seed % 221)

