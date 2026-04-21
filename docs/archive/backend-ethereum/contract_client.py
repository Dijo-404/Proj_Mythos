"""
Lendora AI - Ethereum Contract Client
Web3.py client for interacting with deployed contracts
"""

import os
from typing import Dict, Optional, Any, List
from web3 import Web3
from web3.contract import Contract

try:
    from web3 import Web3
    from web3.contract import Contract
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class EthereumContractClient:
    """Client for interacting with Ethereum contracts."""
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        chain_id: int = 421613
    ):
        """
        Initialize contract client.
        
        Args:
            rpc_url: Ethereum RPC URL
            chain_id: Chain ID
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
        
        self.contracts: Dict[str, Contract] = {}
    
    @property
    def available(self) -> bool:
        """Check if client is available."""
        return WEB3_AVAILABLE and self._available
    
    def load_contract(
        self,
        contract_name: str,
        address: str,
        abi: List[Dict]
    ) -> Optional[Contract]:
        """
        Load a contract instance.
        
        Args:
            contract_name: Name identifier for the contract
            address: Contract address
            abi: Contract ABI
        
        Returns:
            Contract instance
        """
        if not self.available:
            return None
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=abi
            )
            self.contracts[contract_name] = contract
            return contract
        except Exception as e:
            print(f"[ContractClient] Error loading contract {contract_name}: {e}")
            return None
    
    def get_loan(self, loan_manager_address: str, loan_id: int, abi: List[Dict]) -> Optional[Dict]:
        """
        Get loan details from LoanManager contract.
        
        Args:
            loan_manager_address: LoanManager contract address
            loan_id: Loan identifier
            abi: Contract ABI
        
        Returns:
            Loan data dictionary
        """
        if not self.available:
            return None
        
        try:
            contract_name = f"LoanManager_{loan_manager_address}"
            if contract_name not in self.contracts:
                self.load_contract(contract_name, loan_manager_address, abi)
            
            contract = self.contracts[contract_name]
            loan = contract.functions.getLoan(loan_id).call()
            
            # Convert to dictionary (structure depends on Loan struct)
            return {
                "loanId": loan_id,
                "borrower": loan[0],
                "lender": loan[1],
                "principal": loan[2],
                "interestRate": loan[3],
                "termMonths": loan[4],
                "status": loan[5]
            }
            
        except Exception as e:
            print(f"[ContractClient] Error getting loan: {e}")
            return None
    
    def get_collateral_balance(
        self,
        vault_address: str,
        loan_id: int,
        abi: List[Dict]
    ) -> Optional[int]:
        """
        Get collateral balance for a loan.
        
        Args:
            vault_address: CollateralVault contract address
            loan_id: Loan identifier
            abi: Contract ABI
        
        Returns:
            Collateral balance
        """
        if not self.available:
            return None
        
        try:
            contract_name = f"CollateralVault_{vault_address}"
            if contract_name not in self.contracts:
                self.load_contract(contract_name, vault_address, abi)
            
            contract = self.contracts[contract_name]
            balance = contract.functions.getCollateralBalance(loan_id).call()
            
            return balance
            
        except Exception as e:
            print(f"[ContractClient] Error getting collateral: {e}")
            return None


# Global instance
_contract_client: Optional[EthereumContractClient] = None


def get_contract_client() -> EthereumContractClient:
    """Get or create global contract client instance."""
    global _contract_client
    if _contract_client is None:
        rpc_url = os.getenv("ETH_RPC_URL", "https://goerli-rollup.arbitrum.io/rpc")
        chain_id = int(os.getenv("ETH_CHAIN_ID", "421613"))
        _contract_client = EthereumContractClient(rpc_url=rpc_url, chain_id=chain_id)
    return _contract_client

