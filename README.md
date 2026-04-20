<div align="center">

# ◎ MYTHOS

### AI-Native Agentic Lending Protocol on Solana

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Solana](https://img.shields.io/badge/Solana-Devnet-9945FF.svg)](https://solana.com/)
[![Anchor](https://img.shields.io/badge/Anchor-0.30-blue.svg)](https://anchor-lang.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org/)
[![Built for Solana Hackathon 2026](https://img.shields.io/badge/Solana%20Hackathon-2026-9945FF)](https://colosseum.org/)

<p align="center">
  <strong>Two AI agents. One loan. Fully on-chain.</strong><br/>
  Lenny & Luna negotiate your interest rate autonomously, pay each other in USDC via x402, and settle on Solana Devnet — no humans required.
</p>

[Live Demo](#-quick-start) •
[Architecture](#-architecture) •
[Tech Stack](#-tech-stack) •
[API Docs](#-api-reference)

</div>

---

## 🚀 What is Mythos?

**Mythos** is an AI-native, agentic DeFi lending protocol built natively on Solana. It eliminates the human negotiation bottleneck in DeFi lending by deploying two autonomous AI agents:

- 🤖 **Lenny** — the borrower agent. Reads your on-chain credit attestation (SAS), checks collateral prices via Jupiter, pays x402 micropayments to access AI services, and fights for the lowest possible interest rate.
- 🌙 **Luna** — the lender agent. Prices risk based on SAS credit tiers, evaluates counter-offers, and co-signs the final Anchor transaction.

Every AI service call between agents is governed by **x402** — the HTTP 402 payment protocol. Agents autonomously pay each other in USDC on Solana. No human clicks required.

### Why This Wins the Hackathon

| Hackathon Theme | Mythos Implementation |
|---|---|
| **Agentic Commerce** | Lenny & Luna are autonomous CrewAI agents that negotiate, pay, and settle — zero human intervention |
| **x402 Payments** | Every `/api/agent/*` endpoint requires a USDC micropayment in the `X-PAYMENT` header |
| **Identity & Stablecoins** | Solana Attestation Service (SAS) for on-chain credit identity, USDC for all payments |
| **Solana Performance** | Anchor programs on Devnet, Helius RPC, Jupiter price feeds, <1s settlement |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite + Framer Motion)          │
│  ┌──────────────┐  ┌─────────────────────┐  ┌───────────────────┐  │
│  │ Phantom/     │  │ Agent Negotiation   │  │ x402 Payment      │  │
│  │ Solflare     │  │ Live Feed (Lenny×   │  │ Visualizer        │  │
│  │ Wallet       │  │ Luna dialogue)      │  │ (USDC micropays)  │  │
│  └──────────────┘  └─────────────────────┘  └───────────────────┘  │
│                        Helius WebSocket Live Ticker                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ REST API / WebSocket
┌───────────────────────────▼─────────────────────────────────────────┐
│                   BACKEND (FastAPI + x402 Middleware)               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ Lenny Agent  │  │ Luna Agent   │  │ x402 Payment Gate         │ │
│  │ (CrewAI)     │  │ (CrewAI)     │  │ /api/agent/* → 402 →      │ │
│  │ SAS + Jup    │  │ Risk Pricing │  │ X-PAYMENT header verify   │ │
│  └──────────────┘  └──────────────┘  └───────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                                 │
│  │ SAS Client   │  │ Helius RPC   │                                 │
│  │ (Attestation)│  │ (Webhooks)   │                                 │
│  └──────────────┘  └──────────────┘                                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ Anchor CPI
┌───────────────────────────▼─────────────────────────────────────────┐
│                   SOLANA DEVNET (Anchor Programs)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ LoanAccount  │  │ Collateral   │  │ Solana Attestation        │ │
│  │ PDA          │  │ Vault (SPL)  │  │ Service (SAS) PDAs        │ │
│  └──────────────┘  └──────────────┘  └───────────────────────────┘ │
│                    Program: MythosLend1111...                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │  Jupiter Price API        │
              │  SOL/USDC/BONK real-time  │
              └───────────────────────────┘
```

### How a Loan Works

```
1. User connects Phantom wallet
2. Lenny reads SAS credit attestation (on-chain PDA)
3. Lenny calls /api/agent/evaluate [requires X-PAYMENT: 0.001 USDC via x402]
4. Luna prices the risk based on SAS tier + Jupiter collateral value
5. Lenny counter-offers [requires X-PAYMENT: 0.0005 USDC via x402]
6. Luna accepts/counters (2-3 rounds, ~5 seconds total)
7. Lenny broadcasts Anchor instruction: initialize_loan()
8. Collateral locked in SPL token vault PDA
9. USDC disbursed to borrower wallet
10. Helius webhook fires → dashboard updates in real-time
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Helius API key](https://helius.dev) (optional — demo mode works without it)
- A free [Groq API key](https://console.groq.com) (optional — simulation mode works without it)

### 1. Clone & Configure

```bash
git clone https://github.com/MUTHUKUMARAN-K-1/Proj_Mythos.git
cd Proj_Mythos

# Copy environment config
cp .env.example .env
# Edit .env and add your HELIUS_API_KEY and GROQ_API_KEY
```

### 2. Start the Backend

```bash
pip install -r requirements.txt
cd backend/api
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: **http://localhost:8000/docs**

### 3. Start the Frontend

```bash
cd frontend/Dashboard
npm install
npm run dev
```

Open: **http://localhost:5173**

### 4. Try the Demo

1. Click **"Connect Wallet"** (Phantom, Solflare, or Demo mode)
2. Set loan amount, term, collateral token
3. Click **"Start AI Negotiation"**
4. Watch Lenny & Luna negotiate live — with x402 micropayments flowing in real-time

---

## 💸 x402 Payment Protocol

Mythos is one of the first DeFi protocols to implement **x402** — the HTTP 402 Payment Required standard for machine-to-machine payments.

```
Agent (Lenny)                    Mythos API                    Solana
     │                               │                            │
     │  POST /api/agent/evaluate     │                            │
     │──────────────────────────────>│                            │
     │                               │                            │
     │  HTTP 402 Payment Required    │                            │
     │  X-PAYMENT-REQUIRED: base64({ │                            │
     │    scheme: "exact",           │                            │
     │    asset: USDC_DEVNET_MINT,   │                            │
     │    amount: 1000,  // 0.001 USDC│                           │
     │    payTo: TREASURY_WALLET     │                            │
     │  })                           │                            │
     │<──────────────────────────────│                            │
     │                               │                            │
     │  [Lenny pays 0.001 USDC]      │──── SPL Transfer ────────>│
     │                               │                            │
     │  POST /api/agent/evaluate     │                            │
     │  X-PAYMENT: base64({sig})     │                            │
     │──────────────────────────────>│                            │
     │                               │  getTransaction(sig)       │
     │                               │──────────────────────────>│
     │                               │  ✅ Verified               │
     │                               │<──────────────────────────│
     │  200 OK: AI evaluation result │                            │
     │<──────────────────────────────│                            │
```

### Protected Endpoints

| Endpoint | Price | Purpose |
|---|---|---|
| `POST /api/agent/evaluate` | 0.001 USDC | AI loan evaluation |
| `POST /api/agent/negotiate` | 0.0005 USDC | Counter-offer submission |
| `POST /api/agent/attest` | 0.002 USDC | Credit attestation request |

---

## 🪪 Solana Attestation Service (SAS)

Instead of ZK proofs (complex, expensive), Mythos uses **SAS** — Solana's native on-chain attestation system — for credit scoring.

```python
# SAS Credit Tiers
CREDIT_TIERS = {
    "AAA": {"rate_bps": 700, "max_loan": 100_000},  # Exceptional
    "AA":  {"rate_bps": 800, "max_loan": 75_000},   # Very Good
    "A":   {"rate_bps": 950, "max_loan": 50_000},   # Good
    "B":   {"rate_bps": 1100, "max_loan": 25_000},  # Fair
    "C":   {"rate_bps": 1300, "max_loan": 10_000},  # Limited
}
```

Each attestation is a **PDA** (Program Derived Address) on Solana that stores the borrower's credit tier, max loan amount, and LTV ratio — verifiable by any program without revealing raw financial data.

---

## 🔧 API Reference

### Solana-Native Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/solana/attest` | Issue SAS credit attestation |
| `GET` | `/api/solana/attest/{pubkey}` | Verify existing attestation |
| `GET` | `/api/solana/price/{symbol}` | Jupiter real-time price (SOL/USDC/BONK) |
| `GET` | `/api/solana/network` | Helius network stats |
| `GET` | `/api/solana/x402/stats` | x402 payment gate statistics |
| `POST` | `/api/solana/workflow/start` | Start full AI lending workflow |

### x402-Gated Agent Endpoints

| Method | Endpoint | Price | Description |
|---|---|---|---|
| `POST` | `/api/agent/evaluate` | 0.001 USDC | AI loan evaluation (SAS + Jupiter) |
| `POST` | `/api/agent/negotiate` | 0.0005 USDC | Submit counter-offer to Luna |

### WebSocket Events

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
// Events:
// attestation_issued    — New SAS attestation on-chain
// negotiation_round     — Lenny/Luna counter-offer exchange
// agent_evaluation      — x402-verified AI evaluation complete
// workflow_complete     — Loan settled on Solana
// workflow_step         — Any workflow state change
```

---

## 🛠 Tech Stack

### Smart Contracts
- **Framework**: Anchor (Rust)
- **Network**: Solana Devnet
- **Program**: `programs/mythos/src/lib.rs`
- **Instructions**: `initialize_loan`, `accept_loan`, `repay_loan`, `liquidate`
- **Accounts**: `LoanAccount` PDA, `CollateralVault` SPL token vault

### Backend
- **Framework**: FastAPI (Python)
- **AI Agents**: CrewAI + Groq (Llama 3.3 70B)
- **Payment Gate**: x402 HTTP 402 middleware (custom)
- **RPC**: Helius Enhanced API + Webhooks
- **Prices**: Jupiter Price API v6
- **Credit**: Solana Attestation Service (SAS)

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Wallet**: Phantom / Solflare (+ demo mode fallback)
- **Animation**: Framer Motion
- **Styling**: Tailwind CSS + shadcn/ui
- **Real-time**: Helius WebSocket live ticker

---

## 📁 Project Structure

```
Proj_Mythos/
├── programs/
│   └── mythos/
│       ├── Cargo.toml              # Anchor dependencies
│       └── src/lib.rs              # Anchor smart contract (498 lines)
│           ├── initialize_loan()   # Lock collateral, open loan request
│           ├── accept_loan()       # Luna accepts, disburses USDC
│           ├── repay_loan()        # Repay principal + interest, release collateral
│           └── liquidate()         # Seize collateral if overdue
├── agents/
│   ├── solana_borrower_agent.py   # Lenny (CrewAI) — x402 + SAS + Jupiter + Anchor
│   └── solana_lender_agent.py     # Luna (CrewAI) — risk pricing + health monitoring
├── backend/api/
│   ├── server.py                  # FastAPI app (Mythos v3.0.0)
│   ├── x402_middleware.py         # HTTP 402 payment gate (real x402 spec)
│   ├── attestation.py             # SAS client — issue/verify credit attestations
│   └── helius_client.py           # Helius RPC + webhook + event streaming
└── frontend/Dashboard/src/
    ├── lib/solana.ts               # Solana utilities (fetch-based, no SDK dep)
    ├── components/
    │   ├── wallet/SolanaWalletProvider.tsx  # Phantom + Solflare + demo mode
    │   ├── AgentNegotiationFeed.tsx          # Live Lenny×Luna dialogue
    │   └── X402PaymentVisualizer.tsx         # Animated micropayment flows
    └── pages/MythosPage.tsx        # Main hackathon demo page
```


---

## 🚀 Live Deployment — Solana Devnet

> **The Mythos program is deployed and live on Solana Devnet.**

| | |
|---|---|
| **Program ID** | `FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM` |
| **Network** | Solana **Devnet** |
| **Deploy Wallet** | `61m3ESHMhzDygAUWkSyXTCBr6Jy9gSnSF3Dqm6fxhg6s` |
| **Deploy TX** | [`3twz9fk...`](https://explorer.solana.com/tx/3twz9fkqZWktXGXukqGZqrwJLpY41A8iLmjyPN3TwWP4J4fobtUYNZPbshxkS6cdDqCAAT8t3xVFE8zw3y5TBrig?cluster=devnet) |
| **Deployed Slot** | `456903617` |
| **View on Solscan** | [solscan.io/account/FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM?cluster=devnet](https://solscan.io/account/FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM?cluster=devnet) |
| **View on Explorer** | [explorer.solana.com/address/FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM?cluster=devnet](https://explorer.solana.com/address/FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM?cluster=devnet) |
| **Anchor Version** | 1.0.0 |
| **Deploy Toolchain** | Rust stable 1.95 + cargo-build-sbf (Agave 3.1.13) |

### Instructions in the Anchor Program

| Instruction | Description |
|---|---|
| `initialize_loan` | Borrower opens loan — locks SPL collateral in PDA vault |
| `accept_loan` | Luna (lender agent) accepts terms — disburses USDC to borrower |
| `repay_loan` | Borrower repays principal + interest — collateral released |
| `liquidate` | Seize collateral on overdue/undercollateralized loan |

### Redeploy from Source

```bash
# Prerequisites: Solana CLI + Rust stable + cargo-build-sbf

# 1. Build the program
cargo-build-sbf --manifest-path programs/mythos/Cargo.toml

# 2. Deploy to Devnet
solana program deploy \
  target/deploy/mythos.so \
  --keypair ~/.config/solana/id.json \
  --url devnet \
  --program-id target/deploy/mythos-keypair.json

# 3. Verify
solana program show FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM --url devnet
```

### Full Stack Deployment

| Service | Platform | Status |
|---|---|---|
| **Anchor Program** | Solana Devnet | ✅ Live |
| Frontend | Vercel / Netlify | Deploy with `vercel --prod` |
| Backend | Railway / Render | Deploy with `railway up` |

---

## 🔑 Environment Variables

```env
# Solana — Devnet (live)
SOLANA_NETWORK=devnet
MYTHOS_PROGRAM_ID=FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM
DEPLOY_WALLET=61m3ESHMhzDygAUWkSyXTCBr6Jy9gSnSF3Dqm6fxhg6s

# Get free API keys:
HELIUS_API_KEY=your_key_from_helius.dev     # https://helius.dev
GROQ_API_KEY=your_key_from_console.groq.com # https://console.groq.com

# Protocol
TREASURY_WALLET=61m3ESHMhzDygAUWkSyXTCBr6Jy9gSnSF3Dqm6fxhg6s
USDC_MINT=4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU  # Devnet USDC

# Frontend
VITE_API_URL=http://localhost:8000
VITE_SOLANA_NETWORK=devnet
VITE_HELIUS_API_KEY=your_helius_key
VITE_PROGRAM_ID=FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM
```

See [`.env.example`](.env.example) for all options.

---

## 🏆 Hackathon Alignment

**Solana Hackathon 2026 — Track: Agentic Commerce, Identity, Payments & Stablecoins**

| Criterion | Score | Evidence |
|---|---|---|
| Solana scalability | ✅ | Anchor program live on Devnet (`FGG836...`), Helius RPC, <400ms settlement |
| Composability | ✅ | SAS + Jupiter + x402 + Anchor in one atomic flow |
| Agentic commerce | ✅ | Lenny & Luna pay each other (M2M) via x402 — zero human clicks |
| Identity | ✅ | SAS on-chain credit attestation PDAs replace centralized credit bureaus |
| Stablecoins | ✅ | USDC for x402 micropayments AND loan disbursement |
| Innovation | ✅ | First DeFi protocol gating AI calls behind x402 USDC micropayments |
| Technical skill | ✅ | Rust/Anchor + CrewAI + FastAPI + React + Helius — full-stack on Solana |
| Real-world impact | ✅ | Eliminates human negotiation bottleneck in DeFi lending, M2M agentic economy |

---

<div align="center">

Built with ◎ for the Solana Hackathon 2026

**Program: [`FGG836...`](https://explorer.solana.com/address/FGG8363rUtdVernzHtXr4AD9PS9m4BezgAN8MJKcybpM?cluster=devnet) | Wallet: [`61m3ES...`](https://explorer.solana.com/address/61m3ESHMhzDygAUWkSyXTCBr6Jy9gSnSF3Dqm6fxhg6s?cluster=devnet)**

**[⬆ Back to Top](#-mythos)**

</div>


| Service | Platform |
|---|---|
| Frontend | Vercel / Netlify |
| Backend | Railway / Render |
| Smart Contract | Solana Devnet (Anchor deploy) |

```bash
# Deploy Anchor program to Devnet
anchor build
anchor deploy --provider.cluster devnet

# Deploy backend
railway up

# Deploy frontend
vercel --prod
```

---

## 🔑 Environment Variables

```env
# Solana
SOLANA_NETWORK=devnet
HELIUS_API_KEY=your_key_from_helius.dev
MYTHOS_PROGRAM_ID=<from: anchor deploy>

# AI Agents
GROQ_API_KEY=your_key_from_console.groq.com

# Protocol
TREASURY_WALLET=<your Solana wallet address>
USDC_MINT=4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU

# Frontend
VITE_API_URL=http://localhost:8000
VITE_SOLANA_NETWORK=devnet
VITE_HELIUS_API_KEY=your_helius_key
```

See [`.env.example`](.env.example) for all options.

---

## 🏆 Hackathon Alignment

**Solana Hackathon 2026 — Track: Agentic Commerce, Identity, Payments & Stablecoins**

| Criterion | Score | Evidence |
|---|---|---|
| Solana scalability | ✅ | Anchor/Devnet, Helius RPC, <1s settlement |
| Composability | ✅ | SAS + Jupiter + x402 + Anchor in one flow |
| Agentic commerce | ✅ | Agents pay each other (M2M) via x402 without any human action |
| Identity | ✅ | SAS on-chain credit attestation PDAs |
| Stablecoins | ✅ | USDC for x402 payments AND loan disbursement |
| Innovation | ✅ | First agentic lending protocol with x402 payment gates |
| Technical skill | ✅ | Rust Anchor + CrewAI + FastAPI + React full-stack |
| Real-world impact | ✅ | Eliminates human negotiation in DeFi lending |

---

<div align="center">

Built with ◎ for the Solana Hackathon 2026

**[⬆ Back to Top](#-mythos)**

</div>
