use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone, PartialEq)]
pub enum LoanStatus {
    Requested,
    Active,
    Repaid,
    Liquidated,
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct LoanState {
    pub is_initialized: bool,
    pub borrower: Pubkey,
    pub lender: Pubkey,
    pub principal: u64,
    pub interest_rate_bps: u16,
    pub term_seconds: u64,
    pub start_time: u64,
    pub collateral_mint: Pubkey,
    pub collateral_amount: u64,
    pub stablecoin_mint: Pubkey,
    pub amount_repaid: u64,
    pub status: LoanStatus,
}

impl LoanState {
    pub const LEN: usize = 1 + 32 + 32 + 8 + 2 + 8 + 8 + 32 + 8 + 32 + 8 + 1;
}
