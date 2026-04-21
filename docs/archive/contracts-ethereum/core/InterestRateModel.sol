// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title InterestRateModel
 * @dev Dynamic interest rate calculation model
 * @notice Interest rates are calculated in basis points (1 basis point = 0.01%)
 */
contract InterestRateModel {
    // Constants
    uint256 public constant MIN_INTEREST_RATE = 100; // 1% minimum
    uint256 public constant MAX_INTEREST_RATE = 5000; // 50% maximum
    uint256 public constant BASIS_POINTS = 10000; // 100%
    
    // Base rate (in basis points)
    uint256 public baseRate;
    
    // Risk premium parameters
    uint256 public riskPremiumMultiplier; // Multiplier for collateral ratio
    
    event InterestRateUpdated(uint256 baseRate, uint256 multiplier);

    constructor(uint256 _baseRate, uint256 _riskPremiumMultiplier) {
        require(_baseRate <= MAX_INTEREST_RATE, "Base rate too high");
        require(_riskPremiumMultiplier <= 10000, "Multiplier too high");
        
        baseRate = _baseRate;
        riskPremiumMultiplier = _riskPremiumMultiplier;
    }

    /**
     * @dev Calculate interest rate based on collateral ratio and risk factors
     * @param collateralRatio Collateral ratio in basis points (e.g., 15000 = 150%)
     * @param creditEligible Whether borrower passed ZK credit check
     * @return interestRate Interest rate in basis points
     */
    function calculateInterestRate(
        uint256 collateralRatio,
        bool creditEligible
    ) external view returns (uint256) {
        // Start with base rate
        uint256 rate = baseRate;
        
        // Adjust based on collateral ratio
        // Higher collateral = lower risk = lower rate
        if (collateralRatio >= 20000) {
            // 200%+ collateral: premium rate (base rate - 50 bps)
            rate = baseRate > 50 ? baseRate - 50 : baseRate;
        } else if (collateralRatio >= 15000) {
            // 150-200% collateral: standard rate
            rate = baseRate;
        } else if (collateralRatio >= 12000) {
            // 120-150% collateral: base + 100 bps
            rate = baseRate + 100;
        } else {
            // <120% collateral: base + 200 bps (high risk)
            rate = baseRate + 200;
        }
        
        // Credit check premium
        if (!creditEligible) {
            rate += 150; // Add 1.5% for no credit check
        }
        
        // Ensure rate is within bounds
        if (rate < MIN_INTEREST_RATE) rate = MIN_INTEREST_RATE;
        if (rate > MAX_INTEREST_RATE) rate = MAX_INTEREST_RATE;
        
        return rate;
    }

    /**
     * @dev Calculate total interest for a loan
     * @param principal Loan principal amount
     * @param interestRate Interest rate in basis points
     * @param termMonths Loan term in months
     * @return totalInterest Total interest amount
     */
    function calculateTotalInterest(
        uint256 principal,
        uint256 interestRate,
        uint256 termMonths
    ) external pure returns (uint256) {
        // Simple interest calculation: Principal * Rate * Time
        // Rate is in basis points, time in months (12 months = 1 year)
        return (principal * interestRate * termMonths) / (BASIS_POINTS * 12);
    }

    /**
     * @dev Update base interest rate (admin function)
     */
    function updateBaseRate(uint256 _baseRate) external {
        require(_baseRate <= MAX_INTEREST_RATE, "Rate too high");
        baseRate = _baseRate;
        emit InterestRateUpdated(baseRate, riskPremiumMultiplier);
    }
}

