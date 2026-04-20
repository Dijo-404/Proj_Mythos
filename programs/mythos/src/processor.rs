use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};

use crate::{
    error::MythosError,
    instruction::MythosInstruction,
    state::{LoanState, LoanStatus},
};

pub struct Processor;

impl Processor {
    pub fn process(
        program_id: &Pubkey,
        accounts: &[AccountInfo],
        instruction_data: &[u8],
    ) -> ProgramResult {
        let instruction = MythosInstruction::unpack(instruction_data)?;

        match instruction {
            MythosInstruction::InitializeGlobalState => {
                msg!("Instruction: InitializeGlobalState");
                Self::process_initialize_global_state(accounts, program_id)
            }
            MythosInstruction::RequestLoan { principal, interest_rate_bps, term_seconds, credit_score_proof } => {
                msg!("Instruction: RequestLoan");
                Self::process_request_loan(accounts, principal, interest_rate_bps, term_seconds, credit_score_proof, program_id)
            }
            MythosInstruction::FundLoan => {
                msg!("Instruction: FundLoan");
                Self::process_fund_loan(accounts, program_id)
            }
            MythosInstruction::DepositCollateral { amount } => {
                msg!("Instruction: DepositCollateral");
                Self::process_deposit_collateral(accounts, amount, program_id)
            }
            MythosInstruction::RepayLoan { amount } => {
                msg!("Instruction: RepayLoan");
                Self::process_repay_loan(accounts, amount, program_id)
            }
            MythosInstruction::LiquidateLoan => {
                msg!("Instruction: LiquidateLoan");
                Self::process_liquidate_loan(accounts, program_id)
            }
        }
    }

    fn process_initialize_global_state(
        _accounts: &[AccountInfo],
        _program_id: &Pubkey,
    ) -> ProgramResult {
        // Implementation stub
        Ok(())
    }

    fn process_request_loan(
        _accounts: &[AccountInfo],
        _principal: u64,
        _interest_rate_bps: u16,
        _term_seconds: u64,
        _credit_score_proof: [u8; 32],
        _program_id: &Pubkey,
    ) -> ProgramResult {
        // Here we'd verify ZK compression proof for credit score
        // Stub implementation
        Ok(())
    }

    fn process_fund_loan(
        accounts: &[AccountInfo],
        _program_id: &Pubkey,
    ) -> ProgramResult {
        let account_info_iter = &mut accounts.iter();
        let _lender = next_account_info(account_info_iter)?;
        let _loan_state = next_account_info(account_info_iter)?;
        let _lender_token = next_account_info(account_info_iter)?;
        let _borrower_token = next_account_info(account_info_iter)?;
        let mint_info = next_account_info(account_info_iter)?;

        // Enforce Stablecoin Mints (USDC, USDT, PYUSD mainnet addresses)
        let usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v".parse::<Pubkey>().unwrap();
        let usdt = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB".parse::<Pubkey>().unwrap();
        let pyusd = "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo".parse::<Pubkey>().unwrap();
        
        if *mint_info.key != usdc && *mint_info.key != usdt && *mint_info.key != pyusd {
            return Err(MythosError::UnsupportedMint.into());
        }

        Ok(())
    }

    fn process_deposit_collateral(
        _accounts: &[AccountInfo],
        _amount: u64,
        _program_id: &Pubkey,
    ) -> ProgramResult {
        // Stub implementation
        Ok(())
    }

    fn process_repay_loan(
        _accounts: &[AccountInfo],
        _amount: u64,
        _program_id: &Pubkey,
    ) -> ProgramResult {
        // Stub implementation
        Ok(())
    }

    fn process_liquidate_loan(
        _accounts: &[AccountInfo],
        _program_id: &Pubkey,
    ) -> ProgramResult {
        // Here we'd integrate Pyth Oracle
        // Stub implementation
        Ok(())
    }
}
