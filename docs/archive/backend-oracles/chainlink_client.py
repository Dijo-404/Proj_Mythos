"""
Lendora AI - Chainlink Oracle Integration
Replaces Charli3 oracle for Ethereum stack
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("[Chainlink] Warning: web3 not installed. Run: pip install web3")


@dataclass
class PriceData:
    """Price data from Chainlink oracle."""
    price: int  # Price in USD (scaled by decimals)
    decimals: int  # Price decimals (usually 8)
    updatedAt: int  # Timestamp of last update
    roundId: int  # Round ID
    source: str = "chainlink"


class ChainlinkOracle:
    """Client for Chainlink price feed oracles."""
    
    # Chainlink price feed ABI (simplified)
    PRICE_FEED_ABI = [
        {
            "inputs": [],
            "name": "latestRoundData",
            "outputs": [
                {"name": "roundId", "type": "uint80"},
                {"name": "answer", "type": "int256"},
                {"name": "startedAt", "type": "uint256"},
                {"name": "updatedAt", "type": "uint256"},
                {"name": "answeredInRound", "type": "uint80"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Common Chainlink price feeds (Arbitrum)
    PRICE_FEEDS = {
        "ETH": "0x639Fe6ab55C92174dC7ECF4e0c8D6A3E78C5C7F7",  # ETH/USD Arbitrum Mainnet
        "USDC": None,  # USDC is a stablecoin, use 1:1 USD
        "USDT": None,  # USDT is a stablecoin, use 1:1 USD
        "DAI": None,   # DAI is a stablecoin, use 1:1 USD
        "WETH": "0x639Fe6ab55C92174dC7ECF4e0c8D6A3E78C5C7F7",  # Same as ETH
    }
    
    def __init__(self, rpc_url: Optional[str] = None, chain_id: int = 421613):
        """
        Initialize Chainlink oracle client.
        
        Args:
            rpc_url: Ethereum RPC URL
            chain_id: Chain ID (421613 = Arbitrum Goerli, 42161 = Arbitrum Mainnet)
        """
        self.rpc_url = rpc_url or os.getenv("ETH_RPC_URL", "https://goerli-rollup.arbitrum.io/rpc")
        self.chain_id = chain_id
        
        if WEB3_AVAILABLE:
            try:
                self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
                self._available = self.w3.is_connected()
            except Exception:
                self._available = False
                self.w3 = None
        else:
            self._available = False
            self.w3 = None
    
    @property
    def available(self) -> bool:
        """Check if oracle is available."""
        return WEB3_AVAILABLE and self._available
    
    def get_price(self, token_symbol: str, price_feed_address: Optional[str] = None) -> Optional[PriceData]:
        """
        Get token price from Chainlink oracle.
        
        Args:
            token_symbol: Token symbol (ETH, WETH, etc.)
            price_feed_address: Optional override for price feed address
        
        Returns:
            Price data or None if unavailable
        """
        if not self.available:
            return None
        
        # Stablecoins are 1:1 USD
        if token_symbol in ["USDC", "USDT", "DAI"]:
            return PriceData(
                price=1e8,  # 1 USD scaled by 8 decimals
                decimals=8,
                updatedAt=int(datetime.now().timestamp()),
                roundId=0,
                source="chainlink-stablecoin"
            )
        
        # Get price feed address
        feed_address = price_feed_address or self.PRICE_FEEDS.get(token_symbol)
        if not feed_address:
            print(f"[Chainlink] No price feed for {token_symbol}")
            return None
        
        try:
            from web3.contract import Contract
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(feed_address),
                abi=self.PRICE_FEED_ABI
            )
            
            # Get latest round data
            round_id, price, started_at, updated_at, answered_in_round = contract.functions.latestRoundData().call()
            decimals = contract.functions.decimals().call()
            
            # Check if price is stale (older than 1 hour)
            current_time = int(datetime.now().timestamp())
            if current_time - updated_at > 3600:
                print(f"[Chainlink] Warning: Price data stale for {token_symbol}")
            
            return PriceData(
                price=price,
                decimals=decimals,
                updatedAt=updated_at,
                roundId=round_id,
                source="chainlink"
            )
            
        except Exception as e:
            print(f"[Chainlink] Error fetching price for {token_symbol}: {e}")
            return None
    
    def get_price_usd(self, token_symbol: str, amount: int, token_decimals: int = 18) -> Optional[int]:
        """
        Get USD value of a token amount.
        
        Args:
            token_symbol: Token symbol
            amount: Token amount (in token units)
            token_decimals: Token decimals
        
        Returns:
            USD value (scaled by 1e18)
        """
        price_data = self.get_price(token_symbol)
        if not price_data:
            return None
        
        # Calculate: (amount * price) / (10^token_decimals * 10^price_decimals)
        # Return value in 1e18 scale
        usd_value = (amount * price_data.price * (10**(18 - price_data.decimals))) // (10**token_decimals)
        
        return usd_value
    
    def set_price_feed(self, token_symbol: str, price_feed_address: str):
        """
        Set custom price feed address for a token.
        
        Args:
            token_symbol: Token symbol
            price_feed_address: Chainlink price feed address
        """
        self.PRICE_FEEDS[token_symbol] = price_feed_address


# Global instance
_chainlink_oracle: Optional[ChainlinkOracle] = None


def get_chainlink_oracle() -> ChainlinkOracle:
    """Get or create global Chainlink oracle instance."""
    global _chainlink_oracle
    if _chainlink_oracle is None:
        rpc_url = os.getenv("ETH_RPC_URL", "https://goerli-rollup.arbitrum.io/rpc")
        chain_id = int(os.getenv("ETH_CHAIN_ID", "421613"))
        _chainlink_oracle = ChainlinkOracle(rpc_url=rpc_url, chain_id=chain_id)
    return _chainlink_oracle

