/**
 * Mythos — x402 Payment Flow Visualizer
 * =======================================
 * Animated visualization of micropayments flowing between AI agents.
 * Shows the x402 protocol in action: agents paying each other in USDC
 * to access AI services on Solana.
 */

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ============================================================================
// Types
// ============================================================================

export interface X402PaymentEvent {
  id: string;
  from: 'lenny' | 'luna' | 'user';
  to: 'luna' | 'lenny' | 'treasury';
  amount: number;
  resource: string;
  timestamp: string;
  status: 'pending' | 'confirmed' | 'failed';
  signature?: string;
}

interface X402PaymentVisualizerProps {
  payments: X402PaymentEvent[];
  totalPaid?: number;
  className?: string;
}

// ============================================================================
// Payment Flow Arrow
// ============================================================================

function PaymentArrow({ from, to, amount, status }: {
  from: string;
  to: string;
  amount: number;
  status: X402PaymentEvent['status'];
}) {
  const colors = {
    pending: 'text-yellow-400 border-yellow-400/40',
    confirmed: 'text-green-400 border-green-400/40',
    failed: 'text-red-400 border-red-400/40',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={`flex items-center gap-2 text-xs border rounded-lg px-3 py-2 ${colors[status]}`}
    >
      <div className="font-semibold capitalize">{from}</div>
      <motion.div
        animate={{ x: [0, 4, 0] }}
        transition={{ repeat: status === 'pending' ? Infinity : 0, duration: 0.8 }}
        className="flex-1 flex items-center gap-1"
      >
        <div className="flex-1 h-px border-t border-dashed border-current opacity-50" />
        <span className="font-mono text-amber-400 font-bold">${amount.toFixed(4)}</span>
        <div className="flex-1 h-px border-t border-dashed border-current opacity-50" />
        <span>→</span>
      </motion.div>
      <div className="font-semibold capitalize">{to}</div>
      {status === 'confirmed' && <span>✓</span>}
      {status === 'pending' && (
        <motion.span
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          ⟳
        </motion.span>
      )}
    </motion.div>
  );
}

// ============================================================================
// Payment Stats Card
// ============================================================================

function PaymentStats({ payments }: { payments: X402PaymentEvent[] }) {
  const totalUsdc = payments
    .filter(p => p.status === 'confirmed')
    .reduce((s, p) => s + p.amount, 0);

  const byResource = payments.reduce<Record<string, number>>((acc, p) => {
    acc[p.resource] = (acc[p.resource] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="grid grid-cols-3 gap-3 text-center">
      <div className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/50">
        <div className="text-2xl font-bold text-amber-400">{payments.length}</div>
        <div className="text-xs text-gray-400 mt-0.5">Total Payments</div>
      </div>
      <div className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/50">
        <div className="text-2xl font-bold text-green-400">${totalUsdc.toFixed(4)}</div>
        <div className="text-xs text-gray-400 mt-0.5">USDC Spent</div>
      </div>
      <div className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/50">
        <div className="text-2xl font-bold text-purple-400">{Object.keys(byResource).length}</div>
        <div className="text-xs text-gray-400 mt-0.5">Services Called</div>
      </div>
    </div>
  );
}

// ============================================================================
// Protocol Info
// ============================================================================

function X402ProtocolCard() {
  return (
    <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">PAY</span>
        <span className="text-sm font-bold text-yellow-300">x402 Protocol Active</span>
        <span className="ml-auto px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-300 rounded-full border border-yellow-500/30">
          HTTP 402
        </span>
      </div>
      <p className="text-xs text-gray-400 leading-relaxed">
        Every AI service call is governed by the x402 payment protocol.
        Agents pay micropayments in USDC on Solana to access gated endpoints —
        fully autonomous, machine-to-machine commerce.
      </p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <span className="text-green-400">◎</span> Network: Solana Devnet
        </div>
        <div className="flex items-center gap-1">
          <span className="text-blue-400">$</span> Asset: USDC
        </div>
        <div className="flex items-center gap-1">
          <span className="text-purple-400">FAST</span> Settlement: &lt;1 second
        </div>
        <div className="flex items-center gap-1">
          <span className="text-amber-400">AI</span> Payer: AI Agents
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function X402PaymentVisualizer({
  payments,
  className = '',
}: X402PaymentVisualizerProps) {
  const [highlightedId, setHighlightedId] = useState<string | null>(null);

  // Auto-highlight latest payment briefly
  useEffect(() => {
    if (payments.length > 0) {
      const latest = payments[payments.length - 1];
      setHighlightedId(latest.id);
      const timer = setTimeout(() => setHighlightedId(null), 2000);
      return () => clearTimeout(timer);
    }
  }, [payments.length]);

  return (
    <div className={`flex flex-col gap-4 ${className}`}>
      {/* Protocol Info */}
      <X402ProtocolCard />

      {/* Stats */}
      {payments.length > 0 && <PaymentStats payments={payments} />}

      {/* Payment Feed */}
      <div className="space-y-2">
        <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
          Payment History
        </div>
        {payments.length === 0 ? (
          <div className="text-center py-8 text-gray-600 text-sm">
            <div className="text-3xl mb-2">IDLE</div>
            <p>No payments yet</p>
            <p className="text-xs mt-1">Start a loan request to see x402 payments flow</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            <AnimatePresence>
              {[...payments].reverse().map((payment) => (
                <motion.div
                  key={payment.id}
                  className={`rounded-lg border p-3 transition-all ${
                    payment.id === highlightedId
                      ? 'border-yellow-400/60 bg-yellow-400/10'
                      : 'border-gray-700/50 bg-gray-800/40'
                  }`}
                >
                  <PaymentArrow
                    from={payment.from}
                    to={payment.to}
                    amount={payment.amount}
                    status={payment.status}
                  />
                  <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                    <span className="font-mono truncate max-w-[200px]">{payment.resource}</span>
                    <span>{new Date(payment.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {payment.signature && (
                    <div className="mt-1 text-xs font-mono text-gray-600 truncate">
                      sig: {payment.signature.slice(0, 24)}...
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Demo data generator
// ============================================================================

const DEMO_RESOURCES = [
  '/api/agent/evaluate',
  '/api/agent/negotiate',
  '/api/agent/attest',
];

const DEMO_AMOUNTS = [0.001, 0.0005, 0.002];

export function generateDemoPayment(index: number): X402PaymentEvent {
  return {
    id: `x402_${Date.now()}_${index}`,
    from: index % 2 === 0 ? 'lenny' : 'luna',
    to: index % 2 === 0 ? 'treasury' : 'treasury',
    amount: DEMO_AMOUNTS[index % DEMO_AMOUNTS.length],
    resource: DEMO_RESOURCES[index % DEMO_RESOURCES.length],
    timestamp: new Date().toISOString(),
    status: 'confirmed',
    signature: `SIM_X402_${Math.random().toString(36).slice(2, 16)}`,
  };
}
