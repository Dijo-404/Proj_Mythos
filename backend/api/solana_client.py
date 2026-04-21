"""
Mythos — Solana On-Chain Client
================================
Submits real transactions to Solana Devnet using solders + solana-py.
Requires BACKEND_SIGNER_KEYPAIR (base58 private key) env var.

Capabilities:
  - generate_keypair()           → print pubkey for airdrop
  - initialize_loan_tx()         → build + send initialize_loan instruction
  - verify_usdc_transfer()       → confirm a USDC transfer tx on-chain

Usage (demo mode enabled by SOLANA_DEMO_MODE=true):
  - All methods return realistic simulated results when demo mode is on.
  - Set SOLANA_DEMO_MODE=false + BACKEND_SIGNER_KEYPAIR for real devnet txs.
"""

import os
import hashlib
import struct
import base58
import base64
import json
import asyncio
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.transaction import Transaction
    from solders.message import Message
    from solders.instruction import Instruction, AccountMeta
    from solders.hash import Hash
    from solders.system_program import ID as SYS_PROGRAM_ID
    SOLDERS_AVAILABLE = True
except ImportError:
    SOLDERS_AVAILABLE = False
    print("[SolanaClient] solders not installed — demo mode only")


# ============================================================================
# Config
# ============================================================================

MYTHOS_PROGRAM_ID = os.getenv(
    "MYTHOS_PROGRAM_ID", "FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM"
)
SOLANA_NETWORK    = os.getenv("SOLANA_NETWORK", "devnet")
HELIUS_API_KEY    = os.getenv("HELIUS_API_KEY", "demo")
DEMO_MODE         = os.getenv("SOLANA_DEMO_MODE", "true").lower() == "true"

RPC_URL = (
    f"https://{SOLANA_NETWORK}.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    if HELIUS_API_KEY != "demo"
    else f"https://api.{SOLANA_NETWORK}.solana.com"
)

# Anchor discriminator for initialize_loan = sha256("global:initialize_loan")[:8]
INITIALIZE_LOAN_DISCRIMINATOR: bytes = hashlib.sha256(b"global:initialize_loan").digest()[:8]


# ============================================================================
# Keypair Management
# ============================================================================

def load_signer_keypair() -> Optional["Keypair"]:
    """
    Load backend signer keypair from BACKEND_SIGNER_KEYPAIR env var.
    Value is a base58-encoded 64-byte secret key (as output by `solana-keygen new`).
    Returns None if not set or solders unavailable.
    """
    if not SOLDERS_AVAILABLE:
        return None
    raw = os.getenv("BACKEND_SIGNER_KEYPAIR", "")
    if not raw:
        return None
    try:
        secret_bytes = base58.b58decode(raw)
        return Keypair.from_bytes(secret_bytes)
    except Exception as e:
        print(f"[SolanaClient] Failed to load keypair: {e}")
        return None


def generate_and_print_keypair() -> Dict[str, str]:
    """
    Generate a fresh devnet keypair and print funding instructions.
    Call once, save the secret key in BACKEND_SIGNER_KEYPAIR env var.
    """
    if not SOLDERS_AVAILABLE:
        return {"error": "solders not installed"}

    kp = Keypair()
    pubkey = str(kp.pubkey())
    secret_b58 = base58.b58encode(bytes(kp)).decode()

    print(f"\n[SolanaClient] 🔑 Generated new devnet keypair")
    print(f"  Pubkey  : {pubkey}")
    print(f"  Secret  : {secret_b58}")
    print(f"\n  ➜ Fund this wallet:")
    print(f"    solana airdrop 1 {pubkey} --url devnet")
    print(f"\n  ➜ Add to .env:")
    print(f"    BACKEND_SIGNER_KEYPAIR={secret_b58}")

    return {"pubkey": pubkey, "secret_b58": secret_b58}


# ============================================================================
# RPC Helpers
# ============================================================================

async def _rpc(method: str, params: list) -> Any:
    """Raw JSON-RPC call to Solana."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(RPC_URL, json={
            "jsonrpc": "2.0", "id": 1, "method": method, "params": params
        })
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC error: {data['error']}")
        return data.get("result")


async def get_latest_blockhash() -> str:
    """Get the latest blockhash from Solana."""
    result = await _rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
    return result["value"]["blockhash"]


async def send_transaction(tx_b64: str) -> str:
    """Send a base64-encoded signed transaction. Returns signature."""
    result = await _rpc("sendTransaction", [
        tx_b64,
        {"encoding": "base64", "skipPreflight": False, "preflightCommitment": "confirmed"}
    ])
    return result  # transaction signature


async def confirm_transaction(sig: str, max_retries: int = 10) -> bool:
    """Poll until transaction is confirmed or max retries exceeded."""
    for _ in range(max_retries):
        try:
            result = await _rpc("getSignatureStatuses", [[sig]])
            statuses = result.get("value", [])
            if statuses and statuses[0]:
                confirmation = statuses[0].get("confirmationStatus")
                err = statuses[0].get("err")
                if err:
                    print(f"[SolanaClient] ❌ TX failed: {err}")
                    return False
                if confirmation in ("confirmed", "finalized"):
                    return True
        except Exception:
            pass
        await asyncio.sleep(1)
    return False


# ============================================================================
# Instruction Builder: initialize_loan
# ============================================================================

def build_initialize_loan_data(
    amount_usdc: int,
    initial_rate_bps: int,
    term_months: int,
    attestation_id: bytes,
) -> bytes:
    """
    Serialize initialize_loan instruction data.
    Layout: discriminator(8) + amount_usdc(u64 LE) + initial_rate_bps(u16 LE)
            + term_months(u8) + attestation_id([u8;32])
    """
    assert len(attestation_id) == 32, "attestation_id must be 32 bytes"
    return (
        INITIALIZE_LOAN_DISCRIMINATOR
        + struct.pack("<Q", amount_usdc)       # u64 little-endian
        + struct.pack("<H", initial_rate_bps)  # u16 little-endian
        + struct.pack("<B", term_months)       # u8
        + attestation_id                       # [u8; 32]
    )


# ============================================================================
# Main: initialize_loan_tx
# ============================================================================

async def initialize_loan_tx(
    borrower_pubkey: str,
    amount_usdc_ui: float,     # human-readable USDC (e.g. 1000.0)
    initial_rate_bps: int,     # e.g. 950
    term_months: int,          # e.g. 12
    attestation_id_str: str,   # e.g. "att_abc123..." (padded to 32 bytes)
) -> Dict[str, Any]:
    """
    Build and send an initialize_loan transaction to Solana Devnet.

    In DEMO_MODE: returns a simulated signature immediately.
    In REAL_MODE: requires BACKEND_SIGNER_KEYPAIR and HELIUS_API_KEY.

    Returns dict with:
      signature, slot, explorer_url, demo, program_id
    """
    amount_usdc_lamports = int(amount_usdc_ui * 1_000_000)  # 6 decimals

    # Pad/truncate attestation_id to 32 bytes
    att_bytes = attestation_id_str.encode()[:32].ljust(32, b'\x00')

    if DEMO_MODE or not SOLDERS_AVAILABLE:
        sim_sig = f"SIM_INIT_LOAN_{int(datetime.utcnow().timestamp())}"
        print(f"[SolanaClient] 🔵 Demo mode — simulated initialize_loan: {sim_sig}")
        return {
            "signature": sim_sig,
            "slot": 350_000_000,
            "explorer_url": f"https://explorer.solana.com/tx/{sim_sig}?cluster=devnet",
            "demo": True,
            "program_id": MYTHOS_PROGRAM_ID,
            "amount_usdc": amount_usdc_ui,
            "rate_bps": initial_rate_bps,
            "term_months": term_months,
            "note": "Set SOLANA_DEMO_MODE=false + BACKEND_SIGNER_KEYPAIR for real devnet tx",
        }

    signer = load_signer_keypair()
    if not signer:
        raise RuntimeError(
            "BACKEND_SIGNER_KEYPAIR not set. "
            "Run /api/solana/generate-keypair to create one, then fund it with airdrop."
        )

    program_id = Pubkey.from_string(MYTHOS_PROGRAM_ID)
    borrower   = Pubkey.from_string(borrower_pubkey)
    payer      = signer.pubkey()

    # Derive loan PDA: seeds = [b"loan", borrower]
    loan_pda, _ = Pubkey.find_program_address(
        [b"loan", bytes(borrower)], program_id
    )

    # Instruction data
    ix_data = build_initialize_loan_data(
        amount_usdc_lamports, initial_rate_bps, term_months, att_bytes
    )

    # Minimal accounts (borrower + loan PDA + system program)
    # NOTE: collateral vault accounts would also be needed for a full tx.
    # For the demo endpoint we pass borrower as both borrower and signer.
    accounts = [
        AccountMeta(pubkey=payer,      is_signer=True,  is_writable=True),   # payer/borrower
        AccountMeta(pubkey=loan_pda,   is_signer=False, is_writable=True),   # loan PDA
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]

    ix = Instruction(program_id=program_id, data=ix_data, accounts=accounts)

    blockhash_str = await get_latest_blockhash()
    blockhash = Hash.from_string(blockhash_str)

    msg = Message.new_with_blockhash([ix], payer, blockhash)
    tx  = Transaction([signer], msg, blockhash)

    tx_bytes = bytes(tx)
    tx_b64   = base64.b64encode(tx_bytes).decode()

    print(f"[SolanaClient] 📤 Sending initialize_loan tx to {SOLANA_NETWORK}...")
    sig = await send_transaction(tx_b64)
    confirmed = await confirm_transaction(sig)

    print(f"[SolanaClient] {'✅' if confirmed else '⚠️ '} TX {sig[:20]}... confirmed={confirmed}")

    return {
        "signature": sig,
        "slot": None,  # fill from confirmTransaction if needed
        "explorer_url": f"https://explorer.solana.com/tx/{sig}?cluster={SOLANA_NETWORK}",
        "demo": False,
        "confirmed": confirmed,
        "program_id": MYTHOS_PROGRAM_ID,
        "loan_pda": str(loan_pda),
        "amount_usdc": amount_usdc_ui,
        "rate_bps": initial_rate_bps,
        "term_months": term_months,
    }


# ============================================================================
# USDC Transfer Verifier (for x402 gate)
# ============================================================================

USDC_MINT_DEVNET = os.getenv(
    "USDC_MINT", "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
)
MIN_X402_USDC = 0.001  # minimum x402 payment in USDC


async def verify_usdc_transfer(
    signature: str,
    expected_recipient: Optional[str] = None,
    min_amount_usdc: float = MIN_X402_USDC,
) -> Dict[str, Any]:
    """
    Verify that a Solana transaction contains a USDC transfer of >= min_amount_usdc.

    Args:
        signature:          Transaction signature from X-Payment-Signature header
        expected_recipient: If set, verify the transfer went to this pubkey
        min_amount_usdc:    Minimum acceptable USDC amount (default 0.001)

    Returns dict with: verified(bool), amount(float), recipient, error(str|None)
    """
    if DEMO_MODE:
        return {
            "verified": True,
            "amount": min_amount_usdc,
            "recipient": expected_recipient or "demo",
            "signature": signature,
            "demo": True,
            "note": "Set X402_DEMO_MODE=false + HELIUS_API_KEY for real verification",
        }

    try:
        result = await _rpc("getTransaction", [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
        ])
    except Exception as e:
        return {"verified": False, "error": f"RPC error: {e}", "signature": signature}

    if result is None:
        return {"verified": False, "error": "Transaction not found", "signature": signature}

    # Walk token transfers in meta.postTokenBalances vs preTokenBalances
    meta = result.get("meta", {})
    if meta.get("err"):
        return {"verified": False, "error": f"TX failed on chain: {meta['err']}", "signature": signature}

    pre_balances  = {b["accountIndex"]: b for b in meta.get("preTokenBalances",  [])}
    post_balances = {b["accountIndex"]: b for b in meta.get("postTokenBalances", [])}
    account_keys  = result["transaction"]["message"]["accountKeys"]

    best_transfer_amount = 0.0
    best_recipient = None

    for idx, post in post_balances.items():
        # Only USDC transfers
        if post.get("mint") != USDC_MINT_DEVNET:
            continue
        pre_amt  = float(pre_balances.get(idx, {}).get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
        post_amt = float(post.get("uiTokenAmount", {}).get("uiAmount", 0) or 0)
        delta = post_amt - pre_amt
        if delta > best_transfer_amount:
            best_transfer_amount = delta
            key = account_keys[idx]
            best_recipient = key["pubkey"] if isinstance(key, dict) else str(key)

    if best_transfer_amount < min_amount_usdc:
        return {
            "verified": False,
            "error": f"USDC transfer too small: {best_transfer_amount:.6f} < {min_amount_usdc:.6f}",
            "signature": signature,
            "amount": best_transfer_amount,
        }

    if expected_recipient and best_recipient != expected_recipient:
        return {
            "verified": False,
            "error": f"Transfer went to {best_recipient}, expected {expected_recipient}",
            "signature": signature,
            "amount": best_transfer_amount,
        }

    return {
        "verified": True,
        "amount": best_transfer_amount,
        "recipient": best_recipient,
        "signature": signature,
        "demo": False,
    }


# ============================================================================
# CLI Entry (for keypair generation)
# ============================================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "generate-keypair":
        generate_and_print_keypair()
    else:
        print("Usage: python solana_client.py generate-keypair")
