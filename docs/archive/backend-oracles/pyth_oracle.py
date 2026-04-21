import time
import requests
from typing import Dict, Optional, Tuple

class PythOracleClient:
    """
    Hybrid Oracle Pipeline:
    Primary: Pyth Network
    Fallback: Jupiter Price API
    """
    def __init__(self, rpc_url: str = "https://hermes.pyth.network"):
        self.rpc_url = rpc_url
        self.jupiter_url = "https://price.jup.ag/v4/price"
        
        # Mainnet Pyth Price Feed IDs for SOL, USDC, USDT, PYUSD
        self.feeds = {
            "SOL": "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
            "USDC": "0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a",
            "USDT": "0x2b89b9dc8fdf9f34709a5b106b472f0f39bb6ca9ce04b0fd7f2e971688e2e53b",
            "PYUSD": "0x40360a4f5db577f80db61ed07cc2cda44b6b158dc356064ce6c412f86aa5ca4c",
        }

    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        """
        Returns (price, source) where source is 'pyth' or 'jupiter'.
        Implements staleness, confidence, and failover policy.
        """
        feed_id = self.feeds.get(symbol.upper())
        if not feed_id:
            return self._get_jupiter_fallback(symbol)

        try:
            res = requests.get(f"{self.rpc_url}/api/latest_price_feeds?ids[]={feed_id}", timeout=2)
            res.raise_for_status()
            data = res.json()
            if not data:
                return self._get_jupiter_fallback(symbol)

            price_info = data[0]["price"]
            
            # Check staleness (if older than 60 seconds, failover)
            publish_time = int(price_info["publish_time"])
            if time.time() - publish_time > 60:
                print(f"[Oracle] Pyth {symbol} feed is stale, failing over...")
                return self._get_jupiter_fallback(symbol)
                
            # Check confidence interval (if confidence is > 5% of price, failover)
            price = float(price_info["price"]) * (10 ** int(price_info["expo"]))
            conf = float(price_info["conf"]) * (10 ** int(price_info["expo"]))
            
            if (conf / price) > 0.05:
                print(f"[Oracle] Pyth {symbol} confidence interval too wide, failing over...")
                return self._get_jupiter_fallback(symbol)

            return price, "pyth"
            
        except Exception as e:
            print(f"[Oracle] Pyth API error for {symbol}: {e}")
            return self._get_jupiter_fallback(symbol)

    def _get_jupiter_fallback(self, symbol: str) -> Tuple[Optional[float], str]:
        try:
            res = requests.get(f"{self.jupiter_url}?ids={symbol.upper()}", timeout=2)
            res.raise_for_status()
            data = res.json()
            if symbol.upper() in data.get("data", {}):
                return float(data["data"][symbol.upper()]["price"]), "jupiter"
        except Exception as e:
            print(f"[Oracle] Jupiter fallback failed for {symbol}: {e}")
        
        return None, "none"
