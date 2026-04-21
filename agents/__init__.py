"""
Mythos â€” Agents Module
AI-Native Agentic Lending on Solana

Architecture:
    User Request â†’ Lenny (Borrower Agent)
                    |
              [reads SAS]  â† Solana Attestation Service (on-chain credit)
                    |
              [pays x402]  â† HTTP 402 micropayment to Luna
                    |
              [negotiates] â† Luna (Lender Agent) â€” AI rate negotiation
                    |
              [signs Anchor tx] â†’ Solana Devnet
                    |
                Loan Disbursed! ðŸŽ‰

Agents:
- solana_borrower_agent (Lenny): Reads SAS, pays x402, negotiates, settles on Solana
- solana_lender_agent  (Luna):  Prices risk, evaluates counter-offers, confirms loan
"""

# Legacy non-Solana agents have been moved to archive/legacy/
# Active Solana agents live at the module level
try:
    from .solana_borrower_agent import (
        run_solana_borrower_workflow,
        create_solana_borrower_agent,
        SolanaClient,
        SolanaAttestation,
        LoanOffer,
        SolanaLoanResult,
    )
    _SOLANA_AGENTS_AVAILABLE = True
except ImportError as e:
    _SOLANA_AGENTS_AVAILABLE = False
    import warnings
    warnings.warn(f"[Mythos] Solana agents not loaded: {e}")

__all__ = [
    # Borrower Agent â€” Lenny
    "run_solana_borrower_workflow",
    "create_solana_borrower_agent",
    "SolanaClient",
    "SolanaAttestation",
    "LoanOffer",
    "SolanaLoanResult",
]

