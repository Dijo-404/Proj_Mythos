// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./CollateralVault.sol";
import "./LoanManager.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title LiquidationEngine
 * @dev Automated liquidation system for undercollateralized loans
 */
contract LiquidationEngine is ReentrancyGuard, Ownable {
    CollateralVault public collateralVault;
    LoanManager public loanManager;
    
    // Liquidation threshold (in basis points, e.g., 12000 = 120%)
    uint256 public liquidationThreshold;
    
    // Liquidation bonus (in basis points, e.g., 500 = 5% bonus for liquidator)
    uint256 public liquidationBonus;
    
    event LoanLiquidated(
        uint256 indexed loanId,
        address indexed liquidator,
        uint256 collateralAmount,
        uint256 bonusAmount
    );

    constructor(
        address _collateralVault,
        address _loanManager,
        uint256 _liquidationThreshold,
        uint256 _liquidationBonus
    ) {
        require(_liquidationThreshold >= 10000, "Threshold must be >= 100%");
        require(_liquidationBonus <= 1000, "Bonus must be <= 10%");
        
        collateralVault = CollateralVault(_collateralVault);
        loanManager = LoanManager(_loanManager);
        liquidationThreshold = _liquidationThreshold;
        liquidationBonus = _liquidationBonus;
    }

    /**
     * @dev Check if a loan can be liquidated
     * @param loanId Loan identifier
     * @return canLiquidate Whether loan can be liquidated
     * @return collateralRatio Current collateral ratio
     */
    function canLiquidate(uint256 loanId) external view returns (bool canLiquidate, uint256 collateralRatio) {
        LoanManager.Loan memory loan = loanManager.getLoan(loanId);
        
        if (loan.status != LoanManager.LoanStatus.Active) {
            return (false, 0);
        }
        
        // Get collateral value
        uint256 principal = loan.principal;
        (uint256 collateralValueUSD, uint256 ratio) = collateralVault.getCollateralValue(loanId, principal);
        
        // Can liquidate if ratio is below threshold
        canLiquidate = ratio < liquidationThreshold && collateralValueUSD > 0;
        collateralRatio = ratio;
    }

    /**
     * @dev Liquidate an undercollateralized loan
     * @param loanId Loan identifier
     */
    function liquidate(uint256 loanId) external nonReentrant {
        LoanManager.Loan memory loan = loanManager.getLoan(loanId);
        
        require(loan.status == LoanManager.LoanStatus.Active, "Loan not active");
        
        // Check collateral ratio
        uint256 principal = loan.principal;
        (uint256 collateralValueUSD, uint256 ratio) = collateralVault.getCollateralValue(loanId, principal);
        
        require(ratio < liquidationThreshold, "Loan not undercollateralized");
        require(collateralValueUSD > 0, "No collateral");
        
        // Calculate liquidation amount (only take enough to cover loan + bonus)
        uint256 collateralBalance = collateralVault.getCollateralBalance(loanId);
        
        // Calculate total debt (principal + interest)
        uint256 totalDebt = loanManager.getTotalRepayment(loanId);
        require(totalDebt > 0, "Invalid debt amount");
        
        // Liquidator gets collateral value of debt + bonus
        // Simplified: liquidate all collateral, liquidator pays debt to lender
        uint256 liquidationAmount = collateralBalance;
        uint256 bonus = (liquidationAmount * liquidationBonus) / 10000;
        uint256 totalToLiquidator = liquidationAmount + bonus;
        
        // Mark loan as liquidated in LoanManager (must be called first)
        loanManager.markLoanLiquidated(loanId);
        
        // Transfer collateral to liquidator
        collateralVault.liquidateCollateral(loanId, msg.sender, totalToLiquidator);
        
        emit LoanLiquidated(loanId, msg.sender, liquidationAmount, bonus);
    }

    /**
     * @dev Update liquidation parameters
     */
    function updateLiquidationThreshold(uint256 _threshold) external onlyOwner {
        require(_threshold >= 10000, "Threshold must be >= 100%");
        liquidationThreshold = _threshold;
    }

    function updateLiquidationBonus(uint256 _bonus) external onlyOwner {
        require(_bonus <= 1000, "Bonus must be <= 10%");
        liquidationBonus = _bonus;
    }
}
