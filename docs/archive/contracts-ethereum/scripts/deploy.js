// Hardhat deployment script for Lendora AI contracts
// Deploy order: InterestRateModel -> CollateralVault -> LiquidationEngine -> CreditScoreVerifier -> LoanManager

const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString());

  // ============================================================================
  // 1. Deploy InterestRateModel
  // ============================================================================
  console.log("\n1. Deploying InterestRateModel...");
  const InterestRateModel = await hre.ethers.getContractFactory("InterestRateModel");
  const baseRate = 500; // 5% base rate (in basis points)
  const riskPremiumMultiplier = 1000; // 10% multiplier
  const interestRateModel = await InterestRateModel.deploy(baseRate, riskPremiumMultiplier);
  await interestRateModel.waitForDeployment();
  const interestRateModelAddress = await interestRateModel.getAddress();
  console.log("InterestRateModel deployed to:", interestRateModelAddress);

  // ============================================================================
  // 2. Deploy CollateralVault
  // ============================================================================
  console.log("\n2. Deploying CollateralVault...");
  const CollateralVault = await hre.ethers.getContractFactory("CollateralVault");
  const minCollateralRatio = 15000; // 150% minimum (in basis points)
  const collateralVault = await CollateralVault.deploy(minCollateralRatio);
  await collateralVault.waitForDeployment();
  const collateralVaultAddress = await collateralVault.getAddress();
  console.log("CollateralVault deployed to:", collateralVaultAddress);

  // Set price oracles (example: ETH/USD feed on Arbitrum)
  // Chainlink ETH/USD price feed on Arbitrum Goerli: varies, check Chainlink docs
  // For mainnet: 0x639Fe6ab55C92174dC7ECF4e0c8D6A3E78C5C7F7
  const ETH_PRICE_FEED = process.env.CHAINLINK_ETH_FEED || "0x0000000000000000000000000000000000000000";
  if (ETH_PRICE_FEED !== "0x0000000000000000000000000000000000000000") {
    console.log("Setting ETH price oracle...");
    await collateralVault.setPriceOracle("0x0000000000000000000000000000000000000000", ETH_PRICE_FEED);
  }

  // ============================================================================
  // 3. Deploy LiquidationEngine
  // ============================================================================
  console.log("\n3. Deploying LiquidationEngine...");
  const LiquidationEngine = await hre.ethers.getContractFactory("LiquidationEngine");
  const liquidationThreshold = 12000; // 120% threshold (in basis points)
  const liquidationBonus = 500; // 5% bonus (in basis points)
  const liquidationEngine = await LiquidationEngine.deploy(
    collateralVaultAddress,
    "0x0000000000000000000000000000000000000000", // LoanManager address (will update later)
    liquidationThreshold,
    liquidationBonus
  );
  await liquidationEngine.waitForDeployment();
  const liquidationEngineAddress = await liquidationEngine.getAddress();
  console.log("LiquidationEngine deployed to:", liquidationEngineAddress);

  // ============================================================================
  // 4. Deploy CreditScoreVerifier (ZK Verifier)
  // ============================================================================
  console.log("\n4. Deploying CreditScoreVerifier...");
  const CreditScoreVerifier = await hre.ethers.getContractFactory("CreditScoreVerifier");
  const creditScoreVerifier = await CreditScoreVerifier.deploy();
  await creditScoreVerifier.waitForDeployment();
  const creditScoreVerifierAddress = await creditScoreVerifier.getAddress();
  console.log("CreditScoreVerifier deployed to:", creditScoreVerifierAddress);

  // ============================================================================
  // 5. Deploy LoanManager
  // ============================================================================
  console.log("\n5. Deploying LoanManager...");
  const LoanManager = await hre.ethers.getContractFactory("LoanManager");
  const minPrincipal = hre.ethers.parseEther("0.1"); // 0.1 ETH minimum
  const loanManager = await LoanManager.deploy(
    collateralVaultAddress,
    interestRateModelAddress,
    liquidationEngineAddress,
    creditScoreVerifierAddress,
    minPrincipal
  );
  await loanManager.waitForDeployment();
  const loanManagerAddress = await loanManager.getAddress();
  console.log("LoanManager deployed to:", loanManagerAddress);

  // Update LiquidationEngine with LoanManager address
  console.log("\nUpdating LiquidationEngine with LoanManager address...");
  const liquidationEngineContract = await hre.ethers.getContractAt("LiquidationEngine", liquidationEngineAddress);
  // Note: This requires updating LiquidationEngine to allow setting loanManager
  // For now, we'll deploy LiquidationEngine after LoanManager in a future version
  
  // Transfer ownership of CollateralVault to LoanManager (if needed)
  // await collateralVault.transferOwnership(loanManagerAddress);

  // ============================================================================
  // Summary
  // ============================================================================
  console.log("\n" + "=".repeat(70));
  console.log("DEPLOYMENT SUMMARY");
  console.log("=".repeat(70));
  console.log("Network:", hre.network.name);
  console.log("Deployer:", deployer.address);
  console.log("\nContract Addresses:");
  console.log("  InterestRateModel:  ", interestRateModelAddress);
  console.log("  CollateralVault:    ", collateralVaultAddress);
  console.log("  LiquidationEngine:  ", liquidationEngineAddress);
  console.log("  CreditScoreVerifier:", creditScoreVerifierAddress);
  console.log("  LoanManager:        ", loanManagerAddress);
  console.log("\n" + "=".repeat(70));

  // Save deployment addresses to file
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    deployer: deployer.address,
    contracts: {
      InterestRateModel: interestRateModelAddress,
      CollateralVault: collateralVaultAddress,
      LiquidationEngine: liquidationEngineAddress,
      CreditScoreVerifier: creditScoreVerifierAddress,
      LoanManager: loanManagerAddress
    },
    parameters: {
      baseRate: baseRate,
      minCollateralRatio: minCollateralRatio,
      liquidationThreshold: liquidationThreshold,
      liquidationBonus: liquidationBonus,
      minPrincipal: minPrincipal.toString()
    }
  };

  const deploymentsDir = "./deployments";
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  const deploymentFile = `${deploymentsDir}/${hre.network.name}.json`;
  fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
  console.log(`\nDeployment info saved to: ${deploymentFile}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

