/**
 * Lendora AI - Wallet Connection Hook Proxy
 * Proxies legacy useWallet interface to the new SolanaWalletProvider
 */

import { useWallet as useSolanaWallet } from '@/components/wallet/SolanaWalletProvider';

export function useWallet() {
    const solanaWallet = useSolanaWallet();

    return {
        installedWallets: [],
        isConnecting: solanaWallet.connecting,
        isConnected: solanaWallet.connected,
        error: null,
        address: solanaWallet.publicKey || '',
        shortAddress: solanaWallet.shortAddress || '',
        balance: solanaWallet.balance.toString(),
        network: solanaWallet.network,
        chainId: null,
        connect: solanaWallet.connect,
        disconnect: solanaWallet.disconnect,
        refreshBalance: async () => {},
    };
}
