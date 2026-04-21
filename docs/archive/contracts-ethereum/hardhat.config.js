require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    "arbitrum-testnet": {
      url: "https://goerli-rollup.arbitrum.io/rpc",
      chainId: 421613,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    "arbitrum-mainnet": {
      url: "https://arb1.arbitrum.io/rpc",
      chainId: 42161,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    "optimism-testnet": {
      url: "https://goerli.optimism.io",
      chainId: 420,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  },
  paths: {
    sources: "./core",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};

