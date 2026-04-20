use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::program_error::ProgramError;

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum MythosInstruction {
    /// Initialize a new loan pool or global state.
    /// 
    /// Accounts expected:
    /// 0. `[signer, writable]` Admin account
    /// 1. `[writable]` Global state account
    /// 2. `[]` System program
    InitializeGlobalState,

    /// Request a new loan
    /// 
    /// Accounts expected:
    /// 0. `[signer, writable]` Borrower account
    /// 1. `[writable]` Loan state account
    /// 2. `[]` System program
    RequestLoan {
        principal: u64,
        interest_rate_bps: u16,
        term_seconds: u64,
        credit_score_proof: [u8; 32], // Simulating ZK Light Protocol proof hash
    },

    /// Fund a requested loan
    ///
    /// Accounts expected:
    /// 0. `[signer, writable]` Lender account
    /// 1. `[writable]` Loan state account
    /// 2. `[writable]` Lender token account
    /// 3. `[writable]` Borrower token account
    /// 4. `[]` Stablecoin Mint
    /// 5. `[]` Token program
    FundLoan,

    /// Deposit Collateral
    ///
    /// Accounts expected:
    /// 0. `[signer, writable]` Borrower account
    /// 1. `[writable]` Loan state account
    /// 2. `[writable]` Collateral vault token account (PDA)
    /// 3. `[writable]` Borrower collateral token account
    /// 4. `[]` Token program
    DepositCollateral {
        amount: u64,
    },

    /// Repay a loan
    ///
    /// Accounts expected:
    /// 0. `[signer, writable]` Borrower account
    /// 1. `[writable]` Loan state account
    /// 2. `[writable]` Borrower token account
    /// 3. `[writable]` Lender token account
    /// 4. `[]` Token program
    RepayLoan {
        amount: u64,
    },

    /// Liquidate a loan if collateral drops below threshold (checked via Pyth)
    ///
    /// Accounts expected:
    /// 0. `[signer, writable]` Liquidator account
    /// 1. `[writable]` Loan state account
    /// 2. `[writable]` Collateral vault token account (PDA)
    /// 3. `[writable]` Liquidator collateral token account
    /// 4. `[]` Pyth Oracle Account
    /// 5. `[]` Token program
    LiquidateLoan,
}

impl MythosInstruction {
    pub fn unpack(input: &[u8]) -> Result<Self, ProgramError> {
        Self::try_from_slice(input).map_err(|_| ProgramError::InvalidInstructionData)
    }
}
