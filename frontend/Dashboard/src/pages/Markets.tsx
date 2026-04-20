/**
 * Lendora AI - Markets Page
 * Shows available assets with supply/borrow rates and liquidity
 */

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { useLendoraData } from '@/hooks/useLendoraData';
import { Coins, ArrowUp, ArrowDown, TrendingUp } from 'lucide-react';
import { StablecoinLogo, Stablecoin } from '@/lib/stablecoinLogos';
import { TransactionModal, TransactionAsset } from '@/components/dashboard/TransactionModal';

// Market card interface for props
interface MarketCardProps {
    asset: TransactionAsset;
    index: number;
    onSupply: () => void;
    onBorrow: () => void;
}

// Stablecoin symbols for logo rendering
const STABLECOIN_SYMBOLS: Stablecoin[] = ['USDC', 'PYUSD', 'USDT'];

// Market Card Component with supply/borrow handlers
function MarketCard({ asset, index, onSupply, onBorrow }: MarketCardProps) {
    const availableLiquidity = asset.totalLiquidity - asset.totalBorrowed;
    const isBorrowDisabled = availableLiquidity <= 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="h-full"
        >
            <Card className="glass-card p-6 hover:border-primary/50 transition-all duration-200 h-full flex flex-col">
                {/* Asset Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                            {STABLECOIN_SYMBOLS.includes(asset.symbol as Stablecoin) ? (
                                <StablecoinLogo symbol={asset.symbol as Stablecoin} size={48} />
                            ) : (
                                <Coins className="w-6 h-6 text-primary" />
                            )}
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground text-lg">{asset.name}</h3>
                            <p className="text-sm text-muted-foreground font-mono">{asset.symbol}</p>
                        </div>
                    </div>
                </div>

                {/* Supply Rate */}
                <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <ArrowUp className="w-4 h-4 text-green-500" />
                            <span className="text-sm text-muted-foreground">Supply APY</span>
                        </div>
                        <span className="text-lg font-bold text-green-500 tabular-nums">
                            {asset.supplyRate.toFixed(2)}%
                        </span>
                    </div>
                </div>

                {/* Borrow Rate */}
                <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <ArrowDown className="w-4 h-4 text-red-500" />
                            <span className="text-sm text-muted-foreground">Borrow APY</span>
                        </div>
                        <span className="text-lg font-bold text-red-500 tabular-nums">
                            {asset.borrowRate.toFixed(2)}%
                        </span>
                    </div>
                </div>

                {/* Market Stats - Using grid for consistent alignment */}
                <div className="flex-1 pt-4 border-t border-border">
                    <div className="grid grid-cols-2 gap-y-3 gap-x-4">
                        <span className="text-sm text-muted-foreground">Total Liquidity</span>
                        <span className="text-sm font-semibold text-foreground text-right tabular-nums">
                            ${(asset.totalLiquidity / 1000000).toFixed(2)}M
                        </span>
                        <span className="text-sm text-muted-foreground">Total Borrowed</span>
                        <span className="text-sm font-semibold text-foreground text-right tabular-nums">
                            ${(asset.totalBorrowed / 1000000).toFixed(2)}M
                        </span>
                        <span className="text-sm text-muted-foreground">Available</span>
                        <span className="text-sm font-semibold text-foreground text-right tabular-nums">
                            ${(availableLiquidity / 1000000).toFixed(2)}M
                        </span>
                        <span className="text-sm text-muted-foreground">Utilization</span>
                        <span className="text-right">
                            <Badge variant="outline" className="text-xs tabular-nums">
                                {asset.utilizationRate.toFixed(1)}%
                            </Badge>
                        </span>
                    </div>
                </div>

                {/* Action Buttons - Always at bottom with margin-top auto */}
                <div className="flex gap-2 mt-4 pt-4 border-t border-border">
                    <Button 
                        variant="default" 
                        className="flex-1 bg-green-600 hover:bg-green-700 active:scale-[0.98] transition-all duration-200 ease-out"
                        onClick={onSupply}
                    >
                        <ArrowUp className="w-4 h-4 mr-1" />
                        Supply
                    </Button>
                    <Button 
                        variant="outline" 
                        className="flex-1 active:scale-[0.98] transition-all duration-200 ease-out hover:bg-primary/10 hover:border-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={onBorrow}
                        disabled={isBorrowDisabled}
                        title={isBorrowDisabled ? 'No liquidity available to borrow' : `Borrow ${asset.symbol}`}
                    >
                        <ArrowDown className="w-4 h-4 mr-1" />
                        Borrow
                    </Button>
                </div>
            </Card>
        </motion.div>
    );
}

export default function Markets() {
    const { markets, loading } = useLendoraData();
    
    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalType, setModalType] = useState<'supply' | 'borrow'>('supply');
    const [selectedAsset, setSelectedAsset] = useState<TransactionAsset | null>(null);

    // Handle Supply button click
    const handleSupply = (asset: TransactionAsset) => {
        setSelectedAsset(asset);
        setModalType('supply');
        setIsModalOpen(true);
    };

    // Handle Borrow button click
    const handleBorrow = (asset: TransactionAsset) => {
        setSelectedAsset(asset);
        setModalType('borrow');
        setIsModalOpen(true);
    };

    // Close modal
    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedAsset(null);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Card className="glass-card p-8 max-w-md text-center">
                    <p className="text-muted-foreground">Loading markets...</p>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Markets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {markets.map((asset, index) => (
                    <MarketCard
                        key={asset.symbol}
                        asset={asset}
                        index={index}
                        onSupply={() => handleSupply(asset)}
                        onBorrow={() => handleBorrow(asset)}
                    />
                ))}
            </div>

            {/* Market Summary */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
            >
                <Card className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <TrendingUp className="w-5 h-5 text-primary" />
                        <h2 className="text-xl font-semibold text-foreground">Market Overview</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 rounded-lg bg-secondary/30">
                            <p className="text-sm text-muted-foreground mb-1">Total Market Size</p>
                            <p className="text-2xl font-bold text-foreground">
                                ${(markets.reduce((sum, m) => sum + m.totalLiquidity, 0) / 1000000).toFixed(2)}M
                            </p>
                        </div>
                        <div className="p-4 rounded-lg bg-secondary/30">
                            <p className="text-sm text-muted-foreground mb-1">Total Borrowed</p>
                            <p className="text-2xl font-bold text-foreground">
                                ${(markets.reduce((sum, m) => sum + m.totalBorrowed, 0) / 1000000).toFixed(2)}M
                            </p>
                        </div>
                        <div className="p-4 rounded-lg bg-secondary/30">
                            <p className="text-sm text-muted-foreground mb-1">Avg Supply APY</p>
                            <p className="text-2xl font-bold text-foreground">
                                {(markets.reduce((sum, m) => sum + m.supplyRate, 0) / markets.length).toFixed(2)}%
                            </p>
                        </div>
                    </div>
                </Card>
            </motion.div>

            {/* Transaction Modal */}
            <TransactionModal
                isOpen={isModalOpen}
                onClose={handleCloseModal}
                type={modalType}
                asset={selectedAsset}
            />
        </div>
    );
}
