use solana_program::program_error::ProgramError;
use thiserror::Error;

#[derive(Error, Debug, Copy, Clone)]
pub enum MythosError {
    #[error("Invalid Instruction")]
    InvalidInstruction,
    #[error("Not Rent Exempt")]
    NotRentExempt,
    #[error("Unsupported Stablecoin Mint")]
    UnsupportedMint,
    #[error("Loan Already Initialized")]
    AlreadyInitialized,
    #[error("Loan Not Active")]
    LoanNotActive,
    #[error("Insufficient Collateral")]
    InsufficientCollateral,
    #[error("Invalid Pyth Price")]
    InvalidOraclePrice,
    #[error("Invalid Credit Proof")]
    InvalidCreditProof,
}

impl From<MythosError> for ProgramError {
    fn from(e: MythosError) -> Self {
        ProgramError::Custom(e as u32)
    }
}
