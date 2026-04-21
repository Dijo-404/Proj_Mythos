// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IERC20.sol";
import "./CollateralVault.sol";
import "./InterestRateModel.sol";
import "./LiquidationEngine.sol";
import "./zk/CreditScoreVerifier.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title LoanManager
 * @dev Main loan orchestration contract - equivalent to Aiken settlement validator
 * @notice Manages loan lifecycle: creation, repayment, and liquidation
 */
contract LoanManager is ReentrancyGuard, Ownable {
    // ============================================================================
    // Types
    // ============================================================================
    
    enum LoanStatus {
        Pending,
        Active,
        Repaid,
        Liquidated,
        Cancelled
    }
    
    struct Loan {
        address borrower;
        address lender;
        uint256 principal;
        uint256 interestRate; // in basis points
        uint256 termMonths;
        uint256 collateralAmount;
        address collateralToken;
        address loanToken; // USDC, DAI, etc.
        uint256 createdAt;
        uint256 dueDate;
        uint256 repaidAt;
        LoanStatus status;
        bytes32 zkProofHash; // Hash of ZK proof for credit check
        bool creditEligible;
    }
    
    // ============================================================================
    // State Variables
    // ============================================================================
    
    mapping(uint256 => Loan) public loans;
    uint256 public nextLoanId;
    
    CollateralVault public collateralVault;
    InterestRateModel public interestRateModel;
    LiquidationEngine public liquidationEngine;
    CreditScoreVerifier public creditScoreVerifier;
    
    // Minimum loan principal
    uint256 public minPrincipal;
    
    // ============================================================================
    // Events
    // ============================================================================
    
    event LoanCreated(
        uint256 indexed loanId,
        address indexed borrower,
        address indexed lender,
        uint256 principal,
        uint256 interestRate,
        uint256 termMonths,
        bytes32 zkProofHash
    );
    
    event LoanRepaid(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 principal,
        uint256 interest
    );
    
    event LoanLiquidated(
        uint256 indexed loanId,
        address indexed liquidator
    );
    
    // ============================================================================
    // Constructor
    // ============================================================================
    
    constructor(
        address _collateralVault,
        address _interestRateModel,
        address _liquidationEngine,
        address _creditScoreVerifier,
        uint256 _minPrincipal
    ) {
        require(_collateralVault != address(0), "Invalid vault address");
        require(_interestRateModel != address(0), "Invalid rate model");
        require(_liquidationEngine != address(0), "Invalid liquidation engine");
        require(_creditScoreVerifier != address(0), "Invalid verifier");
        
        collateralVault = CollateralVault(_collateralVault);
        interestRateModel = InterestRateModel(_interestRateModel);
        liquidationEngine = LiquidationEngine(_liquidationEngine);
        creditScoreVerifier = CreditScoreVerifier(_creditScoreVerifier);
        minPrincipal = _minPrincipal;
    }
    
    // ============================================================================
    // Main Functions
    // ============================================================================
    
    /**
     * @dev Create a new loan (settlement equivalent from Aiken validator)
     * @notice Both borrower and lender must sign this transaction via multi-sig or EIP-712
     * @param lender Lender address
     * @param principal Principal amount
     * @param interestRate Final interest rate (in basis points) - agreed in off-chain negotiation
     * @param termMonths Loan term in months
     * @param collateralToken Collateral token address (address(0) for ETH)
     * @param collateralAmount Collateral amount
     * @param loanToken Loan token address (USDC, DAI, etc.)
     * @param zkProof ZK proof bytes for credit verification
     * @param publicSignals Public signals for ZK proof
     * @return loanId The ID of the created loan
     */
    function createLoan(
        address lender,
        uint256 principal,
        uint256 interestRate,
        uint256 termMonths,
        address collateralToken,
        uint256 collateralAmount,
        address loanToken,
        uint256[8] calldata zkProof,
        uint256[1] calldata publicSignals
    ) external payable nonReentrant returns (uint256 loanId) {
        require(lender != address(0), "Invalid lender");
        require(msg.sender != lender, "Cannot lend to self");
        require(principal >= minPrincipal, "Principal too low");
        require(interestRate >= 100 && interestRate <= 5000, "Invalid interest rate");
        require(termMonths > 0 && termMonths <= 60, "Invalid term");
        
        // Verify ZK proof for credit eligibility
        bool creditEligible = creditScoreVerifier.verifyCreditScore(zkProof, publicSignals);
        bytes32 proofHash = keccak256(abi.encodePacked(zkProof, publicSignals));
        
        // Verify collateral ratio
        uint256 collateralRatio = _calculateCollateralRatio(
            collateralToken,
            collateralAmount,
            loanToken,
            principal
        );
        require(collateralRatio >= collateralVault.minCollateralRatio(), "Insufficient collateral");
        
        // Verify interest rate matches calculated rate
        uint256 calculatedRate = interestRateModel.calculateInterestRate(collateralRatio, creditEligible);
        require(
            interestRate >= calculatedRate - 50 && interestRate <= calculatedRate + 50,
            "Interest rate mismatch"
        );
        
        // Create loan
        loanId = nextLoanId++;
        loans[loanId] = Loan({
            borrower: msg.sender,
            lender: lender,
            principal: principal,
            interestRate: interestRate,
            termMonths: termMonths,
            collateralAmount: collateralAmount,
            collateralToken: collateralToken,
            loanToken: loanToken,
            createdAt: block.timestamp,
            dueDate: block.timestamp + (termMonths * 30 days),
            repaidAt: 0,
            status: LoanStatus.Pending,
            zkProofHash: proofHash,
            creditEligible: creditEligible
        });
        
        // Deposit collateral
        if (collateralToken == address(0)) {
            require(msg.value == collateralAmount, "ETH amount mismatch");
            collateralVault.depositCollateral{value: collateralAmount}(loanId, collateralToken, collateralAmount);
        } else {
            require(msg.value == 0, "No ETH should be sent for ERC20 collateral");
            IERC20(collateralToken).transferFrom(msg.sender, address(collateralVault), collateralAmount);
            collateralVault.depositCollateral(loanId, collateralToken, collateralAmount);
        }
        
        // Transfer loan principal from lender to borrower
        IERC20 loanTokenContract = IERC20(loanToken);
        require(
            loanTokenContract.transferFrom(lender, msg.sender, principal),
            "Loan transfer failed"
        );
        
        // Mark loan as active
        loans[loanId].status = LoanStatus.Active;
        
        emit LoanCreated(loanId, msg.sender, lender, principal, interestRate, termMonths, proofHash);
        
        return loanId;
    }
    
    /**
     * @dev Repay a loan
     * @param loanId Loan identifier
     */
    function repayLoan(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        
        require(loan.status == LoanStatus.Active, "Loan not active");
        require(msg.sender == loan.borrower, "Not the borrower");
        require(block.timestamp <= loan.dueDate, "Loan overdue");
        
        // Calculate interest
        uint256 totalInterest = interestRateModel.calculateTotalInterest(
            loan.principal,
            loan.interestRate,
            loan.termMonths
        );
        uint256 totalRepayment = loan.principal + totalInterest;
        
        // Transfer repayment from borrower to lender
        IERC20 loanTokenContract = IERC20(loan.loanToken);
        require(
            loanTokenContract.transferFrom(msg.sender, loan.lender, totalRepayment),
            "Repayment transfer failed"
        );
        
        // Update loan state
        loan.status = LoanStatus.Repaid;
        loan.repaidAt = block.timestamp;
        
        // Withdraw collateral back to borrower
        collateralVault.withdrawCollateral(loanId, loan.collateralAmount);
        
        emit LoanRepaid(loanId, msg.sender, loan.principal, totalInterest);
    }
    
    /**
     * @dev Mark loan as liquidated (called by LiquidationEngine)
     * @param loanId Loan identifier
     */
    function markLoanLiquidated(uint256 loanId) external {
        require(msg.sender == address(liquidationEngine), "Only liquidation engine");
        
        Loan storage loan = loans[loanId];
        require(loan.status == LoanStatus.Active, "Loan not active");
        
        loan.status = LoanStatus.Liquidated;
        
        emit LoanLiquidated(loanId, msg.sender);
    }
    
    /**
     * @dev Get loan status
     */
    function getLoanStatus(uint256 loanId) external view returns (LoanStatus) {
        return loans[loanId].status;
    }
    
    // ============================================================================
    // View Functions
    // ============================================================================
    
    /**
     * @dev Get loan details
     */
    function getLoan(uint256 loanId) external view returns (Loan memory) {
        return loans[loanId];
    }
    
    /**
     * @dev Get total repayment amount for a loan
     */
    function getTotalRepayment(uint256 loanId) external view returns (uint256) {
        Loan memory loan = loans[loanId];
        
        if (loan.status != LoanStatus.Active && loan.status != LoanStatus.Pending) {
            return 0;
        }
        
        uint256 totalInterest = interestRateModel.calculateTotalInterest(
            loan.principal,
            loan.interestRate,
            loan.termMonths
        );
        
        return loan.principal + totalInterest;
    }
    
    // ============================================================================
    // Internal Functions
    // ============================================================================
    
    /**
     * @dev Calculate collateral ratio
     */
    function _calculateCollateralRatio(
        address collateralToken,
        uint256 collateralAmount,
        address loanToken,
        uint256 principal
    ) internal view returns (uint256) {
        // Get collateral value in USD
        uint256 collateralValue = collateralVault.getTokenPriceUSD(collateralToken) * collateralAmount / 1e18;
        
        // Get loan token value in USD (assume 1:1 for stablecoins)
        uint256 principalValue = principal; // Adjust if loan token isn't 1:1 USD
        
        if (principalValue == 0) return 0;
        
        // Return ratio in basis points
        return (collateralValue * 10000) / principalValue;
    }
    
    // ============================================================================
    // Admin Functions
    // ============================================================================
    
    function setMinPrincipal(uint256 _minPrincipal) external onlyOwner {
        minPrincipal = _minPrincipal;
    }
}
