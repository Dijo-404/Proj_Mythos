import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { LendoraProvider } from "@/context/LendoraContext";
import { SolanaWalletProvider } from "@/components/wallet/SolanaWalletProvider";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import LoginGate from "./pages/LoginGate";
import DashboardLayout from "./pages/DashboardLayout";
import Portfolio from "./pages/Portfolio";
import Loans from "./pages/Loans";
import Transactions from "./pages/Transactions";
import Markets from "./pages/Markets";
import Settings from "./pages/Settings";
import MythosPage from "./pages/MythosPage";
import { AppLayout } from "./components/layout/AppLayout";

// Configure React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
        {/* Solana Wallet Provider wraps entire app */}
        <SolanaWalletProvider>
          <LendoraProvider>
            <TooltipProvider>
              <Toaster />
              <Sonner />
              <BrowserRouter>
                <Routes>
                  {/* Mythos Solana page — primary entry point */}
                  <Route path="/" element={<MythosPage />} />
                  <Route path="/mythos" element={<MythosPage />} />
                  {/* Legacy routes */}
                  <Route path="/login" element={<LoginGate />} />
                  <Route path="/dashboard" element={<AppLayout><DashboardLayout /></AppLayout>} />
                  <Route path="/portfolio" element={<AppLayout><Portfolio /></AppLayout>} />
                  <Route path="/loans" element={<AppLayout><Loans /></AppLayout>} />
                  <Route path="/transactions" element={<AppLayout><Transactions /></AppLayout>} />
                  <Route path="/markets" element={<AppLayout><Markets /></AppLayout>} />
                  <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
                  <Route path="/legacy" element={<Index />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </BrowserRouter>
            </TooltipProvider>
          </LendoraProvider>
        </SolanaWalletProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
