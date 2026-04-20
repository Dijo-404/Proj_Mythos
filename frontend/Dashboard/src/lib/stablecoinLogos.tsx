/**
 * Stablecoin Logo URLs
 * Maps stablecoin symbols to their logo image URLs
 */

import React, { useState } from 'react';

export type Stablecoin = 'USDT' | 'USDC' | 'PYUSD';

// Using CoinGecko CDN for stablecoin logos
const STABLECOIN_LOGOS: Record<Stablecoin, string> = {
  USDT: 'https://assets.coingecko.com/coins/images/325/small/Tether.png',
  USDC: 'https://assets.coingecko.com/coins/images/6319/small/USD_Coin_icon.png',
  PYUSD: 'https://assets.coingecko.com/coins/images/31239/small/PYUSD_Logo.png',
};

/**
 * Get logo URL for a stablecoin
 */
export function getStablecoinLogo(symbol: Stablecoin): string {
  return STABLECOIN_LOGOS[symbol] || STABLECOIN_LOGOS.USDT;
}

/**
 * Stablecoin logo component props
 */
export interface StablecoinLogoProps {
  symbol: Stablecoin;
  size?: number;
  className?: string;
}

/**
 * Stablecoin Logo Component
 */
export function StablecoinLogo({ symbol, size = 24, className = '' }: StablecoinLogoProps) {
  const logoUrl = getStablecoinLogo(symbol);
  const [imgError, setImgError] = useState(false);
  
  if (imgError) {
    // Fallback to a simple colored circle if image fails to load
    return (
      <div
        className={`rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary ${className}`}
        style={{ width: `${size}px`, height: `${size}px`, minWidth: `${size}px`, minHeight: `${size}px` }}
      >
        {symbol[0]}
      </div>
    );
  }
  
  return (
    <img
      src={logoUrl}
      alt={symbol}
      width={size}
      height={size}
      className={`rounded-full ${className}`}
      style={{ minWidth: `${size}px`, minHeight: `${size}px` }}
      onError={() => setImgError(true)}
    />
  );
}

