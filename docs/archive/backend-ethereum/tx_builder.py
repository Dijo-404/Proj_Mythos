"""
Lendora AI - Ethereum Transaction Builder
Replaces Cardano PyCardano transaction builder
"""

import os
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from web3 import Web3
from eth_account import Account

try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("[Ethereum] Warning: web3 not installed. Run: pip install web3 eth-account")


@dataclass
class LoanSettlementParams:
    """Parameters for loan settlement transaction."""
    borrower_address: str
    lender_address: str
    principal: int  # In token units (e.g., 1e6 for USDC)
    interest_amount: int  # In token units
    loan_token: str  # Token contract address
    collateral_token: str  # Collateral token address (0x0 for ETH)
    collateral_amount: int  # Collateral amount
    interest_rate: int  # In basis points
    term_months: int
    zk_proof: List[int]  # ZK proof array [8 uint256 values]
    public_signals: List[int]  # Public signals [1 uint256 value]


class EthereumTxBuilder:
    """Builds Ethereum transactions using Web3.py."""
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        chain_id: int = 421613,  # Arbitrum Goerli testnet
        private_key: Optional[str] = None
    ):
        """
        Initialize transaction builder.
        
        Args:
            rpc_url: Ethereum RPC URL (L2 recommended)
            chain_id: Chain ID (421613 = Arbitrum Goerli, 42161 = Arbitrum Mainnet)
            private_key: Private key for signing (optional, can sign later)
        """
        self.rpc_url = rpc_url or os.getenv("ETH_RPC_URL", "https://goerli-rollup.arbitrum.io/rpc")
        self.chain_id = chain_id
        
        if WEB3_AVAILABLE:
            try:
                self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
                if not self.w3.is_connected():
                    raise ConnectionError("Failed to connect to Ethereum RPC")
                self._available = True
            except Exception as e:
                print(f"[Ethereum] Warning: Could not connect to RPC: {e}")
                self._available = False
                self.w3 = None
        else:
            self._available = False
            self.w3 = None
        
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = None
    
    @property
    def available(self) -> bool:
        """Check if Web3 is available and connected."""
        return WEB3_AVAILABLE and self._available
    
    def build_create_loan_tx(
        self,
        loan_manager_address: str,
        params: LoanSettlementParams,
        gas_price: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build a loan creation transaction.
        
        Args:
            loan_manager_address: LoanManager contract address
            params: Settlement parameters
            gas_price: Gas price in gwei (optional, uses network default)
        
        Returns:
            Dictionary with transaction data
        """
        if not self.available:
            return {
                "success": False,
                "error": "Web3 not available or not connected",
                "tx_data": None
            }
        
        try:
            # Prepare function call data
            # Function: createLoan(
            #   address lender,
            #   uint256 principal,
            #   uint256 interestRate,
            #   uint256 termMonths,
            #   address collateralToken,
            #   uint256 collateralAmount,
            #   address loanToken,
            #   uint256[8] calldata zkProof,
            #   uint256[1] calldata publicSignals
            # )
            
            function_signature = "createLoan(address,uint256,uint256,uint256,address,uint256,address,uint256[8],uint256[1])"
            function_selector = self.w3.keccak(text=function_signature)[:4].hex()
            
            # Encode parameters (simplified - in production use Contract.encodeABI)
            # For now, return the structure that frontend/backend can use
            
            # Get nonce
            if self.account:
                nonce = self.w3.eth.get_transaction_count(self.account.address)
            else:
                nonce = self.w3.eth.get_transaction_count(Web3.to_checksum_address(params.borrower_address))
            
            # Get gas price
            if gas_price is None:
                gas_price = self.w3.eth.gas_price
            else:
                gas_price = Web3.to_wei(gas_price, 'gwei')
            
            # Estimate gas (simplified)
            estimated_gas = 500000  # Conservative estimate
            
            # Build transaction
            tx_dict = {
                "to": Web3.to_checksum_address(loan_manager_address),
                "from": Web3.to_checksum_address(params.borrower_address),
                "nonce": nonce,
                "gasPrice": gas_price,
                "gas": estimated_gas,
                "value": params.collateral_amount if params.collateral_token == "0x0" else 0,
                "chainId": self.chain_id,
                "data": "0x" + function_selector  # Placeholder - actual encoding needed
            }
            
            return {
                "success": True,
                "tx_data": tx_dict,
                "tx_hash": None,  # Will be set after signing
                "chain_id": self.chain_id,
                "estimated_gas": estimated_gas,
                "gas_price_gwei": Web3.from_wei(gas_price, 'gwei')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tx_data": None
            }
    
    def build_repay_loan_tx(
        self,
        loan_manager_address: str,
        loan_id: int,
        loan_token: str,
        total_repayment: int,
        gas_price: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build a loan repayment transaction.
        
        Args:
            loan_manager_address: LoanManager contract address
            loan_id: Loan identifier
            loan_token: Loan token address (for approval)
            total_repayment: Total repayment amount
            gas_price: Gas price in gwei
        
        Returns:
            Dictionary with transaction data
        """
        if not self.available:
            return {
                "success": False,
                "error": "Web3 not available",
                "tx_data": None
            }
        
        try:
            # Function: repayLoan(uint256 loanId)
            function_signature = "repayLoan(uint256)"
            function_selector = self.w3.keccak(text=function_signature)[:4].hex()
            
            # Encode loanId (simplified)
            loan_id_encoded = self.w3.to_bytes(hexstr=hex(loan_id).replace('0x', '').zfill(64))
            
            tx_data = "0x" + function_selector + loan_id_encoded.hex()
            
            if self.account:
                nonce = self.w3.eth.get_transaction_count(self.account.address)
                from_address = self.account.address
            else:
                # Will need borrower address
                return {
                    "success": False,
                    "error": "Account or borrower address required",
                    "tx_data": None
                }
            
            if gas_price is None:
                gas_price = self.w3.eth.gas_price
            else:
                gas_price = Web3.to_wei(gas_price, 'gwei')
            
            estimated_gas = 200000
            
            tx_dict = {
                "to": Web3.to_checksum_address(loan_manager_address),
                "from": Web3.to_checksum_address(from_address),
                "nonce": nonce,
                "gasPrice": gas_price,
                "gas": estimated_gas,
                "value": 0,
                "chainId": self.chain_id,
                "data": tx_data
            }
            
            return {
                "success": True,
                "tx_data": tx_dict,
                "tx_hash": None,
                "chain_id": self.chain_id,
                "estimated_gas": estimated_gas
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tx_data": None
            }
    
    def estimate_gas(self, tx_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate gas for a transaction.
        
        Args:
            tx_dict: Transaction dictionary
        
        Returns:
            Dictionary with gas estimate
        """
        if not self.available:
            return {
                "success": False,
                "gas_estimate": 0,
                "error": "Web3 not available"
            }
        
        try:
            # Remove fields that estimation doesn't need
            estimate_tx = {k: v for k, v in tx_dict.items() if k not in ['gas', 'gasPrice']}
            gas_estimate = self.w3.eth.estimate_gas(estimate_tx)
            
            return {
                "success": True,
                "gas_estimate": gas_estimate,
                "gas_estimate_gwei": Web3.from_wei(gas_estimate * self.w3.eth.gas_price, 'gwei')
            }
            
        except Exception as e:
            return {
                "success": False,
                "gas_estimate": 0,
                "error": str(e)
            }
    
    def sign_transaction(self, tx_dict: Dict[str, Any], private_key: str) -> Dict[str, Any]:
        """
        Sign a transaction.
        
        Args:
            tx_dict: Transaction dictionary
            private_key: Private key for signing
        
        Returns:
            Dictionary with signed transaction
        """
        if not self.available:
            return {
                "success": False,
                "error": "Web3 not available",
                "signed_tx": None
            }
        
        try:
            account = Account.from_key(private_key)
            signed_tx = account.sign_transaction(tx_dict)
            
            return {
                "success": True,
                "signed_tx": signed_tx.rawTransaction.hex(),
                "tx_hash": signed_tx.hash.hex()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "signed_tx": None
            }
    
    def send_transaction(self, signed_tx_hex: str) -> Dict[str, Any]:
        """
        Send a signed transaction to the network.
        
        Args:
            signed_tx_hex: Signed transaction hex string
        
        Returns:
            Dictionary with transaction hash
        """
        if not self.available:
            return {
                "success": False,
                "error": "Web3 not available",
                "tx_hash": None
            }
        
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx_hex)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": "pending"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tx_hash": None
            }
    
    def wait_for_receipt(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Wait for transaction receipt.
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
        
        Returns:
            Transaction receipt
        """
        if not self.available:
            return {
                "success": False,
                "error": "Web3 not available"
            }
        
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            return {
                "success": True,
                "receipt": {
                    "blockNumber": receipt.blockNumber,
                    "blockHash": receipt.blockHash.hex(),
                    "transactionHash": receipt.transactionHash.hex(),
                    "status": receipt.status,
                    "gasUsed": receipt.gasUsed
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
_tx_builder: Optional[EthereumTxBuilder] = None


def get_tx_builder() -> EthereumTxBuilder:
    """Get or create global transaction builder instance."""
    global _tx_builder
    if _tx_builder is None:
        rpc_url = os.getenv("ETH_RPC_URL", "https://goerli-rollup.arbitrum.io/rpc")
        chain_id = int(os.getenv("ETH_CHAIN_ID", "421613"))  # Arbitrum Goerli
        private_key = os.getenv("ETH_PRIVATE_KEY")
        _tx_builder = EthereumTxBuilder(rpc_url=rpc_url, chain_id=chain_id, private_key=private_key)
    return _tx_builder

