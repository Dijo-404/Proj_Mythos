// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IERC20.sol";
import "./interfaces/IChainlinkOracle.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title CollateralVault
 * @dev Manages collateral deposits and withdrawals for loans
 */
contract CollateralVault is ReentrancyGuard, Ownable {
    // Mapping: loanId => collateral amount
    mapping(uint256 => uint256) public collateralAmounts;
    
    // Mapping: loanId => collateral token address
    mapping(uint256 => address) public collateralTokens;
    
    // Mapping: loanId => borrower address
    mapping(uint256 => address) public loanBorrowers;
    
    // Mapping: token => oracle address (for price feeds)
    mapping(address => address) public priceOracles;
    
    // Minimum collateral ratio (in basis points, e.g., 15000 = 150%)
    uint256 public minCollateralRatio;
    
    event CollateralDeposited(
        uint256 indexed loanId,
        address indexed borrower,
        address indexed token,
        uint256 amount
    );
    
    event CollateralWithdrawn(
        uint256 indexed loanId,
        address indexed borrower,
        address indexed token,
        uint256 amount
    );
    
    event OracleUpdated(address indexed token, address indexed oracle);

    constructor(uint256 _minCollateralRatio) {
        require(_minCollateralRatio >= 10000, "Collateral ratio must be >= 100%");
        minCollateralRatio = _minCollateralRatio;
    }

    /**
     * @dev Deposit collateral for a loan
     * @param loanId Loan identifier
     * @param collateralToken Address of collateral token (address(0) for ETH)
     * @param amount Amount of collateral to deposit
     */
    function depositCollateral(
        uint256 loanId,
        address collateralToken,
        uint256 amount
    ) external payable nonReentrant {
        require(amount > 0, "Amount must be > 0");
        require(collateralToken != address(0) || msg.value == amount, "ETH amount mismatch");
        
        if (collateralToken == address(0)) {
            // ETH collateral
            require(msg.value == amount, "ETH amount mismatch");
        } else {
            // ERC20 collateral
            require(msg.value == 0, "No ETH should be sent for ERC20");
            IERC20 token = IERC20(collateralToken);
            require(
                token.transferFrom(msg.sender, address(this), amount),
                "Token transfer failed"
            );
        }
        
        collateralAmounts[loanId] += amount;
        if (collateralTokens[loanId] == address(0)) {
            collateralTokens[loanId] = collateralToken;
            loanBorrowers[loanId] = msg.sender;
        }
        
        emit CollateralDeposited(loanId, msg.sender, collateralToken, amount);
    }

    /**
     * @dev Withdraw collateral after loan repayment
     * @param loanId Loan identifier
     * @param amount Amount to withdraw
     */
    function withdrawCollateral(
        uint256 loanId,
        uint256 amount
    ) external nonReentrant {
        require(loanBorrowers[loanId] == msg.sender, "Not the borrower");
        require(collateralAmounts[loanId] >= amount, "Insufficient collateral");
        
        collateralAmounts[loanId] -= amount;
        address collateralToken = collateralTokens[loanId];
        
        if (collateralToken == address(0)) {
            // ETH withdrawal
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "ETH transfer failed");
        } else {
            // ERC20 withdrawal
            IERC20 token = IERC20(collateralToken);
            require(token.transfer(msg.sender, amount), "Token transfer failed");
        }
        
        emit CollateralWithdrawn(loanId, msg.sender, collateralToken, amount);
    }

    /**
     * @dev Get collateral value in USD (for liquidation checks)
     * @param loanId Loan identifier
     * @param principalAmount Principal amount of loan (for ratio calculation)
     * @return collateralValueUSD Collateral value in USD (scaled by 1e8)
     * @return collateralRatio Collateral ratio in basis points
     */
    function getCollateralValue(
        uint256 loanId,
        uint256 principalAmount
    ) external view returns (uint256 collateralValueUSD, uint256 collateralRatio) {
        uint256 collateralAmount = collateralAmounts[loanId];
        address collateralToken = collateralTokens[loanId];
        
        if (collateralAmount == 0 || principalAmount == 0) {
            return (0, 0);
        }
        
        // Get price from oracle
        uint256 collateralPriceUSD = getTokenPriceUSD(collateralToken);
        
        // Calculate value (assuming 18 decimals for both, adjust as needed)
        collateralValueUSD = (collateralAmount * collateralPriceUSD) / 1e18;
        
        // Calculate ratio (basis points)
        collateralRatio = (collateralValueUSD * 10000) / principalAmount;
        
        return (collateralValueUSD, collateralRatio);
    }

    /**
     * @dev Get token price in USD from Chainlink oracle
     * @param token Token address (address(0) for ETH)
     * @return price Price in USD (scaled by 1e8)
     */
    function getTokenPriceUSD(address token) public view returns (uint256) {
        address oracle = priceOracles[token];
        require(oracle != address(0), "Oracle not set for token");
        
        IChainlinkOracle priceFeed = IChainlinkOracle(oracle);
        (, int256 price, , uint256 updatedAt, ) = priceFeed.latestRoundData();
        
        require(price > 0, "Invalid price");
        require(block.timestamp - updatedAt < 3600, "Price data stale"); // 1 hour
        
        uint8 decimals = priceFeed.decimals();
        return uint256(price) * (10**(18 - decimals)); // Normalize to 18 decimals
    }

    /**
     * @dev Set price oracle for a token
     * @param token Token address
     * @param oracle Chainlink price feed address
     */
    function setPriceOracle(address token, address oracle) external onlyOwner {
        priceOracles[token] = oracle;
        emit OracleUpdated(token, oracle);
    }

    /**
     * @dev Liquidate collateral (called by LiquidationEngine)
     * @param loanId Loan identifier
     * @param liquidator Address receiving the collateral
     * @param amount Amount to liquidate
     */
    function liquidateCollateral(
        uint256 loanId,
        address liquidator,
        uint256 amount
    ) external onlyOwner nonReentrant {
        require(collateralAmounts[loanId] >= amount, "Insufficient collateral");
        
        collateralAmounts[loanId] -= amount;
        address collateralToken = collateralTokens[loanId];
        
        if (collateralToken == address(0)) {
            (bool success, ) = liquidator.call{value: amount}("");
            require(success, "ETH transfer failed");
        } else {
            IERC20 token = IERC20(collateralToken);
            require(token.transfer(liquidator, amount), "Token transfer failed");
        }
    }

    /**
     * @dev Get collateral balance for a loan
     */
    function getCollateralBalance(uint256 loanId) external view returns (uint256) {
        return collateralAmounts[loanId];
    }

    // Allow contract to receive ETH
    receive() external payable {}
}

